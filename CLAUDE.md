# Project Briefing — LF Property Media Website

This file is auto-loaded by Claude Code. It orients you without needing to re-read every file.

## What this is

A static marketing website for **LF Property Media**, a real estate and automotive photography studio based in Sarasota, Florida. Two core verticals:

1. **Real estate photography** — listings, MLS-ready photos, drone aerials, reels, virtual tours, floor plans.
2. **Automotive photography** — dealer inventory, private collections, custom builds, events.

Tagline: **"Visuals that sell. Branding that speaks."**

## Stack

- Plain HTML + CSS. No framework, no build step.
- Google Fonts (Playfair Display + Inter) via CDN.
- Contact form posts to **Formsubmit.co** → `l.f.gallery03@gmail.com`.
- Deploy target: **Cloudflare Pages** (git-connected).

## File map

```
lf-property-media/
├── index.html          Home — hero, reel, stats, 2 pillars, packages, à la carte, social, CTA
├── packages.html       Full pricing + sq-ft adjustment + à la carte + notes
├── gallery.html        Tabbed portfolio: Real Estate / Automotive / Drone
├── about.html          Story, 6 principles, two-specialty rationale
├── contact.html        Formsubmit.co form + direct contact options (tel/email/IG)
├── faq.html            11 Q&A with FAQPage JSON-LD
├── 404.html            Branded not-found
├── css/styles.css      All styles — tokens in :root, component classes
├── images/favicon.svg  LF monogram favicon
├── images/             Drop real photos here (see README for expected filenames)
├── robots.txt, sitemap.xml
├── _headers, _redirects   Cloudflare Pages config
├── README.md           Deploy + dev notes
└── .gitignore
```

## Brand system

Light/airy editorial photography aesthetic. Warm off-white page, charcoal text, sand/terracotta accent, Playfair Display serif for headlines with italic emphasis on accent words.

| Token | Color | Hex |
|---|---|---|
| `--lf-paper` | Warm off-white (page bg) | `#faf8f5` |
| `--lf-white` | Surface white | `#ffffff` |
| `--lf-cream` | Soft cream (alt bg) | `#f3ede2` |
| `--lf-ink` | Primary text | `#1a1a1a` |
| `--lf-muted` | Secondary text | `#6b6b6b` |
| `--lf-sand` | Accent (warm tan) | `#b08968` |
| `--lf-sand-dark` | Accent dark | `#8c6a4e` |
| `--lf-sand-light` | Accent light | `#d4b896` |
| `--lf-sand-soft` | Accent soft bg | `#ede2d1` |
| `--lf-border` | Borders | `#e8e2d5` |

Fonts:
- **Playfair Display** — headlines, package names, prices, brand mark. Italic variant is used for accent words (e.g., *sell*, *speaks*).
- **Inter** — body copy, UI chrome, buttons (uppercase with letterspacing).

## Pricing — do not change without approval

Base prices cover homes up to 1,600 sq ft:

- **Signature** — $360 — 36 photos (30 home + 6 drone), short reel, 2D floorplan, 24-hr delivery
- **Premier** — $550 — 50 photos (40 + 10 drone), creative reel, 2D floorplans, 50% off virtual tour
- **Platinum** — $795 — 72 photos (56 + 16 drone), scripted reel with mic, 2D + 3D dollhouse, 50% off virtual tour

**Square footage adjustment:** +$150 per additional 1,000 sq ft (or portion thereof) beyond 1,600 sq ft, applied to all three packages. Stated transparently in the UI; never hidden.

**À la carte:** 10 photos $100 · drone $20 ea / $100 set of 5 · creative reel $300 · pro video $425 · virtual tour $200 · automotive shoots quoted per job.

## Contact info (do not change)

- Phone: **(941) 387-5399**
- Email: **l.f.gallery03@gmail.com**
- Instagram: **@lfpropertymedia**
- Location: Sarasota, FL · Southwest Florida service area

## Tone of voice

Confident, minimalist, editorial. Short sentences. The brand is aspirational but not pretentious. Think: photography-first agency that charges fair prices and delivers fast. Avoid jargon, avoid marketing clichés, avoid exclamation points.

Italic accents on key emotional words are a signature move (e.g., "Visuals that *sell*", "show your property the way *it should be seen*").

## Conventions

- **Shared header/footer is duplicated across pages** — no template engine. If you add a nav link, update it on every HTML file including `404.html`.
- **Active nav item:** add `class="active"` to the current page's nav link.
- **Placeholder images:** use `<div class="ph-tile">Label</div>` where a photo isn't in yet — each placeholder has an HTML comment showing the real `<img>` tag to swap in.
- **Void elements:** self-closing slash (`<meta ... />`, `<link ... />`).
- **Prefer CSS tokens** — new components should use existing `--lf-*` variables and the `.section.block` / `.container` / `.grid` patterns rather than one-off styles.

## Things NOT to do without asking

- Don't add a JavaScript framework. This site doesn't need React/Vue/Svelte.
- Don't add analytics or tracking scripts without confirming with the owner.
- Don't change the contact phone or email — leads must route through the existing inbox.
- Don't change pricing without explicit approval. Prices are public-facing commitments.
- Don't inline large images as base64; keep them in `images/`.
- Don't replace placeholder tiles with stock photos. Only the owner's real work goes in the gallery.

## Deploy

1. Push to `main` on GitHub (repo: `openclaudeconsulting/lf-property-media`).
2. Cloudflare Pages auto-builds (no build command needed — static files).
3. Live at the connected custom domain.
