---
name: new-property
description: Publish a new property listing tour for LF Property Media from an MLS URL + a folder of photos. Scrapes the MLS for all listing facts, organizes the photos into sections by visual analysis, generates the property page, refreshes the /properties/ hub + sitemap, and optionally commits and pushes. Falls back to user-supplied facts when no MLS link is available.
---

# new-property

**Use this whenever the user wants to publish a new property tour** at
`lfpropertymedia.org/properties/<slug>/`. They will typically say things like
"new property", "let's add a listing", "publish a tour for X address", or
just paste an MLS URL.

## What you need from the user

Ask for these up front in a single concise message. Don't lecture.

1. **MLS URL** (preferred) — a public-facing MLS or IDX link. The studio uses
   Stellar MLS (via brokerages like Preferred Shore, Premier Sotheby's, etc.).
   - If no MLS link exists, ask for: address, beds, baths, living sq ft, lot
     size, year built, list price, list date, style/type, brief description.
2. **Photo source** — an absolute path to a folder of photos (almost always
   under `C:\Users\joshu\Downloads\...`). The folder usually has subfolders
   like `Home_Photos/` and `Aerial_Photos/`. If the structure is flat, ask
   the user to confirm which photos are aerial vs ground.
3. **Hero photo** (optional) — if the user has a preferred front-elevation
   shot, ask. Otherwise pick the strongest exterior front-of-house shot.
4. **Publish state** — default is `active` + visible on the hub. Ask if it
   should be `unlisted` (private share link, off-hub) or `draft` (built
   but flagged not for publishing yet).

## The procedure — follow in order

### 1. Determine the slug

Slug format: lowercase, kebab-case, derived from the address.
Examples: `2719-fort-worth-street`, `456-bayshore-rd`, `1234-gulf-of-mexico-dr`.
Strip directionals only if they help readability ("N", "S" stay; "North"
expanded to "n" is fine). Keep the street suffix abbreviated as it appears
on the MLS.

### 2. If MLS URL provided — scrape it

Use `WebFetch` on the URL with a prompt asking for the full record. Capture:

| Field | Notes |
|---|---|
| Full address | Street + unit + city + state + zip |
| List price | Numeric, no $ |
| Status | Active / Pending / Sold / Coming Soon |
| Beds / baths | Beds + full/half baths |
| Living sq ft | Heated/AC area |
| Total sq ft under roof | Often called "Gross" or "Total Building" |
| Lot size | Sq ft + acres + dimensions if given |
| Year built | |
| Style / type | "Mid-Century Modern", "Single Family Residence", etc. |
| MLS # | The listing number |
| Days on market | And original list date |
| Property description | The agent's prose block |
| Features | HVAC, roof, flooring, appliances, pool details, etc. |
| Agent + brokerage | Listing agent name + firm |

If WebFetch hits anti-bot/auth on the MLS URL, ask the user to paste the
MLS data sheet directly. Save the raw extract as
`properties/<slug>/mls-data.md` for future reference (the 2719 listing has
an example of the expected format).

### 3. Scaffold the property folder

```bash
python tools/build-property.py --new <slug>
```

This creates `properties/<slug>/` with a draft `listing.json` + empty
`media/Home_Photos/` and `media/Aerial_Photos/` subdirectories.

### 4. Copy photos into place

Copy from the user's source folder into the property's `media/`:

```bash
cp "/path/to/source/Home_Photos/"*.jpg properties/<slug>/media/Home_Photos/
cp "/path/to/source/Aerial_Photos/"*.jpg properties/<slug>/media/Aerial_Photos/
```

If photos are flat (no subfolders), ask the user which are aerial.
On Windows the paths often look like
`/c/Users/joshu/Downloads/<shoot-folder>/`.

### 5. Pick and resize the hero

Pick the best front-elevation exterior photo from `Home_Photos/`. Resize
it to ~1920px wide, 84 quality JPG, progressive:

```bash
python -c "from PIL import Image, ImageOps; im=ImageOps.exif_transpose(Image.open('properties/<slug>/media/Home_Photos/<file>.jpg')).convert('RGB'); im.thumbnail((1920,1920), Image.LANCZOS); im.save('properties/<slug>/media/hero.jpg', 'JPEG', quality=84, optimize=True, progressive=True)"
```

Target: hero.jpg under 600 KB.

### 6. Visually categorize photos into sections

Read each photo with the Read tool to bucket it. The default sections,
in display order, are:

1. **Curb Appeal** — front facade, entry, driveway, street view
2. **Living & Kitchen** — great room, kitchen, dining, hearth
3. **Loft / Bonus** *(only if the home has one)*
4. **Bedrooms** — all bedrooms incl. primary
5. **Baths & Utility** — bathrooms, laundry, mudroom
6. **Pool & Lanai** *(only if applicable)* — pool, cage, covered outdoor
7. **Backyard & Grounds** — yard, landscape, fences, gardens
8. **Aerial & Lot** — drone shots, always last

Omit sections with zero photos. For each photo, record only its **base
filename without extension** (e.g. `DSC07423`, not `DSC07423.jpg`).

If there are 30+ photos and visual sorting is taking too long, ask the
user to confirm a quick grouping you propose based on the first few of
each batch rather than reading every file.

### 7. Write listing.json

Use this skeleton, filled with the data above. Sections in display order.
Numbering is auto-derived by the build script.

```json
{
  "slug": "<slug>",
  "status": "active",
  "unlisted": false,
  "address": "<Street address>",
  "address_short": "<Short form with abbreviation>",
  "address_emphasis": "<Last word to italicize, e.g. Street, Road, Drive>",
  "city": "<City>",
  "state": "FL",
  "zip": "<zip>",
  "country": "US",
  "hero_kicker": "<City>, Florida · Full Visual Tour",
  "hero_describe": "<One-line property description>",
  "hero_categories": "<Top sections joined by · — e.g. Curb Appeal · Interior · Pool & Lanai · Aerial>",
  "hero_photo": "hero.jpg",
  "footer_note": "Photographed for listing",
  "facts": {
    "list_price": "<$725,000>",
    "beds": <int>,
    "baths_full": <int>,
    "baths_half": <int>,
    "living_sqft": <int>,
    "total_sqft": <int>,
    "lot_sqft": <int>,
    "lot_acres": "<0.25>",
    "lot_dimensions": "<75 × 108>",
    "year_built": <int>,
    "style": "<Mid-Century Modern>",
    "type": "<Single Family Residence>",
    "mls_number": "<A4696731>",
    "days_on_market": <int>,
    "list_date": "<YYYY-MM-DD>"
  },
  "sections": [
    {
      "id": "exterior",
      "title": "Curb Appeal",
      "sub": "Street presence & approach",
      "dir": "Home_Photos",
      "photos": ["DSC07519", "DSC07525", ...]
    },
    ... etc per section ...
  ]
}
```

The `facts` block is consumed by the **MLS Property Info data panel**
already wired into the listing-page template. If a fact is unknown, omit
the key rather than including a placeholder — the panel renders only
fields that are present.

### 8. Build the page

```bash
python tools/build-property.py <slug>
```

The script regenerates `properties/<slug>/index.html`, refreshes
`properties/index.html` (hub), and appends the new URL to `sitemap.xml`
(idempotent, skipped if already present, skipped entirely for unlisted
properties).

### 9. Preview check

Quickly verify:
- Hero photo renders (no broken image)
- Every section nav anchor smooth-scrolls to its section
- Property Info panel shows the facts you wrote
- Lightbox opens on tile click

If anything's off, edit `listing.json` and re-run step 8.

### 10. Publish

When the user confirms it's ready:

```bash
python tools/build-property.py <slug> --commit
```

This stages only `properties/<slug>/`, `properties/index.html`, and
`sitemap.xml`, commits with author "LF Property Media" / "openclaude
consulting@gmail.com", and pushes to `origin/main`. Cloudflare auto-
deploys in ~30 seconds.

Live URL: `https://lfpropertymedia.org/properties/<slug>/`
Hub: `https://lfpropertymedia.org/properties/`

## Edge cases

- **No MLS link** — collect the facts list manually from the user. The
  `facts` block can be partial; the panel hides missing fields. Skip
  `properties/<slug>/mls-data.md` (no source to transcribe).
- **HEIC / RAW photos** — ask the user to export to JPG first. The site
  serves JPG only.
- **Photos already on the web (e.g. agent emailed a Dropbox link)** —
  download them locally first, then proceed.
- **Property is sold or pending** — set `"status": "sold"` in
  `listing.json`. The hub card gets a "SOLD" badge automatically.
- **Privacy-sensitive listing** — set `"unlisted": true`. The page still
  builds at the direct URL but it's excluded from the hub and sitemap.
- **Address contains apostrophe / unusual char** — slugify normally;
  the script HTML-escapes display text safely.

## Reference files

- `tools/build-property.py` — the generator (read it if you need to
  understand the schema or extend the template)
- `tools/templates/property-page.html` — the page template (edit once,
  every property inherits the change)
- `tools/templates/properties-hub.html` — the hub template
- `properties/2719-fort-worth-street/listing.json` — canonical example
- `properties/2719-fort-worth-street/mls-data.md` — example MLS extract

## Don't

- Don't hand-edit `properties/<slug>/index.html` — it's generated and
  will be overwritten on the next build.
- Don't commit `.claude/` config or `mls-data.md` files containing
  private information.
- Don't publish AI-generated photos. Use the photographer's real files
  only.
- Don't reorder sections without updating `hero_categories` to match.
