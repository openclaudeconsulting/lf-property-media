#!/usr/bin/env python3
"""
Generate a property listing tour page from listing.json + a shared HTML template.

Usage
-----
  python tools/build-property.py --new <slug>      # scaffold a new property (draft)
  python tools/build-property.py <slug>            # build one property
  python tools/build-property.py <slug> <slug>     # build many
  python tools/build-property.py --hub             # rebuild hub only
  python tools/build-property.py --all             # rebuild every property + hub

  Append --commit to any of the above to git add + commit + push the
  generated changes. Only properties/, properties/index.html, and sitemap.xml
  get staged — other working-tree changes are left alone.
      python tools/build-property.py <slug> --commit
      python tools/build-property.py --all --commit

Side effects of every build
---------------------------
  - properties/<slug>/index.html regenerated
  - properties/index.html (hub) regenerated
  - sitemap.xml gets a <url> entry for the property if not already there
    (skipped for unlisted properties)

Each property lives at:
  properties/<slug>/
    listing.json     ← source of truth (address, sections, photos)
    media/           ← photos, organized into subfolders per section
      hero.jpg
      Aerial_Photos/
      Home_Photos/
    index.html       ← GENERATED — do not hand-edit, edits will be overwritten

The shared HTML template lives at tools/templates/property-page.html and uses
{{double-brace}} placeholders. Edit the template once, regenerate all properties.
"""
from __future__ import annotations

import json
import sys
import html as html_lib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
PROPERTIES_DIR = ROOT / "properties"
TEMPLATE_PATH = ROOT / "tools" / "templates" / "property-page.html"
HUB_TEMPLATE_PATH = ROOT / "tools" / "templates" / "properties-hub.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
SITE_URL = "https://lfpropertymedia.org"

# Identity used for the auto-commit so contributions stay attributed to the
# studio account. Override by exporting GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL.
GIT_AUTHOR_NAME = "LF Property Media"
GIT_AUTHOR_EMAIL = "openclaudeconsulting@gmail.com"


def render_tour_js(sections: list[dict[str, Any]]) -> str:
    """Convert sections list to a pretty-printed JS array literal for the TOUR const.

    Auto-numbers each section as n:'01', n:'02', etc. in display order.
    """
    items = []
    for i, s in enumerate(sections, 1):
        items.append(
            "      { "
            f"id:{json.dumps(s['id'])}, "
            f"n:{json.dumps(f'{i:02d}')}, "
            f"title:{json.dumps(s['title'])}, "
            f"sub:{json.dumps(s['sub'])}, "
            f"dir:{json.dumps(s['dir'])}, "
            f"photos:{json.dumps(s['photos'])}"
            " }"
        )
    return ",\n".join(items)


def address_with_em(address: str, emphasis: str | None) -> str:
    """Wrap the emphasis word in <em>. Falls back to wrapping the last word."""
    target = emphasis or address.split()[-1]
    # Replace LAST occurrence only, in case the word appears earlier.
    idx = address.rfind(target)
    if idx == -1:
        return html_lib.escape(address)
    before = html_lib.escape(address[:idx])
    em_part = html_lib.escape(target)
    after = html_lib.escape(address[idx + len(target):])
    return f"{before}<em>{em_part}</em>{after}"


def _fmt_int(n: Any) -> str:
    """Thousands-separated int, tolerant of strings/floats."""
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def _join(v: Any) -> str:
    """Render a value: lists become ' · '-joined, scalars stringified."""
    if isinstance(v, list):
        return " · ".join(str(x) for x in v)
    return str(v)


def _copy_text(facts: dict[str, Any], address: str, city: str, state: str, zip_code: str) -> str:
    """A compact, paste-ready MLS summary an agent can drop into a text/email."""
    f = facts
    lines = [f"{address}, {city}, {state} {zip_code}".strip()]
    head = []
    if f.get("list_price_display"): head.append(f["list_price_display"])
    if f.get("mls_number"): head.append(f"MLS {f['mls_number']}")
    if f.get("data_source"): head[-1] = head[-1] + f" ({f['data_source']})"
    if f.get("status"): head.append(f["status"])
    if head: lines.append(" · ".join(head))
    specs = []
    if f.get("beds") is not None: specs.append(f"{f['beds']} bd")
    if f.get("baths_display"): specs.append(f"{f['baths_display']} ba")
    if f.get("sqft_heated"):
        s = f"{_fmt_int(f['sqft_heated'])} sqft heated"
        if f.get("sqft_total_under_roof"):
            s += f" ({_fmt_int(f['sqft_total_under_roof'])} under roof)"
        specs.append(s)
    if f.get("price_per_sqft_heated"): specs.append(f"~${f['price_per_sqft_heated']}/sqft")
    if specs: lines.append(" · ".join(specs))
    lot = []
    if f.get("lot_sqft"):
        l = f"Lot {_fmt_int(f['lot_sqft'])} sqft"
        if f.get("lot_acres"): l += f" ({f['lot_acres']} ac)"
        lot.append(l)
    if f.get("year_built"): lot.append(f"Built {f['year_built']}")
    if f.get("architectural_style"): lot.append(f["architectural_style"])
    if lot: lines.append(" · ".join(lot))
    fin = []
    if f.get("annual_taxes_display"):
        t = f"Taxes {f['annual_taxes_display']}"
        if f.get("tax_year"): t += f" ({f['tax_year']})"
        fin.append(t)
    if f.get("hoa") is False: fin.append("No HOA")
    if f.get("cdd") is False: fin.append("No CDD")
    if f.get("ownership"): fin.append(f["ownership"])
    if fin: lines.append(" · ".join(fin))
    if f.get("pool"): lines.append(f"Pool: {f['pool']}")
    if f.get("virtual_tour_url"): lines.append(f"Virtual tour: {f['virtual_tour_url']}")
    return "\n".join(lines)


def render_facts_panel(
    facts: dict[str, Any] | None,
    address: str,
    city: str,
    state: str,
    zip_code: str,
) -> str:
    """Build the agent-facing 'Property Facts' data-sheet section from facts.

    Returns '' when a listing has no facts block, so the template stays
    backward-compatible with photo-only tours.
    """
    if not facts:
        return ""
    f = facts
    esc = html_lib.escape

    def yn(key: str) -> str | None:
        return ("Yes" if f[key] else "No") if key in f else None

    # ---- headline stat row (the six numbers agents quote on the phone) ----
    stats: list[tuple[str, str, str]] = []
    if f.get("list_price_display"):
        sub = f"${f['price_per_sqft_heated']} / sq ft" if f.get("price_per_sqft_heated") else ""
        stats.append((f["list_price_display"], "List Price", sub))
    if f.get("beds") is not None:
        stats.append((str(f["beds"]), "Bedrooms", f.get("beds_note", "")))
    if f.get("baths_display"):
        sub = ""
        if f.get("baths_full") is not None and f.get("baths_half") is not None:
            sub = f"{f['baths_full']} full · {f['baths_half']} half"
        stats.append((f["baths_display"], "Bathrooms", sub))
    if f.get("sqft_heated"):
        sub = f"{_fmt_int(f['sqft_total_under_roof'])} under roof" if f.get("sqft_total_under_roof") else ""
        stats.append((_fmt_int(f["sqft_heated"]), "Heated Sq Ft", sub))
    if f.get("lot_acres") or f.get("lot_sqft"):
        val = f"{f['lot_acres']} ac" if f.get("lot_acres") else f"{_fmt_int(f['lot_sqft'])} sf"
        sub = f"{_fmt_int(f['lot_sqft'])} sq ft" if f.get("lot_sqft") else ""
        stats.append((val, "Lot Size", sub))
    if f.get("year_built"):
        stats.append((str(f["year_built"]), "Year Built", f.get("architectural_style", "")))

    stat_html = "\n".join(
        f'        <div class="fstat"><span class="v">{esc(str(v))}</span>'
        f'<span class="l">{esc(lbl)}</span>'
        + (f'<span class="sub">{esc(str(s))}</span>' if s else "")
        + "</div>"
        for v, lbl, s in stats
    )

    # ---- grouped spec tables ----
    def row(k: str, v: Any) -> tuple[str, str] | None:
        if v is None or v == "" or v == []:
            return None
        return (k, _join(v))

    garage = None
    if f.get("garage_spaces"):
        garage = f"{f['garage_spaces']}-car" + (" attached" if f.get("garage_attached") else "")
    ppsf = None
    if f.get("price_per_sqft_heated"):
        ppsf = f"${f['price_per_sqft_heated']}/sf heated"
        if f.get("price_per_sqft_total"):
            ppsf += f" · ${f['price_per_sqft_total']}/sf total"
    taxes = f.get("annual_taxes_display")
    if taxes and f.get("tax_year"):
        taxes = f"{taxes} ({f['tax_year']})"
    lot = None
    if f.get("lot_sqft"):
        lot = f"{_fmt_int(f['lot_sqft'])} sq ft"
        if f.get("lot_acres"):
            lot += f" · {f['lot_acres']} ac"

    groups: list[tuple[str, list[tuple[str, str] | None]]] = [
        ("Overview", [
            row("Status", f.get("status")),
            row("Property type", f.get("property_type")),
            row("Style", f.get("architectural_style")),
            row("Levels", f.get("levels")),
            row("Stories", f.get("stories")),
            row("Total rooms", f.get("total_rooms")),
            row("Days on market", f.get("days_on_market")),
            row("Listed", f.get("list_date_display")),
            row("MLS #", f.get("mls_number")),
        ]),
        ("Interior", [
            row("Bedrooms", f.get("beds")),
            row("Bathrooms", f.get("baths_display")),
            row("Flooring", f.get("flooring")),
            row("Fireplace", f.get("fireplace")),
            row("Appliances", f.get("appliances")),
            row("Laundry", f.get("laundry")),
            row("Furnished", f.get("furnished")),
            row("Features", f.get("interior_features")),
        ]),
        ("Systems & Construction", [
            row("Heating", f.get("heating")),
            row("Cooling", f.get("cooling")),
            row("Roof", f.get("roof")),
            row("Construction", f.get("construction")),
            row("Foundation", f.get("foundation")),
            row("Sewer", f.get("sewer")),
            row("Water", f.get("water_source")),
            row("Utilities", f.get("utilities")),
        ]),
        ("Exterior & Outdoor", [
            row("Pool", f.get("pool")),
            row("Spa", f.get("spa")),
            row("Garage", garage),
            row("Carport", yn("carport")),
            row("Patio / porch", f.get("patio_porch")),
            row("Exterior", f.get("exterior_features")),
            row("Waterfront", yn("waterfront")),
            row("Water view", yn("water_view")),
        ]),
        ("Financial", [
            row("List price", f.get("list_price_display")),
            row("Price / sq ft", ppsf),
            row("Annual taxes", taxes),
            row("HOA", "None" if f.get("hoa") is False else f.get("hoa")),
            row("CDD", "None" if f.get("cdd") is False else f.get("cdd")),
            row("Ownership", f.get("ownership")),
            row("Terms", f.get("listing_terms")),
        ]),
        ("Location & Legal", [
            row("County", f.get("county")),
            row("Subdivision", f.get("subdivision")),
            row("MLS area", f.get("mls_area")),
            row("Zoning", f.get("zoning")),
            row("Flood zone", f.get("flood_zone")),
            row("Facing", f.get("facing_direction")),
            row("Lot size", lot),
            row("Lot dimensions", f.get("lot_dimensions")),
            row("Parcel / legal", f.get("parcel_legal")),
        ]),
    ]

    groups_html = ""
    for title, rows in groups:
        clean = [r for r in rows if r]
        if not clean:
            continue
        inner = "\n".join(
            f'          <div class="frow"><span class="k">{esc(k)}</span>'
            f'<span class="v">{esc(str(v))}</span></div>'
            for k, v in clean
        )
        groups_html += (
            f'        <div class="fgroup">\n'
            f'          <h3>{esc(title)}</h3>\n{inner}\n'
            f'        </div>\n'
        )

    # ---- recent-updates timeline ----
    updates_html = ""
    updates = f.get("updates") or []
    if updates:
        items = "\n".join(
            f'          <div class="fupd"><span class="yr">{esc(str(u.get("year", "")))}</span>'
            f'<span class="it">{esc(str(u.get("item", "")))}</span></div>'
            for u in updates
        )
        updates_html = (
            '      <div class="fupdates">\n'
            '        <h3 class="fgroup-h">Recent Updates</h3>\n'
            f'        <div class="fupdates-list">\n{items}\n        </div>\n'
            '      </div>\n'
        )

    # ---- actions: virtual tour, copy, print + source line ----
    actions = []
    if f.get("virtual_tour_url"):
        actions.append(
            f'        <a class="fbtn sand" href="{esc(f["virtual_tour_url"])}" target="_blank" rel="noopener">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">'
            '<path d="M23 7l-7 5 7 5V7zM1 5h15v14H1z"/></svg>'
            '<span class="lbl">3D Virtual Tour</span></a>'
        )
    copy_data = esc(_copy_text(f, address, city, state, zip_code), quote=True).replace("\n", "&#10;")
    actions.append(
        f'        <button class="fbtn" id="copyFacts" type="button" data-copy="{copy_data}">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">'
        '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
        '<span class="lbl">Copy MLS Facts</span></button>'
    )
    actions.append(
        '        <button class="fbtn" id="printFacts" type="button">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">'
        '<path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z"/></svg>'
        '<span class="lbl">Print Sheet</span></button>'
    )
    source_bits = []
    if f.get("mls_number"):
        source_bits.append(f"MLS {esc(f['mls_number'])}")
    if f.get("data_source"):
        source_bits.append(esc(f["data_source"]))
    if f.get("listing_office"):
        source_bits.append("Listed by " + esc(f["listing_office"]))
    source_line = ""
    if source_bits:
        source_line = f'        <span class="fsource">{" · ".join(source_bits)}</span>'

    disclaimer = ""
    if f.get("disclaimer"):
        disclaimer = f'      <p class="fdisc">{esc(f["disclaimer"])}</p>\n'

    return (
        '      <section class="section facts" id="facts">\n'
        '        <div class="sec-head">\n'
        '          <div class="l"><span class="sec-num">00</span>'
        '<h2 class="sec-title">Property Info</h2>'
        '<span class="sec-sub">The full listing data sheet</span></div>\n'
        f'          <span class="sec-count">{esc(f.get("mls_number", "Listing Data"))}</span>\n'
        '        </div>\n'
        f'        <div class="facts-stats">\n{stat_html}\n        </div>\n'
        f'        <div class="facts-grid">\n{groups_html}        </div>\n'
        f'{updates_html}'
        '        <div class="facts-actions">\n'
        + "\n".join(actions) + "\n"
        + (source_line + "\n" if source_line else "")
        + '        </div>\n'
        f'{disclaimer}'
        '      </section>'
    )


def build(slug: str) -> None:
    prop_dir = PROPERTIES_DIR / slug
    listing_path = prop_dir / "listing.json"
    if not listing_path.exists():
        raise FileNotFoundError(f"No listing.json at {listing_path}")

    listing = json.loads(listing_path.read_text(encoding="utf-8"))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    sections = listing["sections"]
    photo_count = sum(len(s["photos"]) for s in sections)

    address = listing["address"]
    city = listing["city"]
    state = listing["state"]
    zip_code = listing.get("zip", "")
    hero_describe = listing.get("hero_describe", "A real estate listing")
    hero_categories = listing.get("hero_categories", "")
    hero_kicker = listing.get("hero_kicker", f"{city}, {state} · Full Visual Tour")
    hero_photo = listing.get("hero_photo", "hero.jpg")
    footer_note = listing.get("footer_note", "Photographed for listing")
    address_short = listing.get("address_short", address)
    emphasis = listing.get("address_emphasis")

    canonical = f"{SITE_URL}/properties/{slug}/"
    hero_image_url = f"{canonical}media/{hero_photo}"

    # Derive user-facing text from facts so listing.json stays terse.
    title = f"{address} · {city} — Listing Tour by LF Property Media"
    description = (
        f"Full visual tour of {address}, {city}, {state}. "
        f"{photo_count} photographs by LF Property Media — {hero_categories.lower()}. "
        f"{hero_describe}."
    )
    og_title = f"{address}, {city} — Listing Tour"
    og_description = (
        f"{hero_describe}. {photo_count} photographs by LF Property Media — "
        f"{hero_categories}."
    )
    hero_alt = f"{address}, {city} — front elevation"
    footer_address_line = f"{address} · {footer_note}"

    replacements = {
        "{{title}}": html_lib.escape(title),
        "{{description}}": html_lib.escape(description),
        "{{canonical}}": canonical,
        "{{og_title}}": html_lib.escape(og_title),
        "{{og_description}}": html_lib.escape(og_description),
        "{{hero_image_url}}": hero_image_url,
        "{{address}}": html_lib.escape(address),
        "{{address_short}}": html_lib.escape(address_short),
        "{{address_with_em}}": address_with_em(address, emphasis),
        "{{city}}": html_lib.escape(city),
        "{{state}}": html_lib.escape(state),
        "{{zip}}": html_lib.escape(zip_code),
        "{{country}}": html_lib.escape(listing.get("country", "US")),
        "{{hero_kicker}}": html_lib.escape(hero_kicker),
        "{{hero_describe}}": html_lib.escape(hero_describe),
        "{{photo_count}}": str(photo_count),
        "{{hero_categories}}": html_lib.escape(hero_categories),
        "{{hero_photo}}": hero_photo,
        "{{hero_alt}}": html_lib.escape(hero_alt),
        "{{footer_address_line}}": html_lib.escape(footer_address_line),
        "{{tour_data}}": render_tour_js(sections),
        "{{facts_panel}}": render_facts_panel(
            listing.get("facts"), address, city, state, zip_code
        ),
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # Check for unfilled placeholders to catch template/data drift.
    # Pattern matches {{word}} with only lowercase + underscore; avoids
    # false positives on header-comment meta-references to "{{double-brace}}".
    import re
    leftover_pattern = re.compile(r"\{\{[a-z_]+\}\}")
    leftover_lines = [
        line for line in html.splitlines() if leftover_pattern.search(line)
    ]
    if leftover_lines:
        print(f"WARNING: unfilled placeholders in {slug}:", file=sys.stderr)
        for ln in leftover_lines[:5]:
            print(f"  {ln.strip()}", file=sys.stderr)

    out = prop_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"Built {slug}: {photo_count} photos in {len(sections)} sections -> {out}")

    # Side effect: keep sitemap.xml in sync. Idempotent (skips if URL already
    # present). Skipped for unlisted properties — those are private links.
    if not listing.get("unlisted"):
        if _update_sitemap(slug, listing, address, city, hero_photo):
            print(f"  -> sitemap.xml: added /properties/{slug}/")


def _update_sitemap(slug: str, listing: dict[str, Any], address: str, city: str, hero_photo: str) -> bool:
    """Append a <url> entry for this property to sitemap.xml if not already there.

    Returns True if the sitemap was modified, False if the entry already existed
    or the sitemap couldn't be found.
    """
    if not SITEMAP_PATH.exists():
        print(f"  WARNING: sitemap.xml not found at {SITEMAP_PATH}", file=sys.stderr)
        return False

    text = SITEMAP_PATH.read_text(encoding="utf-8")
    canonical = f"{SITE_URL}/properties/{slug}/"
    if canonical in text:
        return False  # already listed

    hero_url = f"{canonical}media/{hero_photo}"
    entry = (
        f"  <url>\n"
        f"    <loc>{canonical}</loc>\n"
        f"    <changefreq>monthly</changefreq>\n"
        f"    <priority>0.8</priority>\n"
        f"    <image:image>\n"
        f"      <image:loc>{hero_url}</image:loc>\n"
        f"      <image:title>{html_lib.escape(address)}, {html_lib.escape(city)} — Listing Tour</image:title>\n"
        f"    </image:image>\n"
        f"  </url>\n\n"
    )
    if "</urlset>" not in text:
        print(f"  WARNING: sitemap.xml has no </urlset> close tag", file=sys.stderr)
        return False

    # Insert immediately before the closing </urlset>.
    text = text.replace("</urlset>", entry + "</urlset>")
    SITEMAP_PATH.write_text(text, encoding="utf-8")
    return True


def _commit_and_push(slugs: list[str]) -> None:
    """Stage the listing folders, the hub, and sitemap; commit and push.

    Only stages paths we control. Other working-tree changes are left alone.
    Author identity is set inline so we don't depend on git config.
    """
    import subprocess

    paths_to_stage = [
        "properties/index.html",
        "sitemap.xml",
    ]
    for slug in slugs:
        paths_to_stage.append(f"properties/{slug}/")

    # git add
    result = subprocess.run(
        ["git", "add"] + paths_to_stage,
        cwd=ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"git add failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Check if there's anything staged from our paths
    diff_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=ROOT
    )
    if diff_check.returncode == 0:
        print("Nothing to commit - sitemap + pages already match origin.")
        return

    # Commit
    if len(slugs) == 1:
        msg = f"Property tour build: {slugs[0]}"
    else:
        msg = f"Property tour build: {len(slugs)} listing(s)"

    commit = subprocess.run(
        [
            "git",
            "-c", f"user.name={GIT_AUTHOR_NAME}",
            "-c", f"user.email={GIT_AUTHOR_EMAIL}",
            "commit", "-m", msg,
        ],
        cwd=ROOT, capture_output=True, text=True
    )
    if commit.returncode != 0:
        print(f"git commit failed:\n{commit.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Committed: {msg}")

    # Push
    push = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=ROOT, capture_output=True, text=True
    )
    if push.returncode != 0:
        print(f"git push failed:\n{push.stderr}", file=sys.stderr)
        sys.exit(1)
    # The push output usually lands on stderr in git; surface its last lines
    out = (push.stderr or push.stdout).strip().splitlines()
    if out:
        print("Pushed:", out[-1])


def build_all() -> None:
    found = 0
    for prop_dir in sorted(PROPERTIES_DIR.iterdir()):
        if prop_dir.is_dir() and (prop_dir / "listing.json").exists():
            build(prop_dir.name)
            found += 1
    if found == 0:
        print("No properties with listing.json found in properties/")


# ============================================================
#  HUB PAGE — /properties/index.html
# ============================================================

def _load_published_listings() -> list[dict[str, Any]]:
    """Return all listing.json contents that should appear on the hub.

    Skipped:
      - unlisted: true   (private share link only)
      - status: "draft"  (not ready for public)
    Sort: by date_published descending if present, else slug ascending.
    """
    out = []
    for prop_dir in PROPERTIES_DIR.iterdir():
        if not prop_dir.is_dir():
            continue
        listing_path = prop_dir / "listing.json"
        if not listing_path.exists():
            continue
        data = json.loads(listing_path.read_text(encoding="utf-8"))
        if data.get("unlisted"):
            continue
        if data.get("status") == "draft":
            continue
        data["_slug"] = data.get("slug", prop_dir.name)
        out.append(data)
    out.sort(
        key=lambda d: (
            -1 if d.get("date_published") else 0,
            d.get("date_published", "") or "",
            d["_slug"],
        ),
        reverse=True,
    )
    return out


def _render_card(listing: dict[str, Any]) -> str:
    slug = listing["_slug"]
    address = listing["address"]
    city = listing["city"]
    state = listing["state"]
    hero_photo = listing.get("hero_photo", "hero.jpg")
    photo_count = sum(len(s["photos"]) for s in listing["sections"])
    status = (listing.get("status") or "active").strip().lower()
    is_sold = status == "sold"
    # Status badge map. "sold" also hides the price chip (handled below).
    # "pending" / "coming-soon" keep the price visible — the property is still
    # being marketed — but get a distinct badge so the hub reads at a glance.
    _BADGES = {
        "sold": ("sold", "Sold"),
        "pending": ("pending", "Pending"),
        "coming-soon": ("coming", "Coming Soon"),
        "coming_soon": ("coming", "Coming Soon"),
    }
    badge = ""
    if status in _BADGES:
        _cls, _label = _BADGES[status]
        badge = f'<span class="badge {_cls}">{_label}</span>'
    addr_em = address_with_em(address, listing.get("address_emphasis"))

    # Facts strip (price + beds/baths/sqft) — turns each card into an
    # MLS-style search result. Rendered only when a listing has facts.
    facts = listing.get("facts") or {}
    facts_row = ""
    price_chip = ""
    if facts:
        if facts.get("list_price_display") and not is_sold:
            price_chip = f'<span class="price-chip">{html_lib.escape(facts["list_price_display"])}</span>'
        specs = []
        if facts.get("beds") is not None:
            specs.append(f"{facts['beds']} bd")
        if facts.get("baths_display"):
            specs.append(f"{facts['baths_display']} ba")
        if facts.get("sqft_heated"):
            specs.append(f"{_fmt_int(facts['sqft_heated'])} sqft")
        price_html = (
            f'<span class="cf-price">{html_lib.escape(facts["list_price_display"])}</span>'
            if facts.get("list_price_display") and not is_sold else ""
        )
        specs_html = (
            f'<span class="cf-specs">{html_lib.escape(" · ".join(specs))}</span>'
            if specs else ""
        )
        if price_html or specs_html:
            facts_row = f'\n        <div class="card-facts">{price_html}{specs_html}</div>'

    return f"""    <a class="card" href="/properties/{slug}/" aria-label="{html_lib.escape(address)} listing tour">
      <div class="card-img">
        {badge}{price_chip}
        <img src="/properties/{slug}/media/{hero_photo}" alt="{html_lib.escape(address)}, {html_lib.escape(city)} — listing tour hero" loading="lazy" />
      </div>
      <div class="card-body">
        <h3 class="card-addr">{addr_em}</h3>
        <div class="card-meta">
          <span>{html_lib.escape(city)}, {html_lib.escape(state)}</span>
          <span class="pip"></span>
          <span>{photo_count} photos</span>
        </div>{facts_row}
        <span class="card-cta">View Tour <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></span>
      </div>
    </a>"""


def build_hub() -> None:
    listings = _load_published_listings()
    template = HUB_TEMPLATE_PATH.read_text(encoding="utf-8")

    if not listings:
        cards_html = (
            '    <div class="empty" style="grid-column:1/-1;">'
            '<h3>No public tours yet.</h3>'
            '<p>New listings will appear here as we publish them.</p>'
            '</div>'
        )
    else:
        cards_html = "\n".join(_render_card(l) for l in listings)

    total_count = len(listings)
    total_photos = sum(
        sum(len(s["photos"]) for s in l["sections"])
        for l in listings
    )

    replacements = {
        "{{cards_html}}": cards_html,
        "{{total_count}}": str(total_count),
        "{{total_photos}}": str(total_photos),
    }
    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    out = PROPERTIES_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(
        f"Built hub: {total_count} public tour(s), {total_photos} total photos -> {out}"
    )


# ============================================================
#  SCAFFOLD — create a new property folder (Phase: new listing)
# ============================================================

STARTER_SECTIONS = [
    {"id": "exterior", "title": "Curb Appeal", "sub": "Street presence & approach", "dir": "Home_Photos", "photos": []},
    {"id": "interior", "title": "Interior", "sub": "Living spaces", "dir": "Home_Photos", "photos": []},
    {"id": "aerial", "title": "Aerial & Lot", "sub": "The property from above", "dir": "Aerial_Photos", "photos": []},
]
STARTER_MEDIA_DIRS = ["Home_Photos", "Aerial_Photos"]


def slug_to_address(slug: str) -> str:
    """'2719-fort-worth-street' -> '2719 Fort Worth Street' (a starting point to edit)."""
    return " ".join(w.capitalize() for w in slug.split("-") if w)


def new_property(slug: str) -> None:
    """Scaffold properties/<slug>/ with a draft listing.json + media subfolders.

    Created as status="draft" + unlisted=true so it stays off the public hub
    until the owner fills in photos and flips those flags. Never overwrites an
    existing listing.json.
    """
    prop_dir = PROPERTIES_DIR / slug
    listing_path = prop_dir / "listing.json"
    if listing_path.exists():
        print(f"SKIP {slug}: listing.json already exists (left untouched).", file=sys.stderr)
        return

    address = slug_to_address(slug)
    parts = address.split()
    listing = {
        "slug": slug,
        "status": "draft",
        "unlisted": True,
        "address": address,
        "address_short": address,
        "address_emphasis": parts[-1] if parts else "",
        "city": "Sarasota",
        "state": "FL",
        "zip": "",
        "country": "US",
        "hero_kicker": "Sarasota, Florida · Full Visual Tour",
        "hero_describe": "A Southwest Florida home",
        "hero_categories": "Curb Appeal · Interior · Aerial",
        "hero_photo": "hero.jpg",
        "footer_note": "Photographed for listing",
        "sections": STARTER_SECTIONS,
    }

    for d in STARTER_MEDIA_DIRS:
        (prop_dir / "media" / d).mkdir(parents=True, exist_ok=True)
    listing_path.write_text(
        json.dumps(listing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Scaffolded {slug} (draft, unlisted):")
    print(f"  {listing_path}")
    print(f"  {prop_dir / 'media'}/  -> drop hero.jpg + photos into "
          + ", ".join(STARTER_MEDIA_DIRS) + "/")
    print("Next:")
    print("  1. Add photos to media/ subfolders (filenames go in listing.json 'photos').")
    print("  2. Fill in address, sections, and photo lists in listing.json.")
    print('  3. Set "status":"active" and "unlisted":false when ready to publish.')
    print(f"  4. Build it:  python tools/build-property.py {slug}")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1

    # --commit is a cross-cutting flag handled at the end.
    commit_requested = "--commit" in argv
    argv = [a for a in argv if a != "--commit"]

    if "--new" in argv:
        # Scaffolding doesn't produce committable output by itself.
        if commit_requested:
            print("Note: --commit is ignored with --new (nothing to publish until you add photos + run a build).", file=sys.stderr)
        slugs = [a for a in argv if a != "--new"]
        if not slugs:
            print("Usage: python tools/build-property.py --new <slug> [<slug> ...]", file=sys.stderr)
            return 1
        for slug in slugs:
            new_property(slug)
        return 0

    built_slugs: list[str] = []

    if "--hub" in argv:
        build_hub()
        argv = [a for a in argv if a != "--hub"]
        if not argv:
            if commit_requested:
                _commit_and_push([])  # hub-only — paths_to_stage still includes index + sitemap
            return 0

    if "--all" in argv:
        for prop_dir in sorted(PROPERTIES_DIR.iterdir()):
            if prop_dir.is_dir() and (prop_dir / "listing.json").exists():
                build(prop_dir.name)
                built_slugs.append(prop_dir.name)
        if not built_slugs:
            print("No properties with listing.json found in properties/")
        build_hub()
    else:
        for slug in argv:
            build(slug)
            built_slugs.append(slug)
        # Always refresh the hub after building any property so cards stay in sync.
        build_hub()

    if commit_requested:
        _commit_and_push(built_slugs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
