"""
LF Property Media — quote pricing engine.

Pure-Python, no dependencies. Called in-process by discord_bot.py to answer
quote requests. Mirrors the website's instant-quote calculator (packages.html
#build-quote) and the canonical pricing in CLAUDE.md.

SINGLE SOURCE OF TRUTH RULE
---------------------------
These numbers must match three places — there is no shared runtime:
  1. this file (the Discord bot)
  2. packages.html  (the website calculator JS)
  3. CLAUDE.md      (the published pricing table)
If a price changes, change it in all three. CLAUDE.md is canonical.

Base packages cover homes up to 1,600 sq ft. Above that, add $150 per
additional 1,000 sq ft (or any portion thereof) — rounded UP per bracket,
exactly like the website (Math.ceil).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ---- Canonical pricing (keep in sync with CLAUDE.md + packages.html) ----

PACKAGES = {
    "signature": {"label": "Signature", "price": 360},
    "premier":   {"label": "Premier",   "price": 550},
    "platinum":  {"label": "Platinum",  "price": 795},
    "alacarte":  {"label": "À la carte", "price": 0},
}

BASE_SQFT = 1600           # included square footage
SQFT_STEP = 1000           # bracket size above base
SQFT_STEP_PRICE = 150      # cost per bracket

ADDON_PHOTO_SET = 100      # 10 photos
ADDON_DRONE_EACH = 20      # per drone photo
ADDON_DRONE_SET5 = 100     # 5 drone photos
ADDON_CREATIVE_REEL = 300
ADDON_PRO_VIDEO = 425
ADDON_VIRTUAL_TOUR = 200
ADDON_VIRTUAL_TOUR_DISCOUNTED = 100   # with Premier / Platinum

# Packages that unlock the 50%-off virtual tour.
TOUR_DISCOUNT_PACKAGES = {"premier", "platinum"}


@dataclass
class QuoteInput:
    package: str = "signature"          # signature | premier | platinum | alacarte
    sqft: int = 0                       # heated square footage
    extra_photo_sets: int = 0          # sets of 10 photos
    extra_drone_photos: int = 0        # individual drone photos
    creative_reel: bool = False
    pro_video: bool = False
    virtual_tour: bool = False
    # Free-text interests that we quote separately (twilight, listing site, etc.)
    interests: list[str] = field(default_factory=list)


def _sqft_adjustment(sqft: int) -> int:
    """+$150 per additional 1,000 sq ft over 1,600, rounded up per bracket."""
    if sqft <= BASE_SQFT:
        return 0
    brackets = math.ceil((sqft - BASE_SQFT) / SQFT_STEP)
    return brackets * SQFT_STEP_PRICE


def _drone_cost(qty: int) -> int:
    """$100 per set of 5, $20 for each leftover. e.g. 7 -> 100 + 2*20 = 140."""
    if qty <= 0:
        return 0
    return (qty // 5) * ADDON_DRONE_SET5 + (qty % 5) * ADDON_DRONE_EACH


def compute_price(q: QuoteInput) -> dict:
    """Return a structured breakdown: line items + total."""
    pkg_key = (q.package or "signature").lower()
    if pkg_key not in PACKAGES:
        pkg_key = "signature"
    pkg = PACKAGES[pkg_key]

    lines: list[tuple[str, int]] = []

    base = pkg["price"]
    lines.append((f"{pkg['label']} package", base))

    adj = _sqft_adjustment(q.sqft)
    if adj:
        over = q.sqft - BASE_SQFT
        lines.append((f"Square-footage adjustment (+{over:,} sq ft over {BASE_SQFT:,})", adj))

    if q.extra_photo_sets > 0:
        c = q.extra_photo_sets * ADDON_PHOTO_SET
        lines.append((f"Extra photos ({q.extra_photo_sets} × 10)", c))

    if q.extra_drone_photos > 0:
        lines.append((f"Extra drone photos ({q.extra_drone_photos})", _drone_cost(q.extra_drone_photos)))

    if q.creative_reel:
        lines.append(("Creative reel", ADDON_CREATIVE_REEL))

    if q.pro_video:
        lines.append(("Professional video", ADDON_PRO_VIDEO))

    if q.virtual_tour:
        discounted = pkg_key in TOUR_DISCOUNT_PACKAGES
        price = ADDON_VIRTUAL_TOUR_DISCOUNTED if discounted else ADDON_VIRTUAL_TOUR
        label = "Virtual tour" + (" (50% off w/ package)" if discounted else "")
        lines.append((label, price))

    total = sum(c for _, c in lines)

    return {
        "package": pkg_key,
        "package_label": pkg["label"],
        "sqft": q.sqft,
        "lines": lines,
        "total": total,
        "interests": list(q.interests or []),
    }


def format_discord_reply(b: dict) -> str:
    """Render a compute_price() breakdown as a Discord markdown message."""
    out = []
    head = f"**Estimated quote — {b['package_label']}"
    if b.get("sqft"):
        head += f" · {b['sqft']:,} sq ft"
    head += "**"
    out.append(head)
    out.append("")
    for label, cost in b["lines"]:
        out.append(f"• {label}: ${cost:,}")
    out.append("")
    out.append(f"**Total estimate: ${b['total']:,}**")
    if b.get("interests"):
        out.append("")
        out.append("_Quoted separately: " + ", ".join(b["interests"]) + "_")
    out.append("")
    out.append("_Estimate only. Base packages cover homes up to 1,600 sq ft; "
               "final quote confirmed at booking._")
    return "\n".join(out)


if __name__ == "__main__":
    # Quick self-test
    demo = QuoteInput(package="premier", sqft=2400, virtual_tour=True,
                      extra_drone_photos=7, interests=["twilight shoot"])
    b = compute_price(demo)
    print(format_discord_reply(b))
    # premier 550 + sqft(2400-1600=800 -> 1 bracket = 150) + drone(7 -> 140)
    #   + tour(discounted 100) = 940
    assert b["total"] == 550 + 150 + 140 + 100, b["total"]
    print("\nself-test OK:", b["total"])
