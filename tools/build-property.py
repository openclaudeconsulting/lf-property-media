#!/usr/bin/env python3
"""
Generate a property listing tour page from listing.json + a shared HTML template.

Usage
-----
  python tools/build-property.py <slug>            # build one property
  python tools/build-property.py <slug> <slug>     # build many
  python tools/build-property.py --all             # rebuild every property

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
SITE_URL = "https://lfpropertymedia.org"


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


def build_all() -> None:
    found = 0
    for prop_dir in sorted(PROPERTIES_DIR.iterdir()):
        if prop_dir.is_dir() and (prop_dir / "listing.json").exists():
            build(prop_dir.name)
            found += 1
    if found == 0:
        print("No properties with listing.json found in properties/")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    if "--all" in argv:
        build_all()
        return 0
    for slug in argv:
        build(slug)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
