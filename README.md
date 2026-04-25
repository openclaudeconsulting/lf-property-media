# LF Property Media — Website

Static marketing site for **LF Property Media**, a real estate photography studio in Sarasota, Florida.

## Stack

- Plain HTML + CSS. No build step, no framework.
- Google Fonts (Playfair Display + Inter) loaded from CDN.
- Contact form is a [HoneyBook](https://www.honeybook.com) inquiry placement (placement ID `687e66170ec3430007ca9da6`); leads land in the owner's HoneyBook dashboard.
- Designed to deploy on **Cloudflare Pages** (git-connected auto-deploy on push to `main`).

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — hero, reel, experience stats, what-we-shoot pillars, 3 packages preview, à la carte, social follow, CTA |
| `packages.html` | Full pricing: Signature/Premier/Platinum + square-footage adjustment + à la carte |
| `gallery.html` | Tabbed portfolio — Interior & Exterior / Drone & Aerial |
| `about.html` | Story, principles, specialization rationale |
| `contact.html` | HoneyBook inquiry widget + direct contact options |
| `faq.html` | 10 Q&A with FAQPage JSON-LD |
| `404.html` | Branded not-found page |

## Supporting files

- `css/styles.css` — all styles (design tokens in `:root`, section/component classes)
- `images/favicon.svg` — LF monogram favicon
- `images/` — drop real photos here (see "Images" below)
- `robots.txt`, `sitemap.xml` — SEO
- `_headers`, `_redirects` — Cloudflare Pages config
- `.gitignore` — excludes OS junk, editor files, raw photo formats, unrelated STLs

## Images — what's live and what's still placeholder

Real photos live in `images/` as AVIF. Filenames in use:

- `images/landing-page-house.avif` — home page hero (4:5 portrait)
- `images/reel-1.avif` — home page featured reel (still frame)
- `images/interior-livingroom.avif` — home Pillar 1 + gallery "Living room" tile
- `images/exterior-sunset.avif` — home Pillar 2 + gallery "Coastline sunset" drone tile
- `images/interior-kitchen.avif` — gallery "Kitchen" tile
- `images/exterior-beach-crib.avif` — gallery "Pool deck twilight" tile
- `images/reel-2.avif` — about page "Behind the scenes" tile

Remaining `.ph-tile` placeholders (gallery has ~11, about has the founder portrait) still render a cream tile with a label — drop in `<img src="images/..." alt="..." style="aspect-ratio:...;object-fit:cover;width:100%;" />` following the pattern in the swapped tiles above.

Also recommended:
- `images/og-image.jpg` — 1200×630 open-graph share image (not yet added).

## Brand tokens

All colors, fonts, and spacing live as CSS custom properties in `css/styles.css` under `:root` with the `--lf-*` prefix.

| Token | Hex |
|---|---|
| `--lf-paper` (page background) | `#faf8f5` |
| `--lf-white` | `#ffffff` |
| `--lf-cream` | `#f3ede2` |
| `--lf-ink` (primary text) | `#1a1a1a` |
| `--lf-muted` (secondary text) | `#6b6b6b` |
| `--lf-sand` (accent) | `#b08968` |
| `--lf-sand-dark` | `#8c6a4e` |
| `--lf-border` | `#e8e2d5` |

Fonts: **Playfair Display** (display, italic-accent headline) + **Inter** (body, UI, buttons).

## Local preview

No build step. Just open `index.html` in a browser, or run a local server:

```bash
python -m http.server 8000
# then visit http://localhost:8000
```

## Deploy to Cloudflare Pages

1. Push this repo to GitHub.
2. In Cloudflare dashboard: Pages → Create project → Connect to Git → select the repo.
3. Build settings: framework = `None`, build command = (leave blank), output directory = `/`.
4. Add custom domain (e.g., `lfpropertymedia.com`) under Custom domains.
5. Any push to `main` auto-deploys.

## Contact form (HoneyBook)

The contact form is a HoneyBook placement widget. Two pieces in `contact.html`:

1. The placement target `<div class="hb-p-687e66170ec3430007ca9da6-2"></div>` — HoneyBook injects the live form here on load.
2. The loader script just before `</body>` — fetches `placement-controller.min.js` and binds it to placement ID `687e66170ec3430007ca9da6`.

A 1×1 tracking pixel sits next to the placement div. Submitted inquiries land in the owner's HoneyBook dashboard, not in email — manage form fields, automations, and notification routing inside HoneyBook.

To swap to a different placement (e.g., a new HoneyBook account), replace every occurrence of `687e66170ec3430007ca9da6` in `contact.html` with the new placement ID.
