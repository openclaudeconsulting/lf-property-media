---
name: update-property
description: Update an existing LF Property Media listing tour — add or remove photos, reorder or rename sections, change the hero, edit MLS facts, or change status (mark pending, sold, coming-soon, or pull it private). Edits the property's listing.json, rebuilds the page + hub + sitemap, and optionally commits and pushes. For publishing a brand-new listing from scratch, use the new-property skill instead.
---

# update-property

**Use this whenever the user wants to change a listing tour that already
exists** at `lfpropertymedia.org/properties/<slug>/`. They will say things
like "this listing went under contract — mark it pending", "the agent sent
5 more photos for 2719", "swap the hero on the Bayshore tour", "it sold",
"take that listing down", or "fix the price on X".

For a brand-new listing that doesn't exist yet, use **new-property** instead.

## First: identify the property

If the user names an address, map it to its slug under `properties/`. List
the folder if unsure:

```bash
ls properties/
```

Every property is one folder: `properties/<slug>/` with a `listing.json`
(the source of truth), a `media/` folder of photos, and a **generated**
`index.html`. You change `listing.json` and rebuild — never hand-edit
`index.html`.

Read the current `properties/<slug>/listing.json` before changing anything
so you edit from the real current state.

## Common updates

### Change status

The top-level `status` field drives the hub card badge and price. Supported
values:

| `status` | Hub card | Price on card |
|---|---|---|
| `active` (default) | Listed, no badge | Shown |
| `pending` | Listed, **"Pending"** badge | Shown |
| `coming-soon` | Listed, **"Coming Soon"** badge | Shown |
| `sold` | Listed, **"Sold"** badge | **Hidden** |
| `draft` | **Hidden from the hub** | n/a |

**Hub visibility and sitemap indexing are governed by the `unlisted` flag,
not by `status`** — with one exception: `status: "draft"` also hides a
property from the hub. Specifically:
- `unlisted: true` → removed from **both** the hub and the sitemap (the
  tour page still works by direct link).
- `status: "draft"` → hidden from the hub; sitemap inclusion still follows
  the `unlisted` flag. The `--new` scaffolder sets `draft` **and**
  `unlisted: true` together, so a new shell stays fully hidden until you
  publish.
- All other statuses (`active`, `pending`, `coming-soon`, `sold`) appear on
  the hub and in the sitemap as long as `unlisted` is false.

Set the top-level `"status"`, then rebuild. If a `facts` block exists, also
update `facts.status` (the display text in the Property Info panel) to match —
e.g. top-level `"status": "pending"` pairs with `"facts": { "status": "Pending" }`.

- **Under contract** → `"status": "pending"`, `facts.status: "Pending"`
- **Closed** → `"status": "sold"`, `facts.status: "Sold"`
- **Not yet on market** → `"status": "coming-soon"`, `facts.status: "Coming Soon"`
- **Back on market** → `"status": "active"`, `facts.status: "Active"`

### Add photos

1. Copy the new files into the right `media/` subfolder
   (`Home_Photos/` for ground, `Aerial_Photos/` for drone):

   ```bash
   cp "/path/to/new/"*.jpg properties/<slug>/media/Home_Photos/
   ```

2. If any are HEIC/RAW, ask the user to export to JPG first — the site
   serves JPG only.
3. Add each new photo's **base filename without extension** to the right
   section's `photos` array in `listing.json`, in the position you want it
   to appear.
4. Rebuild.

### Remove photos

Delete the filename from the section's `photos` array in `listing.json`
(and optionally delete the file from `media/`). Rebuild. The lightbox and
counts re-derive automatically.

### Reorder or rename sections

Reorder the objects in the `sections` array — display order and the `01`,
`02`… numbering follow the array order (the build script auto-numbers).
Aerial conventionally stays last. To rename, edit a section's `title` /
`sub`. **If you change which sections lead, update `hero_categories`** so
the hero meta line still matches.

### Change the hero photo

Pick the new front shot, resize it to ~1920px wide and overwrite
`media/hero.jpg`:

```bash
python -c "from PIL import Image, ImageOps; im=ImageOps.exif_transpose(Image.open('properties/<slug>/media/Home_Photos/<file>.jpg')).convert('RGB'); im.thumbnail((1920,1920), Image.LANCZOS); im.save('properties/<slug>/media/hero.jpg', 'JPEG', quality=84, optimize=True, progressive=True)"
```

`hero_photo` in `listing.json` stays `"hero.jpg"` — no JSON change needed
unless you use a different filename. Rebuild.

### Edit MLS facts / price

Edit the relevant keys in the `facts` block of `listing.json` (e.g.
`list_price`, `list_price_display`, `days_on_market`, `updates`). The
Property Info panel only renders keys that are present, so omit rather than
blank out a fact you want gone. Rebuild.

### Pull a listing private or take it down

- **Private share link only** (off the hub + sitemap, page still reachable
  by direct URL) → set `"unlisted": true`. Rebuild. Note: the URL already
  in the sitemap is not auto-removed — if it must leave the sitemap, delete
  that `<url>` block from `sitemap.xml` by hand.
- **Fully retire** → delete the `properties/<slug>/` folder and its
  `sitemap.xml` entry, then rebuild the hub with `--hub`.

## Build and publish

Every update ends the same way. Rebuild the property (this also refreshes
the hub and keeps the sitemap in sync):

```bash
python tools/build-property.py <slug>
```

Preview `properties/<slug>/index.html` if the change is visual. When the
user confirms, publish:

```bash
python tools/build-property.py <slug> --commit
```

`--commit` stages only `properties/<slug>/`, `properties/index.html`, and
`sitemap.xml`, commits as "LF Property Media", and pushes to `origin/main`.
Cloudflare auto-deploys in ~30 seconds. If you only changed status/hub-level
things across multiple listings, `python tools/build-property.py --all --commit`
rebuilds everything.

The build is fully idempotent — safe to run repeatedly; it overwrites the
generated page cleanly and won't create duplicate sitemap entries.

## Edge cases

- **Wrong photo orientation after add** — the build doesn't rotate; if a
  photo is sideways, the source file's EXIF is off. Re-export it upright or
  run it through the hero resize one-liner (which applies `exif_transpose`)
  to bake in the correct orientation.
- **Changed the slug / address** — a slug change means a new URL. Treat it
  as a new property (copy the folder to the new slug, rebuild, and add a
  redirect from the old URL in `_redirects` if it was already shared).
- **Status says pending but price should hide** — only `sold` hides price
  by design. If the owner wants a pending listing's price hidden, remove
  `list_price` / `list_price_display` from the `facts` block.
- **Hub didn't update after a status change** — the hub always rebuilds on
  any `build-property.py` run; if it still looks stale it's browser/Cloudflare
  cache, not the build. Hard-refresh.

## Reference files

- `tools/build-property.py` — the generator (status badge map lives in
  `_render_card`; hub filtering in `_load_published_listings`)
- `tools/templates/property-page.html` — the listing-page template
- `tools/templates/properties-hub.html` — the hub template (badge CSS)
- `properties/2719-fort-worth-street/listing.json` — canonical example with
  a full `facts` block
- `.claude/skills/new-property/SKILL.md` — the sibling skill for new listings

## Don't

- Don't hand-edit `properties/<slug>/index.html` — it's generated and the
  next build overwrites it. Change `listing.json` instead.
- Don't forget `facts.status` when you change top-level `status` — the hub
  badge and the panel text are two different fields.
- Don't reorder sections without updating `hero_categories` to match.
- Don't publish AI-generated or stock photos — the photographer's real
  files only.
