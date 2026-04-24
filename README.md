# LF Property Media — Website

Static marketing site for **LF Property Media**, a real estate photography studio in Sarasota, Florida.

## Stack

- Plain HTML + CSS. No build step, no framework.
- Google Fonts (Playfair Display + Inter) loaded from CDN.
- Contact form submits via [Formsubmit.co](https://formsubmit.co) to `l.f.gallery03@gmail.com`.
- Designed to deploy on **Cloudflare Pages** (git-connected auto-deploy on push to `main`).

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — hero, reel, experience stats, what-we-shoot pillars, 3 packages preview, à la carte, social follow, CTA |
| `packages.html` | Full pricing: Signature/Premier/Platinum + square-footage adjustment + à la carte |
| `gallery.html` | Tabbed portfolio — Interior & Exterior / Drone & Aerial |
| `about.html` | Story, principles, specialization rationale |
| `contact.html` | Inquiry form (Formsubmit.co) + direct contact options |
| `faq.html` | 10 Q&A with FAQPage JSON-LD |
| `404.html` | Branded not-found page |

## Supporting files

- `css/styles.css` — all styles (design tokens in `:root`, section/component classes)
- `images/favicon.svg` — LF monogram favicon
- `images/` — drop real photos here (see "Images" below)
- `robots.txt`, `sitemap.xml` — SEO
- `_headers`, `_redirects` — Cloudflare Pages config
- `.gitignore` — excludes OS junk, editor files, raw photo formats, unrelated STLs

## Images — what to drop in

The site currently renders placeholder tiles. Replace `.ph-tile` divs with real `<img>` tags. Suggested filenames:

- `images/hero-realestate.jpg` — home page hero (4:5 portrait, bright interior)
- `images/featured-reel.mp4` + `images/reel-poster.jpg` — home page reel
- `images/pillar-interior.jpg`, `images/pillar-drone.jpg` — what-we-shoot cards on home
- `images/about-founder.jpg`, `images/about-bts.jpg` — about page
- `images/og-image.jpg` — 1200×630 open-graph share image
- Gallery: `images/re-01.jpg`, `re-02.jpg` … `aerial-01.jpg` …

Each placeholder has an HTML comment showing the exact `<img>` tag to use.

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

## Contact form (Formsubmit.co)

The first time someone submits the form, Formsubmit emails `l.f.gallery03@gmail.com` with a confirmation link. Click it once — after that, all inquiries land in the inbox formatted as a table.

To change the recipient, update the `action` URL on `contact.html:~64`.
