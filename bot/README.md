# LF Property Media — Discord Bot

A local Windows bot that runs LF's back-office tasks from plain-English Discord
messages. Mirrors the Southern Barn Builders bot pattern: the bot runs on the
studio PC, watches one Discord channel, parses each message with Claude, and
runs the existing Python tooling.

## What it does

Type a normal message in the bot's channel. It figures out what you want:

| You type | It does |
|---|---|
| `quote a 2,400 sqft premier shoot with twilight` | Prices it (LF package pricing) and replies with a breakdown |
| `new job, Jane Smith, 123 Bayshore Rd, shoot Friday` | Runs `new-job.py` → creates the shoot folder tree on this PC |
| `publish 2719 fort worth st` | Runs `build-property.py` → builds + pushes the listing tour |
| `mark 2719 fort worth st sold` | Flips the listing status (pending / sold / active / coming-soon) and rebuilds |
| `delivery for 2719, gallery <link>, video <link>` | Builds the branded delivery email for copy-paste into Gmail |

Status shows as emoji on your message: 👀 working · ✅ done · ❌ failed · ❓ unclear.

## One-time setup

### 1. Install Python deps

```
pip install -r bot/requirements.txt
```

(Needs Python 3.10+ on PATH. `pythonw.exe` ships with the standard Windows
installer — keep "Add to PATH" checked when installing Python.)

### 2. Create the Discord bot application (only you can do this)

1. Go to <https://discord.com/developers/applications> → **New Application** → name it "LF Property Media".
2. Left sidebar → **Bot** → **Add Bot**.
3. Under **Privileged Gateway Intents**, turn ON **MESSAGE CONTENT INTENT**. (Required — the bot reads message text.)
4. Click **Reset Token** → copy the token.
5. Left sidebar → **OAuth2 → URL Generator**: scope **bot**, permissions **View Channels, Send Messages, Read Message History, Add Reactions, Attach Files**. Open the generated URL and invite the bot to your server.
6. In Discord, enable **Developer Mode** (User Settings → Advanced), right-click the channel the bot should watch → **Copy Channel ID**.

### 3. Drop in the credentials

Both files live in the **repo root** (the `LF Gallery` folder), not in `bot/`. They're gitignored.

```
copy bot\.discord_bot.env.example .discord_bot.env
```

Then edit `.discord_bot.env`:

```
DISCORD_BOT_TOKEN=the-token-from-step-2
DISCORD_BOT_CHANNEL_ID=the-channel-id-from-step-2
DISCORD_ALLOWED_USER_IDS=your-discord-user-id
```

`DISCORD_ALLOWED_USER_IDS` controls who can run the **side-effecting** actions
(new job, publish/update tour — they write files and git-push). Quote and
delivery work for anyone in the channel. Put your own Discord user ID here
(enable Developer Mode → right-click your name → Copy User ID); separate
multiple IDs with commas. If it's left blank, the locked actions refuse to run.

And create `.anthropic_api_key` containing your Claude API key on one line
(starts with `sk-ant-`). Get one at <https://console.anthropic.com>.

### 4. Test it

```
bot\run-bot.bat
```

Leave the window open. Post `quote a 1800 sqft signature shoot` in the channel —
you should get 👀 then ✅ with a price. Ctrl+C to stop.

### 5. Make it always-on

Double-click **`bot\install-autostart.bat`**. This registers a Windows task that
launches the bot silently at every logon (auto-restarts on crash). The bot is
up whenever you're logged into this PC.

To remove it later: double-click `bot\uninstall-autostart.bat`.

## Operating notes

- **It only runs while this PC is logged in.** That's by design — `new job` and
  `publish` need local file + git access. If the PC is off, the bot is offline.
- **Check health:** `python bot/bot_status.py`
- **Watch logs:** `Get-Content bot.log -Wait -Tail 50` (PowerShell)
- **Model / cost:** defaults to `claude-haiku-4-5` (cheapest; fine for parsing).
  Override with a `LF_BOT_MODEL` env var if you ever want a bigger model.
- **Brand-new listings:** the bot publishes/updates *existing* property folders.
  For a first-time listing from an MLS link, use the `new-property` Claude skill
  to scaffold it, then the bot can publish and manage it.

## Files

| File | Purpose |
|---|---|
| `discord_bot.py` | The bot: channel routing, Claude NLU, the four handlers |
| `lf_pricing.py` | Quote pricing engine (mirror of the website calculator) |
| `bot_supervisor.py` | Keeps the bot alive (restart + heartbeat watchdog) |
| `bot_status.py` | Health check (OK / STALE / DEAD) |
| `install-autostart.{ps1,bat}` | Register the Windows logon task |
| `uninstall-autostart.{ps1,bat}` | Remove it |
| `run-bot.bat` | Manual foreground run for testing |
| `requirements.txt` | Python deps |
| `.discord_bot.env.example` | Template for the secrets file |
