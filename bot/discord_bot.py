"""
LF Property Media — Discord automation bot.

Listens to one Discord channel. For each message it:
  1. Reacts 👀 to show it's working.
  2. Sends the message to Claude (Haiku) to classify intent + extract fields
     as strict JSON (output_config.format json_schema — guaranteed parseable).
  3. Dispatches to a handler:
       quote     → price it with lf_pricing, reply with a breakdown
       new_job   → run tools/new-job.py to scaffold the shoot folders
       tour      → run tools/build-property.py to publish / rebuild / change
                   status (pending / sold / active / coming-soon) for a listing
       delivery  → assemble a branded delivery email, post it for copy-paste
  4. Reacts ✅ success / ❌ failure / ❓ unclear.

Mirrors the Southern Barn Builders bot architecture (channel routing +
Claude NLU + emoji status UI) adapted to LF's all-Python backend — no Git
Bash or headless Chrome needed, since new-job.py and build-property.py are
plain Python.

Credentials (plain files in the repo root, gitignored):
  .discord_bot.env    — DISCORD_BOT_TOKEN + DISCORD_BOT_CHANNEL_ID
  .anthropic_api_key  — Claude API key (single line, starts with sk-ant-)

Run via bot_supervisor.py (auto-restart + Windows autostart). For a manual
test run: python bot/discord_bot.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import threading
from pathlib import Path

import discord
from anthropic import Anthropic

# bot/ lives inside the repo; the repo root is one level up.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))  # for `import lf_pricing`
import lf_pricing  # noqa: E402

ENV_FILE = REPO_ROOT / ".discord_bot.env"
API_KEY_FILE = REPO_ROOT / ".anthropic_api_key"
HEARTBEAT_FILE = REPO_ROOT / ".bot.heartbeat"

MODEL = os.environ.get("LF_BOT_MODEL", "claude-haiku-4-5")

# ---------------------------------------------------------------- config load

def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        sys.exit(
            f"ERROR: {ENV_FILE} not found. Create it with:\n"
            "  DISCORD_BOT_TOKEN=...\n"
            "  DISCORD_BOT_CHANNEL_ID=...\n"
        )
    env: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    if "DISCORD_BOT_TOKEN" not in env or "DISCORD_BOT_CHANNEL_ID" not in env:
        sys.exit("ERROR: .discord_bot.env needs DISCORD_BOT_TOKEN and DISCORD_BOT_CHANNEL_ID")
    return env


def load_api_key() -> str:
    if not API_KEY_FILE.exists():
        sys.exit(f"ERROR: {API_KEY_FILE} not found. Paste your Claude API key into it (single line).")
    key = API_KEY_FILE.read_text(encoding="utf-8").strip()
    if not key.startswith("sk-ant-"):
        sys.exit("ERROR: .anthropic_api_key doesn't look like a Claude key (should start with sk-ant-).")
    return key


# ---------------------------------------------------------------- NLU (Claude)

SYSTEM_PROMPT = """You are the dispatch parser for LF Property Media, a Sarasota real estate \
photography studio. Classify each operator message into ONE intent and extract its fields. \
Reply ONLY via the structured schema.

Intents:
- "quote": operator wants a price estimate for a shoot. Extract package (signature/premier/\
platinum/alacarte), sqft (heated square footage as an integer), and add-ons: extra_photo_sets \
(sets of 10 photos), extra_drone_photos (count), creative_reel (bool), pro_video (bool), \
virtual_tour (bool). Put anything quoted separately (twilight, listing website, 3D tour, \
matterport, iphone walkthrough) into interests as short strings. Default package to "signature" \
if a price is asked but no package named.
- "new_job": operator wants to create the shoot folders for a booking. Extract realtor (the \
agent's name), address (the property street address), and date (the shoot date if given, else "").
- "tour": operator wants to publish, rebuild, or change the status of a property listing tour. \
Extract tour_target (the address or slug they name) and tour_action: "publish" or "rebuild" to \
build/republish the page, or "pending"/"sold"/"active"/"coming-soon" to change its status.
- "delivery": operator wants a gallery-delivery email. Extract delivery_first_name (the realtor's \
first name), delivery_address (the property), and any links they provide: gallery_url, video_url, \
tour_url (360/virtual tour), floorplan_url, website_url. Put any extra remark in delivery_note.
- "unknown": the message is not a clear request for any of the above.

Set confidence 0.0-1.0. Leave fields you can't extract as empty string, 0, false, or []. Never \
guess an address or name that isn't in the message."""

# Strict JSON schema — every field required so the model returns a complete object.
PARSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {"type": "string", "enum": ["quote", "new_job", "tour", "delivery", "unknown"]},
        "confidence": {"type": "number"},
        # quote
        "package": {"type": "string", "enum": ["signature", "premier", "platinum", "alacarte", ""]},
        "sqft": {"type": "integer"},
        "extra_photo_sets": {"type": "integer"},
        "extra_drone_photos": {"type": "integer"},
        "creative_reel": {"type": "boolean"},
        "pro_video": {"type": "boolean"},
        "virtual_tour": {"type": "boolean"},
        "interests": {"type": "array", "items": {"type": "string"}},
        # new_job
        "realtor": {"type": "string"},
        "address": {"type": "string"},
        "date": {"type": "string"},
        # tour
        "tour_target": {"type": "string"},
        "tour_action": {"type": "string", "enum": ["publish", "rebuild", "pending", "sold", "active", "coming-soon", ""]},
        # delivery
        "delivery_first_name": {"type": "string"},
        "delivery_address": {"type": "string"},
        "gallery_url": {"type": "string"},
        "video_url": {"type": "string"},
        "tour_url": {"type": "string"},
        "floorplan_url": {"type": "string"},
        "website_url": {"type": "string"},
        "delivery_note": {"type": "string"},
    },
    "required": [
        "intent", "confidence", "package", "sqft", "extra_photo_sets", "extra_drone_photos",
        "creative_reel", "pro_video", "virtual_tour", "interests", "realtor", "address", "date",
        "tour_target", "tour_action", "delivery_first_name", "delivery_address", "gallery_url",
        "video_url", "tour_url", "floorplan_url", "website_url", "delivery_note",
    ],
}


def parse_message(claude: Anthropic, content: str) -> dict:
    resp = claude.messages.create(
        model=MODEL,
        max_tokens=600,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        output_config={"format": {"type": "json_schema", "schema": PARSE_SCHEMA}},
        messages=[{"role": "user", "content": content}],
    )
    text = next((b.text for b in resp.content if b.type == "text"), "{}")
    return json.loads(text)


# ---------------------------------------------------------------- backends

def _run(args: list[str], timeout: int = 300) -> tuple[bool, str]:
    """Run a Python tool in the repo, return (ok, combined_output)."""
    try:
        r = subprocess.run(
            [sys.executable, *args],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=timeout,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, out.strip()
    except subprocess.TimeoutExpired:
        return False, f"Timed out after {timeout}s."
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def handle_quote(p: dict) -> str:
    q = lf_pricing.QuoteInput(
        package=p.get("package") or "signature",
        sqft=int(p.get("sqft") or 0),
        extra_photo_sets=int(p.get("extra_photo_sets") or 0),
        extra_drone_photos=int(p.get("extra_drone_photos") or 0),
        creative_reel=bool(p.get("creative_reel")),
        pro_video=bool(p.get("pro_video")),
        virtual_tour=bool(p.get("virtual_tour")),
        interests=list(p.get("interests") or []),
    )
    return lf_pricing.format_discord_reply(lf_pricing.compute_price(q))


def handle_new_job(p: dict) -> tuple[bool, str]:
    realtor = (p.get("realtor") or "").strip()
    address = (p.get("address") or "").strip()
    if not realtor or not address:
        return False, "I need both a **realtor name** and a **property address** to create the job folders."
    args = ["tools/new-job.py", "--realtor", realtor, "--address", address]
    date = (p.get("date") or "").strip()
    if date:
        args += ["--date", date]
    ok, out = _run(args, timeout=60)
    if ok:
        return True, f"Created shoot folders for **{realtor} — {address}**.\n```\n{out[:1500]}\n```"
    return False, f"Folder creation failed:\n```\n{out[:1500]}\n```"


def _resolve_slug(target: str) -> str | None:
    """Match an address-or-slug against existing properties/<slug>/ folders."""
    target = (target or "").strip().lower()
    if not target:
        return None
    props = REPO_ROOT / "properties"
    if not props.exists():
        return None
    candidates = [d.name for d in props.iterdir()
                  if d.is_dir() and (d / "listing.json").exists()]
    # Exact slug
    if target in candidates:
        return target
    # Slugified address match (drop punctuation, spaces -> hyphens)
    slugged = "".join(c if c.isalnum() else "-" for c in target)
    while "--" in slugged:
        slugged = slugged.replace("--", "-")
    slugged = slugged.strip("-")
    for c in candidates:
        if c == slugged or slugged in c or c in slugged:
            return c
    # Address field match inside listing.json
    for c in candidates:
        try:
            data = json.loads((props / c / "listing.json").read_text(encoding="utf-8"))
            if target in (data.get("address", "").lower()):
                return c
        except Exception:  # noqa: BLE001
            continue
    return None


_STATUS_DISPLAY = {
    "pending": "Pending", "sold": "Sold", "active": "Active", "coming-soon": "Coming Soon",
}


def handle_tour(p: dict) -> tuple[bool, str]:
    target = p.get("tour_target") or ""
    action = (p.get("tour_action") or "rebuild").strip().lower()
    slug = _resolve_slug(target)
    if not slug:
        return False, (f"I couldn't find a property matching **{target}**. "
                       "For a brand-new listing, set it up with the `new-property` skill first, "
                       "then I can publish or update it.")

    # Status change → edit listing.json before rebuilding.
    if action in _STATUS_DISPLAY:
        listing_path = REPO_ROOT / "properties" / slug / "listing.json"
        try:
            data = json.loads(listing_path.read_text(encoding="utf-8"))
            data["status"] = action
            if isinstance(data.get("facts"), dict):
                data["facts"]["status"] = _STATUS_DISPLAY[action]
            listing_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            return False, f"Couldn't update status on {slug}: {e}"

    ok, out = _run(["tools/build-property.py", slug, "--commit"], timeout=300)
    verb = f"marked **{_STATUS_DISPLAY[action]}**" if action in _STATUS_DISPLAY else f"**{action}ed**"
    if ok:
        return True, f"{slug} {verb} and pushed live.\n```\n{out[-1200:]}\n```"
    return False, f"Build failed for {slug}:\n```\n{out[-1200:]}\n```"


def handle_delivery(p: dict) -> str:
    first = (p.get("delivery_first_name") or "there").strip()
    address = (p.get("delivery_address") or "your listing").strip()
    links = [
        ("Photo gallery", p.get("gallery_url")),
        ("Video", p.get("video_url")),
        ("360 / virtual tour", p.get("tour_url")),
        ("Floor plan", p.get("floorplan_url")),
        ("Listing website", p.get("website_url")),
    ]
    links = [(label, url.strip()) for label, url in links if (url or "").strip()]
    subject = f"Your listing media is ready — {address}"
    lines = [
        f"Hi {first},",
        "",
        f"The media for {address} is ready. Everything's below:",
        "",
    ]
    if links:
        for label, url in links:
            lines.append(f"  {label}: {url}")
    else:
        lines.append("  (no links provided yet — add them and resend)")
    note = (p.get("delivery_note") or "").strip()
    if note:
        lines += ["", note]
    lines += [
        "",
        "Photos are MLS-ready — sized, color-balanced, and named for upload. "
        "Let me know if you need anything adjusted.",
        "",
        "Thank you,",
        "Locke",
        "LF Property Media",
        "(941) 387-5399 · lfpropertymedia.org",
    ]
    body = "\n".join(lines)
    return (f"**Delivery email — copy/paste into Gmail:**\n"
            f"**Subject:** {subject}\n```\n{body}\n```")


# ---------------------------------------------------------------- discord glue

def build_bot(env: dict[str, str], claude: Anthropic) -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True  # PRIVILEGED — enable in the Developer Portal
    client = discord.Client(intents=intents)
    channel_id = int(env["DISCORD_BOT_CHANNEL_ID"])

    async def react(msg, emoji):
        try:
            await msg.add_reaction(emoji)
        except Exception:  # noqa: BLE001
            pass

    async def unreact(msg, emoji):
        try:
            await msg.remove_reaction(emoji, client.user)
        except Exception:  # noqa: BLE001
            pass

    @client.event
    async def on_ready():
        print(f"LF bot online as {client.user} — watching channel {channel_id}")

    @client.event
    async def on_message(message: discord.Message):
        if message.author == client.user or not message.content.strip():
            return
        if message.channel.id != channel_id:
            return

        import asyncio
        await react(message, "👀")
        try:
            parsed = await asyncio.to_thread(parse_message, claude, message.content)
        except Exception as e:  # noqa: BLE001
            await unreact(message, "👀")
            await react(message, "❌")
            await message.reply(f"Parser error:\n```\n{type(e).__name__}: {e}\n```"[:1900])
            return

        intent = parsed.get("intent", "unknown")
        confidence = float(parsed.get("confidence") or 0)

        if intent == "unknown" or confidence < 0.45:
            await unreact(message, "👀")
            await react(message, "❓")
            await message.reply(
                "Not sure what you need. Try:\n"
                "• `quote a 2,400 sqft premier shoot with twilight`\n"
                "• `new job, Jane Smith, 123 Bayshore Rd, shoot Friday`\n"
                "• `publish 2719 fort worth st` / `mark 2719 fort worth st sold`\n"
                "• `delivery for 2719, gallery <link>, video <link>`"
            )
            return

        try:
            if intent == "quote":
                ok, reply = True, handle_quote(parsed)
            elif intent == "new_job":
                ok, reply = handle_new_job(parsed)
            elif intent == "tour":
                ok, reply = handle_tour(parsed)
            elif intent == "delivery":
                ok, reply = True, handle_delivery(parsed)
            else:
                ok, reply = False, "Unhandled intent."
        except Exception as e:  # noqa: BLE001
            ok, reply = False, f"Handler error:\n```\n{type(e).__name__}: {e}\n```"

        await unreact(message, "👀")
        await react(message, "✅" if ok else "❌")
        # Discord hard-limits messages to 2000 chars.
        await message.reply(reply[:1990])

    return client


# ---------------------------------------------------------------- heartbeat

def _heartbeat_loop():
    while True:
        try:
            HEARTBEAT_FILE.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        time.sleep(30)


def main() -> None:
    env = load_env()
    claude = Anthropic(api_key=load_api_key())
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
    bot = build_bot(env, claude)
    bot.run(env["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
