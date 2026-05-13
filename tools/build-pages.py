"""
Generate service + area landing pages for LF Property Media.

Each page is keyword-targeted for local SEO + AI/GEO. Schema is
LocalBusiness with serviceArea / Service for the relevant entity.
Output:
  services/real-estate-photography.html
  services/drone-photography.html
  services/twilight-photography.html
  services/3d-tours.html
  areas/sarasota.html
  areas/siesta-key.html
  areas/bird-key.html
  areas/lakewood-ranch.html
  areas/longboat-key.html
  areas/palmer-ranch.html
  areas/venice.html
  areas/osprey.html
"""
from pathlib import Path
import html

ROOT = Path(__file__).parent.parent
SERVICES_DIR = ROOT / "services"
AREAS_DIR = ROOT / "areas"
SERVICES_DIR.mkdir(exist_ok=True)
AREAS_DIR.mkdir(exist_ok=True)

SITE_URL = "https://lfpropertymedia.org"


def shared_head(title, description, canonical, og_image="https://lfpropertymedia.org/images/og-image.jpg",
                rel_root="../", extra_keywords="", extra_schema=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}" />
<meta name="keywords" content="{html.escape(extra_keywords)}" />
<link rel="canonical" href="{canonical}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="{rel_root}css/styles.css?v=2" />
<link rel="icon" type="image/svg+xml" href="{rel_root}images/favicon.svg" />
<meta property="og:site_name" content="LF Property Media" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{canonical}" />
<meta property="og:title" content="{html.escape(title)}" />
<meta property="og:description" content="{html.escape(description)}" />
<meta property="og:image" content="{og_image}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html.escape(title)}" />
<meta name="twitter:description" content="{html.escape(description)}" />
<meta name="twitter:image" content="{og_image}" />
{extra_schema}
</head>"""


def shared_header(rel_root="../"):
    """Topbar + main nav. No 'active' class — these are sub-pages."""
    return f"""<body>
<a class="skip-link" href="#main">Skip to content</a>

<div class="topbar">
  <div class="container">
    <span>Sarasota, FL &middot; Southwest Florida</span>
    <span><a href="tel:+19413875399">(941) 387-5399</a> &nbsp;&middot;&nbsp; <a href="mailto:l.f.gallery03@gmail.com">l.f.gallery03@gmail.com</a></span>
  </div>
</div>

<header class="site-header">
  <div class="container">
    <a class="brand" href="{rel_root}index.html">
      <span class="brand-mark">LF<em>.</em></span>
      <span>
        <span style="display:block;font-family:var(--font-display);font-size:1.05rem;line-height:1;color:var(--lf-ink);">Property Media</span>
        <span class="brand-tag">Sarasota &middot; Florida</span>
      </span>
    </a>
    <button class="nav-toggle" aria-label="Open menu" aria-expanded="false" onclick="document.querySelector('.main-nav').classList.toggle('open');document.querySelector('.nav-overlay').classList.toggle('open');this.setAttribute('aria-expanded',this.getAttribute('aria-expanded')==='false')">
      <span></span><span></span><span></span>
    </button>
    <div class="nav-overlay" onclick="document.querySelector('.main-nav').classList.remove('open');this.classList.remove('open');document.querySelector('.nav-toggle').setAttribute('aria-expanded','false')"></div>
    <nav class="main-nav" aria-label="Main">
      <ul>
        <li><a href="{rel_root}index.html">Home</a></li>
        <li><a href="{rel_root}packages.html">Packages</a></li>
        <li><a href="{rel_root}gallery.html">Gallery</a></li>
        <li><a href="{rel_root}about.html">About</a></li>
        <li><a href="{rel_root}faq.html">FAQ</a></li>
        <li><a class="nav-cta" href="{rel_root}contact.html">Book Now</a></li>
      </ul>
    </nav>
  </div>
</header>

<main id="main">
"""


def shared_footer(rel_root="../"):
    return f"""</main>

<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <span class="footer-brand">LF<em>.</em> Property Media</span>
        <p>Premium real estate photography serving Sarasota and Southwest Florida since 2021.</p>
      </div>
      <div>
        <h4>Explore</h4>
        <ul>
          <li><a href="{rel_root}index.html">Home</a></li>
          <li><a href="{rel_root}packages.html">Packages</a></li>
          <li><a href="{rel_root}gallery.html">Gallery</a></li>
          <li><a href="{rel_root}about.html">About</a></li>
          <li><a href="{rel_root}faq.html">FAQ</a></li>
        </ul>
      </div>
      <div>
        <h4>Services</h4>
        <ul>
          <li><a href="{rel_root}services/real-estate-photography.html">Real Estate Photography</a></li>
          <li><a href="{rel_root}services/drone-photography.html">Drone Photography</a></li>
          <li><a href="{rel_root}services/twilight-photography.html">Twilight Photography</a></li>
          <li><a href="{rel_root}services/3d-tours.html">3D Virtual Tours</a></li>
        </ul>
      </div>
      <div>
        <h4>Areas We Serve</h4>
        <ul>
          <li><a href="{rel_root}areas/sarasota.html">Sarasota</a></li>
          <li><a href="{rel_root}areas/siesta-key.html">Siesta Key</a></li>
          <li><a href="{rel_root}areas/lakewood-ranch.html">Lakewood Ranch</a></li>
          <li><a href="{rel_root}areas/longboat-key.html">Longboat Key</a></li>
          <li><a href="{rel_root}areas/bird-key.html">Bird Key</a></li>
          <li><a href="{rel_root}areas/palmer-ranch.html">Palmer Ranch</a></li>
          <li><a href="{rel_root}areas/venice.html">Venice</a></li>
          <li><a href="{rel_root}areas/osprey.html">Osprey</a></li>
        </ul>
      </div>
      <div>
        <h4>Get In Touch</h4>
        <ul>
          <li><a href="tel:+19413875399">(941) 387-5399</a></li>
          <li><a href="mailto:l.f.gallery03@gmail.com">l.f.gallery03@gmail.com</a></li>
          <li>Sarasota, FL</li>
          <li><a href="https://instagram.com/lfpropertymedia" target="_blank" rel="noopener">@lfpropertymedia</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span id="yr"></span> LF Property Media. All rights reserved.</span>
      <span>Sarasota, FL &middot; Real Estate Photography</span>
    </div>
  </div>
</footer>

<script>
document.getElementById('yr').textContent = new Date().getFullYear();
const reveals = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {{
  const observer = new IntersectionObserver(function(entries) {{
    entries.forEach(function(entry) {{
      if (entry.isIntersecting) {{ entry.target.classList.add('visible'); observer.unobserve(entry.target); }}
    }});
  }}, {{ threshold: 0.12 }});
  reveals.forEach(function(el) {{ observer.observe(el); }});
}} else {{
  reveals.forEach(function(el) {{ el.classList.add('visible'); }});
}}
</script>
<script src="{rel_root}js/gallery-preload.js" defer></script>
</body>
</html>
"""


# ===== SERVICE PAGE TEMPLATE =====

def service_page(slug, title, description, h1, lede, sections, faq_items, related_imgs, keywords):
    canonical = f"{SITE_URL}/services/{slug}.html"
    rel = "../"
    schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "{title.split(' | ')[0]}",
  "url": "{canonical}",
  "description": "{description}",
  "provider": {{
    "@type": "LocalBusiness",
    "name": "LF Property Media",
    "url": "{SITE_URL}/",
    "telephone": "+1-941-387-5399",
    "email": "l.f.gallery03@gmail.com",
    "address": {{
      "@type": "PostalAddress",
      "addressLocality": "Sarasota",
      "addressRegion": "FL",
      "addressCountry": "US"
    }}
  }},
  "areaServed": [
    {{ "@type": "City", "name": "Sarasota", "addressRegion": "FL" }},
    {{ "@type": "Place", "name": "Siesta Key" }},
    {{ "@type": "Place", "name": "Longboat Key" }},
    {{ "@type": "Place", "name": "Lakewood Ranch" }}
  ]
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{",".join(f'    {{ "@type": "Question", "name": "{html.escape(q)}", "acceptedAnswer": {{ "@type": "Answer", "text": "{html.escape(a)}" }} }}' for q, a in faq_items)}
  ]
}}
</script>"""

    body_sections = ""
    for sec in sections:
        body_sections += f"""
<section class="bg-white">
  <div class="container-narrow">
    <div class="section-head reveal"><h2>{html.escape(sec['heading'])}</h2><span class="divider"></span></div>
    {sec['body']}
  </div>
</section>
"""

    faq_html = "\n".join(
        f'        <details class="faq-item"><summary>{html.escape(q)}</summary><div class="faq-answer">{html.escape(a)}</div></details>'
        for q, a in faq_items
    )

    img_html = "\n".join(
        f'        <figure><img src="{rel}{img["src"]}" alt="{html.escape(img["alt"])}" decoding="async" loading="lazy" /></figure>'
        for img in related_imgs
    )

    return (
        shared_head(title, description, canonical, rel_root=rel, extra_keywords=keywords, extra_schema=schema)
        + shared_header(rel)
        + f"""
<section class="hero" style="padding:100px 0 60px;">
  <div class="container">
    <div class="section-head" style="margin-bottom:0;">
      <span class="kicker">Sarasota Real Estate Photography</span>
      <h1 style="font-size:clamp(2.4rem,5vw,3.6rem);">{html.escape(h1)}</h1>
      <p class="lede-large" style="margin:24px auto 0;max-width:760px;">{html.escape(lede)}</p>
      <div class="btn-row" style="justify-content:center;margin-top:32px;">
        <a href="{rel}contact.html" class="btn btn-primary">Book a Shoot</a>
        <a href="{rel}packages.html" class="btn btn-secondary">View Packages</a>
      </div>
    </div>
  </div>
</section>

{body_sections}

<section class="bg-cream">
  <div class="container">
    <div class="section-head reveal"><h2>Sample work</h2><span class="divider"></span></div>
    <div class="gallery-masonry">
{img_html}
    </div>
    <p style="text-align:center;margin-top:32px;"><a href="{rel}gallery.html" class="btn-ghost">See the full gallery &rarr;</a></p>
  </div>
</section>

<section class="bg-white">
  <div class="container-narrow">
    <div class="section-head reveal"><span class="kicker">FAQ</span><h2>Common questions</h2><span class="divider"></span></div>
    <div class="faq-list">
{faq_html}
    </div>
  </div>
</section>

<section class="cta-banner">
  <div class="container">
    <h2>Ready to book?</h2>
    <p>Send us the property. We'll come back with a quote in under 24 hours.</p>
    <a href="{rel}contact.html" class="btn btn-light">Get a Quote</a>
  </div>
</section>
"""
        + shared_footer(rel)
    )


# ===== AREA PAGE TEMPLATE =====

def area_page(slug, area_name, title, description, h1, lede, area_context, neighborhoods_blurb, faq_items, related_imgs, keywords):
    canonical = f"{SITE_URL}/areas/{slug}.html"
    rel = "../"
    schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "LF Property Media — {area_name} Real Estate Photography",
  "url": "{canonical}",
  "image": "https://lfpropertymedia.org/images/og-image.jpg",
  "description": "{description}",
  "telephone": "+1-941-387-5399",
  "email": "l.f.gallery03@gmail.com",
  "priceRange": "$360–$795+",
  "areaServed": {{
    "@type": "Place",
    "name": "{area_name}"
  }},
  "provider": {{
    "@type": "LocalBusiness",
    "name": "LF Property Media",
    "url": "{SITE_URL}/"
  }}
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{",".join(f'    {{ "@type": "Question", "name": "{html.escape(q)}", "acceptedAnswer": {{ "@type": "Answer", "text": "{html.escape(a)}" }} }}' for q, a in faq_items)}
  ]
}}
</script>"""

    faq_html = "\n".join(
        f'        <details class="faq-item"><summary>{html.escape(q)}</summary><div class="faq-answer">{html.escape(a)}</div></details>'
        for q, a in faq_items
    )

    img_html = "\n".join(
        f'        <figure><img src="{rel}{img["src"]}" alt="{html.escape(img["alt"])}" decoding="async" loading="lazy" /></figure>'
        for img in related_imgs
    )

    return (
        shared_head(title, description, canonical, rel_root=rel, extra_keywords=keywords, extra_schema=schema)
        + shared_header(rel)
        + f"""
<section class="hero" style="padding:100px 0 60px;">
  <div class="container">
    <div class="section-head" style="margin-bottom:0;">
      <span class="kicker">Sarasota Area · Real Estate Photography</span>
      <h1 style="font-size:clamp(2.4rem,5vw,3.6rem);">{html.escape(h1)}</h1>
      <p class="lede-large" style="margin:24px auto 0;max-width:760px;">{html.escape(lede)}</p>
      <div class="btn-row" style="justify-content:center;margin-top:32px;">
        <a href="{rel}contact.html" class="btn btn-primary">Book a {html.escape(area_name)} Shoot</a>
        <a href="{rel}packages.html" class="btn btn-secondary">View Packages</a>
      </div>
    </div>
  </div>
</section>

<section class="bg-white">
  <div class="container-narrow">
    <div class="section-head reveal"><h2>About {html.escape(area_name)}</h2><span class="divider"></span></div>
    {area_context}
  </div>
</section>

<section class="bg-cream">
  <div class="container-narrow">
    <div class="section-head reveal"><h2>What makes {html.escape(area_name)} listings photograph well</h2><span class="divider"></span></div>
    {neighborhoods_blurb}
  </div>
</section>

<section class="bg-white">
  <div class="container">
    <div class="section-head reveal"><h2>Recent {html.escape(area_name)} work</h2><span class="divider"></span></div>
    <div class="gallery-masonry">
{img_html}
    </div>
    <p style="text-align:center;margin-top:32px;"><a href="{rel}gallery.html" class="btn-ghost">See the full gallery &rarr;</a></p>
  </div>
</section>

<section class="bg-cream">
  <div class="container-narrow">
    <div class="section-head reveal"><span class="kicker">FAQ</span><h2>Common questions — {html.escape(area_name)}</h2><span class="divider"></span></div>
    <div class="faq-list">
{faq_html}
    </div>
  </div>
</section>

<section class="cta-banner">
  <div class="container">
    <h2>Book a {html.escape(area_name)} shoot</h2>
    <p>Send the address and we'll come back with a quote in under 24 hours.</p>
    <a href="{rel}contact.html" class="btn btn-light">Get a Quote</a>
  </div>
</section>
"""
        + shared_footer(rel)
    )


# ===== DATA: SERVICE PAGES =====

SERVICE_PAGES = [
    {
        "slug": "real-estate-photography",
        "title": "Real Estate Photography in Sarasota, FL | LF Property Media",
        "description": "Sarasota real estate photography by LF Property Media. MLS-ready interior and exterior photos hand-edited for true-to-life light. 24-hour delivery. Packages from $360.",
        "keywords": "real estate photography Sarasota, real estate photographer Sarasota FL, MLS photography, Sarasota listing photographer, interior photography Sarasota, exterior real estate photos",
        "h1": "Real Estate Photography in Sarasota",
        "lede": "MLS-ready photos that move listings. Hand-edited, color-corrected, delivered in 24 hours so your property hits the market on day one — not day three.",
        "sections": [
            {
                "heading": "What you get on every shoot",
                "body": """<p>Every Sarasota real estate photography shoot includes hand-edited interior and exterior photos sized and named correctly for MLS. We blend multiple exposures so windows don't blow out and shadows stay readable. No AI sky replacement, no synthetic compositing — just careful editing that makes the property look like itself on its best day.</p>
<ul style="margin-top:20px;padding-left:24px;line-height:1.8;">
  <li><strong>Wide-angle interior coverage</strong> — every room shot from multiple angles so the agent has selection</li>
  <li><strong>Twilight-ready exposures</strong> — interior windows balanced against natural daylight</li>
  <li><strong>Hand-edited blends</strong> — no AI shortcuts, no fake skies</li>
  <li><strong>MLS-correct file sizes</strong> — uploaded straight to your CRM with no re-export needed</li>
  <li><strong>Web + social crops</strong> — vertical and horizontal versions for Zillow, Realtor.com, Instagram</li>
</ul>"""
            },
            {
                "heading": "Pricing — straightforward, published, no surprises",
                "body": """<p>Three packages, all with photo + drone + reel included. Square-footage adjustments are stated on the packages page, not sprung at invoice.</p>
<ul style="margin-top:20px;padding-left:24px;line-height:1.8;">
  <li><strong>Signature — $360.</strong> 36 photos (30 home + 6 drone), short reel, 2D floor plan, 24-hour photo delivery. Best for under 1,600 sq ft listings.</li>
  <li><strong>Premier — $550.</strong> 50 photos (40 + 10 drone), creative reel on pro camera, 2D floor plans, 50% off virtual tour.</li>
  <li><strong>Platinum — $795.</strong> 72 photos (56 + 16 drone), scripted reel with realtor mic'd, 2D + 3D dollhouse floor plan, 50% off virtual tour.</li>
</ul>
<p style="margin-top:20px;">Base prices cover homes up to 1,600 sq ft. Larger homes add $150 per additional 1,000 sq ft. <a href="../packages.html">Full pricing here.</a></p>"""
            },
            {
                "heading": "Service area",
                "body": """<p>LF Property Media serves all of Sarasota County and most of Manatee County. Standard service area includes Sarasota, Siesta Key, Lakewood Ranch, Longboat Key, Bird Key, Palmer Ranch, Venice, Osprey, and Bradenton. Shoots outside that footprint are still available with a small travel fee — just send the address and we'll quote.</p>"""
            }
        ],
        "faq_items": [
            ("How fast do I get my photos back?", "Photos are delivered in 24 hours from every shoot. Reels and walkthrough videos take longer (3–5 business days) because of editing."),
            ("Do you use AI to edit the photos?", "No. Every photo is hand-edited. No AI sky replacement, no synthetic compositing. Your listing looks like itself."),
            ("Do you provide MLS-ready file sizes?", "Yes. Files are sized, color-corrected, and named so they upload straight to your MLS or CRM with no re-export."),
            ("Can I get vertical crops for Instagram?", "Yes — vertical and square crops are included on Premier and Platinum. Available as a $50 add-on on Signature."),
            ("Do you photograph commercial real estate?", "Primarily residential, but we'll quote commercial on a case-by-case basis. Send the property details.")
        ],
        "related_imgs": [
            {"src": "images/interior/_DSC1457.jpg", "alt": "Open-concept living, dining, and kitchen in a Sarasota home"},
            {"src": "images/exterior/_DSC1496.jpg", "alt": "Lakefront covered lanai in a Sarasota luxury home"},
            {"src": "images/interior/_DSC1481.jpg", "alt": "Chef's kitchen with custom range hood, Sarasota"},
            {"src": "images/interior/_DSC1487.jpg", "alt": "Master bedroom with chandelier, Sarasota luxury home"}
        ]
    },
    {
        "slug": "drone-photography",
        "title": "Drone Real Estate Photography in Sarasota | FAA Part 107 | LF Property Media",
        "description": "FAA Part 107 certified drone real estate photography in Sarasota, FL. Aerial shots that show off lot size, waterfront, neighborhood, and outdoor amenities. Included in every package.",
        "keywords": "drone photography Sarasota, real estate drone photographer Sarasota, FAA Part 107 drone Sarasota, aerial real estate photography Florida, drone for real estate Sarasota",
        "h1": "Drone Real Estate Photography",
        "lede": "Aerials that show what an interior photo can't — lot size, waterfront, neighborhood context, golf course adjacency. FAA Part 107 certified, included in every package.",
        "sections": [
            {
                "heading": "Why aerials sell waterfront and golf-course properties",
                "body": """<p>If your listing has a feature that doesn't fit in a window — a pool, a dock, a fairway view, beach proximity, a private drive — the ground photographer can't show it. Drone aerials can. A well-composed top-down or low-altitude angle communicates lot size, landscaping, and neighborhood context in a single frame.</p>
<p style="margin-top:14px;">Every LF Property Media package includes drone aerials. Signature gets 6 shots, Premier gets 10, Platinum gets 16. Add-on aerials are $20 each or $100 for a set of 5.</p>"""
            },
            {
                "heading": "FAA Part 107 certified — what that means for you",
                "body": """<p>Operating drones commercially in the United States requires FAA Part 107 certification. Locke holds this credential, which means we can legally fly for paid real estate shoots, we follow controlled-airspace regulations, and we carry the proper certifications to back it up.</p>
<p style="margin-top:14px;">If your listing is near Sarasota-Bradenton International Airport, Venice Municipal, or other controlled airspace, we file LAANC authorizations in advance so the shoot happens without surprises.</p>"""
            },
            {
                "heading": "Shot list",
                "body": """<ul style="padding-left:24px;line-height:1.8;">
  <li><strong>Top-down roofline</strong> — communicates square footage and lot shape at a glance</li>
  <li><strong>Low-altitude angled facade</strong> — the hero shot, shows the home + landscaping</li>
  <li><strong>Backyard / pool</strong> — outdoor amenities, screened cage, water features</li>
  <li><strong>Neighborhood context</strong> — proximity to Gulf, golf course, downtown, schools</li>
  <li><strong>Waterfront / dock</strong> — for canal homes, boat slips, beachfront</li>
</ul>"""
            }
        ],
        "faq_items": [
            ("Is drone included in every package?", "Yes. Signature includes 6 drone shots, Premier 10, Platinum 16. Extra drone photos are $20 each or $100 for a set of 5."),
            ("Are you FAA Part 107 certified?", "Yes. Locke is FAA Part 107 certified, which is required to operate drones commercially in the U.S."),
            ("What about controlled airspace?", "If the property is near Sarasota-Bradenton or another controlled airport, we file LAANC authorizations in advance. No surprises on shoot day."),
            ("Can you fly in bad weather?", "Drone flights require winds under ~20 mph and clear visibility. If conditions are bad on shoot day, we'll reschedule the aerials at no charge."),
            ("Do you offer drone video?", "Yes — drone video is included in the Premier and Platinum reels. Standalone drone video is available as a $200 add-on.")
        ],
        "related_imgs": [
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-21.jpg", "alt": "Top-down drone aerial of Sarasota luxury home"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-17.jpg", "alt": "Angled drone aerial of lakefront Sarasota home"},
            {"src": "images/aerial/DJI_0980-Enhanced-NR.jpg", "alt": "Gated community entry drone aerial, Sarasota"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of Sarasota waterway and development"}
        ]
    },
    {
        "slug": "twilight-photography",
        "title": "Twilight Real Estate Photography in Sarasota, FL | LF Property Media",
        "description": "Twilight real estate photography in Sarasota — golden hour and blue hour blends with painted Florida skies. Multi-exposure technique. No AI sky replacement. Add-on or standalone.",
        "keywords": "twilight photography Sarasota, twilight real estate photos Florida, golden hour real estate photography, blue hour exterior photos Sarasota",
        "h1": "Twilight Real Estate Photography",
        "lede": "The pink-and-purple Florida sky is the most expensive light a listing can wear — and it's free. We blend multiple exposures so warm interior lights glow and the sky stays painted.",
        "sections": [
            {
                "heading": "What twilight photography actually is",
                "body": """<p>"Twilight" in real estate photography means the 30–60 minute window when the sun is just below the horizon. The sky is still bright enough to show color (pink, orange, purple, blue-violet), but it's dim enough that the home's interior lights start to glow through the windows.</p>
<p style="margin-top:14px;">This is the highest-impact exterior shot you can buy. Twilight photos consistently get the most engagement on listing thumbnails — Zillow, Realtor.com, social — because they feel cinematic instead of clinical.</p>"""
            },
            {
                "heading": "Multi-exposure technique — no AI fakery",
                "body": """<p>A single camera exposure can't capture both a glowing sky and properly-lit windows at the same time. So we shoot brackets — multiple exposures at different settings — and blend them by hand. The result looks natural because it <em>is</em> natural: every pixel comes from your property, your sky, your light.</p>
<p style="margin-top:14px;">No AI sky replacement, no stock skies pasted in. We've all seen the listings where the sky is suspiciously perfect and doesn't match the angle of the light on the house. That's not us.</p>"""
            },
            {
                "heading": "When twilight is worth it",
                "body": """<ul style="padding-left:24px;line-height:1.8;">
  <li><strong>Luxury listings</strong> — over $750k, where every advantage counts</li>
  <li><strong>Architecturally striking homes</strong> — modern, contemporary, Mediterranean</li>
  <li><strong>Strong outdoor lighting</strong> — landscape lights, pool lights, sconces, fire features</li>
  <li><strong>Waterfront properties</strong> — the sky reflects on the water</li>
  <li><strong>Anything with a great pool or outdoor living area</strong></li>
</ul>
<p style="margin-top:14px;">Pricing: twilight is available as an à la carte add-on. We coordinate it with a regular daytime shoot so we can capture both in one visit. Send the address and we'll quote.</p>"""
            }
        ],
        "faq_items": [
            ("How much does a twilight shoot cost?", "Twilight is available as an à la carte add-on, typically bundled with a daytime shoot so we capture everything in one visit. Pricing depends on the home size and shot count — send the property details for a quote."),
            ("Can I get twilight on the Signature package?", "Yes — twilight can be added to any package. We schedule it for the same evening as the daytime shoot so the property is staged once."),
            ("How many twilight shots do I get?", "Typically 4–8 hero exterior twilight shots. We focus on the front facade, key outdoor living areas, and the pool / water feature if applicable."),
            ("Do you use AI sky replacement?", "No. Every twilight photo is a real multi-exposure blend of the actual sky at that property at that time."),
            ("What if the weather is bad?", "We'll reschedule the twilight portion at no charge. Florida skies are usually cooperative but we won't waste your time on a flat grey evening.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC0964-twilight.jpg", "alt": "Sarasota luxury home at twilight with painted pink and purple sky"},
            {"src": "images/exterior/Twilight-1.jpg", "alt": "Single-story Sarasota home at twilight with Florida sunset"}
        ]
    },
    {
        "slug": "3d-tours",
        "title": "3D Virtual Tours & Floor Plans in Sarasota, FL | LF Property Media",
        "description": "Interactive 3D virtual tours and 2D/3D floor plans for Sarasota real estate listings. Dollhouse views, walkthrough navigation. Included in Platinum, 50% off with Premier.",
        "keywords": "3D virtual tour Sarasota, Matterport Sarasota, real estate virtual tour Florida, 3D floor plan Sarasota, dollhouse floor plan real estate",
        "h1": "3D Virtual Tours & Floor Plans",
        "lede": "Interactive walkthroughs that let buyers explore the home from their couch. Combined with 2D and 3D dollhouse floor plans for the full spatial picture.",
        "sections": [
            {
                "heading": "What a 3D virtual tour delivers",
                "body": """<p>A 3D virtual tour is an interactive web view where the buyer clicks through the home as if they were walking it. They control the path. They can stop in any room, look up at the ceiling, look down at the floor, zoom into a detail. The whole house is captured in scan, not in static photos.</p>
<p style="margin-top:14px;">For buyers who haven't seen the home in person — out-of-state buyers, snowbirds, anyone short on time — the 3D tour is often the difference between a showing request and a scroll-past.</p>"""
            },
            {
                "heading": "Included floor plans",
                "body": """<p>Every package includes a 2D floor plan — clean, scaled, labeled. The Platinum package adds a 3D dollhouse view that shows the home as if you removed the roof. Buyers see the full layout, room flow, and proportions at a glance.</p>
<p style="margin-top:14px;">Floor plans are valuable for the same reason the 3D tour is: they answer the question photos can't — <em>how does this house actually flow?</em> Where's the kitchen relative to the master? How far is the garage from the entry?</p>"""
            },
            {
                "heading": "Pricing",
                "body": """<ul style="padding-left:24px;line-height:1.8;">
  <li><strong>2D floor plan</strong> — included in all three packages</li>
  <li><strong>3D dollhouse floor plan</strong> — included in Platinum, $150 add-on to Signature/Premier</li>
  <li><strong>3D virtual tour</strong> — $200 standalone, or $100 (50% off) when added to Premier or Platinum</li>
</ul>"""
            }
        ],
        "faq_items": [
            ("How long does a 3D tour shoot take?", "On top of the regular photo shoot, expect 60–90 extra minutes for the 3D scan depending on home size. We try to schedule both in the same visit."),
            ("Where does the 3D tour live?", "On a hosted link you can drop into your MLS listing, your website, Zillow, or social. The tour runs in any modern browser."),
            ("How long does the link stay active?", "1 year included with every 3D tour. After that, $30/year to keep it hosted, or you can self-host."),
            ("Do I get a Matterport-style dollhouse view?", "Yes — the 3D dollhouse floor plan is part of the tour. Buyers can switch between walkthrough mode and dollhouse mode."),
            ("Can I add a 3D tour after the shoot?", "It would require a second visit. Better to plan it during the original shoot — that's why Premier/Platinum bundle a 50% discount.")
        ],
        "related_imgs": [
            {"src": "images/interior/DSC05344.jpg", "alt": "Open-concept new construction interior in Sarasota — ideal for 3D tour"},
            {"src": "images/interior/_DSC1457.jpg", "alt": "Open-concept Sarasota living and kitchen for virtual tour"}
        ]
    }
]


# ===== DATA: AREA PAGES =====

AREA_PAGES = [
    {
        "slug": "sarasota",
        "area_name": "Sarasota",
        "title": "Sarasota Real Estate Photographer | LF Property Media",
        "description": "Local Sarasota real estate photographer. MLS-ready interior + exterior photos, FAA Part 107 drone aerials, twilight, reels, and 3D tours. 24-hour photo turnaround. Packages from $360.",
        "keywords": "Sarasota real estate photographer, real estate photography Sarasota FL, downtown Sarasota photographer, Sarasota MLS photos, Sarasota drone photographer",
        "h1": "Sarasota Real Estate Photography",
        "lede": "We're based in Sarasota and shoot here every week. Downtown condos, single-family in Indian Beach, new builds in Hidden Lake — if it's listed in Sarasota proper, we've probably photographed something like it.",
        "area_context": """<p>Sarasota is the home market — where we live and where most LF Property Media shoots happen. From downtown condos with bay views to Sarasota School Mid-Century homes in Lido Shores to new construction in Hidden Lake, the variety in this market keeps the work interesting.</p>
<p style="margin-top:14px;">Because we're local, we know the things that don't show up in MLS data: which neighborhoods photograph best in morning light, which intersections have helpful pull-offs for setting up drone shots, which downtown high-rises have the cleanest sightlines from the rooftop. That local knowledge saves real shooting time.</p>""",
        "neighborhoods_blurb": """<p>Most Sarasota proper listings have at least one of three photogenic features: <strong>water</strong> (Sarasota Bay, the Gulf, canals, intracoastal), <strong>architecture</strong> (Sarasota School, mid-century modern, contemporary), or <strong>landscape</strong> (mature oaks, palms, water features). Our job is to make sure those features hit the camera the way they hit the buyer in person.</p>
<p style="margin-top:14px;">Notable Sarasota proper neighborhoods we shoot regularly: Indian Beach, Lido Shores, Lido Key, downtown high-rises (Vue, BLVD, Ritz-Carlton Residences), Arlington Park, Southside Village, Hidden Lake, Granada, Bay Point, and historic neighborhoods like Laurel Park.</p>""",
        "faq_items": [
            ("How quickly can you shoot a Sarasota listing?", "We can usually book within 2–3 business days. Same-week if the schedule allows. Urgent listings — call us directly at (941) 387-5399 and we'll see what we can do."),
            ("Do you photograph downtown high-rises?", "Yes. We've shot in The Vue, BLVD Sarasota, Ritz-Carlton Residences, and similar high-rise condos. Window shots from the upper floors are stunning at twilight."),
            ("What about Sarasota School / mid-century homes?", "Some of our favorite shoots. The clean lines, glass walls, and Gulf light are made for photography. We approach them the way Ezra Stoller would have — straight on, no distortion, real shadows."),
            ("Do you travel out of Sarasota proper?", "Yes — Bradenton, Venice, Osprey, Lakewood Ranch, all the keys. Standard service area. Further out is available with a small travel fee.")
        ],
        "related_imgs": [
            {"src": "images/exterior/DSC03249.jpg", "alt": "Screened pool with fountains in Sarasota home"},
            {"src": "images/exterior/_DSC0964-twilight.jpg", "alt": "Sarasota luxury home at twilight"},
            {"src": "images/interior/_DSC1457.jpg", "alt": "Open-concept Sarasota interior"}
        ]
    },
    {
        "slug": "siesta-key",
        "area_name": "Siesta Key",
        "title": "Siesta Key Real Estate Photographer | LF Property Media",
        "description": "Real estate photography on Siesta Key, FL. Beachfront and canal listings, drone aerials of the Gulf, twilight pool shots. FAA Part 107 certified. 24-hour photo turnaround.",
        "keywords": "Siesta Key real estate photographer, Siesta Key drone photography, Crescent Beach photographer, Siesta Key beachfront photography, Siesta Key MLS photos",
        "h1": "Siesta Key Real Estate Photography",
        "lede": "Crescent Beach, Point of Rocks, the Village, and every canal-front home in between. We know which time of day works best for Gulf-side facades and how to frame the water without losing the home.",
        "area_context": """<p>Siesta Key is the most photogenic ZIP code in Sarasota County, and the trickiest. The Gulf-side homes face west, which means morning shoots have flat front-facade light and evening shoots can blow out the sky. Twilight is almost always the move for west-facing exteriors. Canal-front and inland Siesta homes are more forgiving — we shoot those mornings or late afternoons.</p>""",
        "neighborhoods_blurb": """<p>Siesta Key listings sell on three things: <strong>beach access</strong>, <strong>water views</strong>, and <strong>outdoor living</strong>. Our shot list adapts to whichever you have. Beachfront homes get drone aerials emphasizing the sand and Gulf. Canal homes get dock + waterway shots. Inland homes lean into the pool, the lanai, and the lush landscape.</p>
<p style="margin-top:14px;">We photograph regularly in Crescent Beach, Point of Rocks, Siesta Village area, Beach Road condos, Bay Island, and the canal neighborhoods around Bayview Drive and Higel Avenue.</p>""",
        "faq_items": [
            ("Can you shoot at sunset on the beach?", "Yes — Gulf-side twilight is a signature shot. We coordinate the daytime portion of the shoot in the morning, then return for the twilight exterior 30 minutes before sunset."),
            ("Do you have drone clearance for Siesta Key?", "Siesta Key is outside Sarasota-Bradenton International's controlled airspace, so most of it is clear for Part 107 flight without special authorization. We always check the property's exact location before quoting."),
            ("What about beach-rental / vacation listings?", "Yes. Vacation rentals benefit even more from strong photography — they compete on Vrbo and Airbbnb where the thumbnail is everything. Same packages apply."),
            ("How quickly can you book on Siesta Key?", "Typically 2–3 business days. Twilight shoots need to be coordinated around sunset times, so a bit more lead time is helpful.")
        ],
        "related_imgs": [
            {"src": "images/exterior/DSC03249.jpg", "alt": "Screened pool with fountains, Siesta Key area"},
            {"src": "images/exterior/_DSC0964-twilight.jpg", "alt": "Twilight front facade in Sarasota Florida"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of Sarasota waterway"}
        ]
    },
    {
        "slug": "bird-key",
        "area_name": "Bird Key",
        "title": "Bird Key Real Estate Photographer | LF Property Media",
        "description": "Real estate photography on Bird Key, Sarasota. Waterfront estates, canal homes, twilight exteriors, drone aerials. FAA Part 107 certified. Packages from $360.",
        "keywords": "Bird Key real estate photographer, Bird Key Sarasota drone photography, Bird Key waterfront photography",
        "h1": "Bird Key Real Estate Photography",
        "lede": "A private island, ten minutes from downtown, with deep-water canals on three sides. Bird Key listings live or die on water views and outdoor living — our shot list emphasizes both.",
        "area_context": """<p>Bird Key is small, private, and almost entirely waterfront. Most listings are deep-water canal homes with boat docks, pools, and lush yards. Many are tear-downs being replaced with contemporary builds — the kind of property that benefits from both daytime interiors and twilight exteriors.</p>""",
        "neighborhoods_blurb": """<p>What we focus on for Bird Key: <strong>dock and water</strong> (drone aerial showing the dock + boat + canal frontage), <strong>pool and lanai</strong> (the outdoor living square footage often rivals the indoor), and <strong>architecture</strong> (many properties have been recently rebuilt by notable Sarasota builders). Twilight shoots are especially effective here because the sky reflects on the canal.</p>""",
        "faq_items": [
            ("Do you have drone access for Bird Key?", "Yes. Bird Key is clear for Part 107 flight. We capture top-down water views and angled facade shots that show the lot's water frontage."),
            ("Can you coordinate with the dock / boat for the shoot?", "Yes — if the boat is at the dock, we factor it into the composition. If the slip is empty, we can quietly frame around it."),
            ("Best time of day to shoot Bird Key listings?", "Morning for daytime interiors and east-facing exteriors. Twilight for the hero exterior and water reflection shots."),
            ("Do you handle gated access?", "Yes — Bird Key's guard gate is standard. We coordinate with the listing agent for access ahead of time.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC1505.jpg", "alt": "Lakefront fire pit at a Sarasota luxury home"},
            {"src": "images/exterior/_DSC1496.jpg", "alt": "Lakefront lanai with fireplace"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-17.jpg", "alt": "Angled drone aerial of lakefront luxury home"}
        ]
    },
    {
        "slug": "lakewood-ranch",
        "area_name": "Lakewood Ranch",
        "title": "Lakewood Ranch Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Lakewood Ranch, FL. New construction, country club homes, community amenities. Drone aerials, twilight shoots, 3D tours. 24-hour delivery.",
        "keywords": "Lakewood Ranch real estate photographer, Lakewood Ranch drone photography, Country Club East photography, Lakewood Ranch MLS photos",
        "h1": "Lakewood Ranch Real Estate Photography",
        "lede": "From new construction in Mallory Park to country club estates in The Concession, Lakewood Ranch is a different photography problem than downtown Sarasota — bigger lots, more amenities, more drone work.",
        "area_context": """<p>Lakewood Ranch is master-planned, which means lots of similar floor plans across different villages. The photography has to differentiate — what makes <em>this</em> Mallory Park home different from the one next door? Usually it's the upgrades inside (custom kitchen finishes, primary suite layout) and the outdoor living (pool, summer kitchen, lakefront).</p>
<p style="margin-top:14px;">Drone aerials matter more here than in Sarasota proper because community amenities are a selling point. Buyers want to see the community clubhouse, pool complex, walking trails, and golf course in context.</p>""",
        "neighborhoods_blurb": """<p>Notable Lakewood Ranch villages we shoot regularly: <strong>The Concession</strong>, <strong>Country Club East</strong>, <strong>Country Club</strong>, <strong>Mallory Park</strong>, <strong>Lake Club</strong>, <strong>Esplanade</strong>, <strong>Polo Run</strong>, and <strong>Sapphire Point</strong>. Each has its own architectural style — from luxury custom estates to consistent production builds — and the photography approach adjusts accordingly.</p>""",
        "faq_items": [
            ("Do you photograph Lakewood Ranch new construction?", "Yes — frequently. New builds benefit from staging photos (model homes) or staged hero shots before listing. We work with both individual sellers and builder marketing teams."),
            ("Can you capture the community amenities?", "Yes. For listings where the community is a major selling point (golf course, clubhouse, pool, walking trails), we include drone aerials showing the amenities in context."),
            ("Drone access for Country Club East / The Concession?", "Both are clear for Part 107 flight. We notify the gate and HOA before the shoot when required."),
            ("What's your travel fee for Lakewood Ranch?", "No travel fee — Lakewood Ranch is in our standard service area.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC1542.jpg", "alt": "Modern two-story luxury home in Lakewood Ranch area"},
            {"src": "images/interior/_DSC1448.jpg", "alt": "Coffered-ceiling living room"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-15.jpg", "alt": "Community clubhouse and pool aerial"}
        ]
    },
    {
        "slug": "longboat-key",
        "area_name": "Longboat Key",
        "title": "Longboat Key Real Estate Photographer | LF Property Media",
        "description": "Real estate photography on Longboat Key, FL. Gulf-front condos, beachside estates, bayfront homes. Drone aerials, twilight shoots, FAA Part 107 certified.",
        "keywords": "Longboat Key real estate photographer, Longboat Key drone photography, Gulf-front condo photography, Longboat Key luxury photography",
        "h1": "Longboat Key Real Estate Photography",
        "lede": "Gulf on one side, bay on the other, 12 miles of luxury condos and beachfront homes in between. Longboat photography is mostly about the water — getting it into the frame at the right time of day.",
        "area_context": """<p>Longboat Key listings are dominated by waterfront. Even mid-island properties often have bay or Gulf views from upper floors. Our job is to make sure the water appears bright and saturated, not washed out — which means timing the shoot for the right light and using polarizing filters to cut surface glare.</p>""",
        "neighborhoods_blurb": """<p>Most Longboat photography divides into <strong>Gulf-front high-rises</strong> (Privateer, Beachplace, L'Ambiance, Promenade), <strong>bayfront and canal homes</strong> (mid-key, Longboat Key Club area), and <strong>beachside estates</strong> (especially in the north end). Each requires different shot strategy — high-rises need exterior framing that doesn't include neighboring buildings, beachfront needs drone for context, canal homes need dock + water shots.</p>""",
        "faq_items": [
            ("Drone restrictions on Longboat Key?", "Most of Longboat is clear for Part 107 flight. We always check the property's exact location and notify the appropriate authorities when required."),
            ("Can you shoot Gulf-side at sunset?", "Yes — west-facing Gulf-side exteriors are made for twilight. We aim for the 30 minutes after sunset when the sky still has color and interior lights start to glow."),
            ("Travel fee to Longboat?", "No travel fee — Longboat Key is in our standard service area."),
            ("Best time to shoot Longboat condos?", "Morning for north and east-facing units. Evening / twilight for west-facing Gulf views.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC1496.jpg", "alt": "Lakefront lanai with TV and fireplace, Sarasota luxury home"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide aerial of Sarasota waterway"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-17.jpg", "alt": "Lakefront luxury home aerial"}
        ]
    },
    {
        "slug": "palmer-ranch",
        "area_name": "Palmer Ranch",
        "title": "Palmer Ranch Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Palmer Ranch, Sarasota. Country club estates, golf course homes, gated community amenities. Drone aerials, twilight, 3D tours.",
        "keywords": "Palmer Ranch real estate photographer, Palmer Ranch drone photography, Stoneybrook Golf photography, Prestancia photographer",
        "h1": "Palmer Ranch Real Estate Photography",
        "lede": "Mature trees, golf course frontage, gated community amenities. Palmer Ranch listings benefit from drone aerials almost as much as from interior coverage — buyers want to see the lot and community context.",
        "area_context": """<p>Palmer Ranch is one of the most established master-planned communities in Sarasota County. The lots are bigger, the landscaping is mature, and many homes back to golf course or preserve. Photography here leans heavily on outdoor shots: lanai, pool, golf views, mature oaks.</p>""",
        "neighborhoods_blurb": """<p>Sub-communities we shoot in Palmer Ranch include <strong>Prestancia</strong>, <strong>Stoneybrook Golf & Country Club</strong>, <strong>The Hamptons</strong>, <strong>Deer Creek</strong>, <strong>Wellington Chase</strong>, and <strong>Mira Lago</strong>. Each has its own gate procedures and amenity story — country club homes lean into golf views, Prestancia residences into the wooded estate feel.</p>""",
        "faq_items": [
            ("Do you have access for Palmer Ranch gates?", "Yes — we coordinate with listing agents to get gate access for both vehicle entry and drone flight clearance over private community amenities."),
            ("Can you photograph golf course views?", "Yes. We shoot from the home looking out across the fairway, and we use drone aerials to show the property's position on the hole."),
            ("Travel fee?", "No — Palmer Ranch is in our standard service area."),
            ("Are 3D tours common in Palmer Ranch?", "Yes — the homes are large and the layouts are interesting, which is exactly what 3D tours showcase well. Worth bundling with Platinum for a larger listing.")
        ],
        "related_imgs": [
            {"src": "images/interior/DSC03174.jpg", "alt": "Vaulted-ceiling living room with sliding doors"},
            {"src": "images/exterior/DSC03249.jpg", "alt": "Screened pool with fountains, Sarasota"},
            {"src": "images/aerial/DJI_0976-Enhanced-NR.jpg", "alt": "Golf course clubhouse aerial, Sarasota"}
        ]
    },
    {
        "slug": "venice",
        "area_name": "Venice",
        "title": "Venice FL Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Venice, FL. Beachside homes, golf community listings, island and downtown properties. Drone aerials, twilight, 24-hour photo turnaround.",
        "keywords": "Venice FL real estate photographer, Venice Island photography, Venice drone photographer, Plantation Golf photography",
        "h1": "Venice FL Real Estate Photography",
        "lede": "Venice Island, the mainland golf communities, and beachfront condos — three different listing types, one consistent photography approach. We shoot Venice weekly.",
        "area_context": """<p>Venice has a tighter, older-Florida feel than Sarasota — Venice Island in particular is full of mid-century beach cottages and walkable downtown blocks. Mainland Venice is more varied: golf communities, newer subdivisions, and waterfront homes along the Intracoastal.</p>""",
        "neighborhoods_blurb": """<p>Sub-areas we cover regularly in Venice: <strong>Venice Island</strong> (historic downtown + beach cottages), <strong>Plantation Golf & Country Club</strong>, <strong>The Venice Golf and Country Club</strong>, <strong>Boca Royale</strong>, <strong>Calusa Lakes</strong>, <strong>Sarasota National</strong>, and <strong>IslandWalk</strong> (newer construction).</p>""",
        "faq_items": [
            ("Do you charge a travel fee for Venice?", "No — Venice is in our standard Southwest Florida service area."),
            ("Can you photograph Venice Beach / island listings?", "Yes. Venice Island is one of our favorite locations for twilight shoots — the Gulf-side sunsets are reliably dramatic."),
            ("How about drone over the Venice Municipal Airport area?", "Some Venice properties fall within controlled airspace near the municipal airport. We file LAANC authorizations when needed before the shoot."),
            ("Same 24-hour turnaround?", "Yes — same service standard regardless of where in Southwest Florida the shoot is.")
        ],
        "related_imgs": [
            {"src": "images/exterior/Twilight-1.jpg", "alt": "Single-story home at twilight"},
            {"src": "images/exterior/_DSC1542.jpg", "alt": "Modern two-story luxury home"},
            {"src": "images/interior/_DSC1487.jpg", "alt": "Master bedroom with chandelier"}
        ]
    },
    {
        "slug": "osprey",
        "area_name": "Osprey",
        "title": "Osprey FL Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Osprey, FL. Bayfront homes, Oaks Club estates, golf course listings, drone aerials, twilight. FAA Part 107 certified. Packages from $360.",
        "keywords": "Osprey FL real estate photographer, Oaks Club Osprey photography, Osprey drone photography, Casey Key photographer",
        "h1": "Osprey FL Real Estate Photography",
        "lede": "Between Sarasota and Venice — golf course estates, bayfront homes, Casey Key beachfront. Quieter market than the keys, but no less photogenic.",
        "area_context": """<p>Osprey is one of the more under-the-radar Sarasota County markets — bayfront homes, estate properties around the Oaks Club, and the south end of Casey Key. We shoot here regularly and like the variety.</p>""",
        "neighborhoods_blurb": """<p>Notable Osprey areas we cover: <strong>The Oaks Club</strong> (both Bayside and Clubside), <strong>Casey Key</strong> (south end), <strong>Sorrento Shores</strong>, <strong>Bayside Terrace</strong>, and the bayfront homes along Casey Way and Bayshore Road. Each has its own character — Oaks Club is gated estate, Casey Key is barrier-island beach.</p>""",
        "faq_items": [
            ("Travel fee to Osprey?", "No — Osprey is in our standard service area."),
            ("Can you photograph Casey Key beachfront?", "Yes — Casey Key beachfront is one of the most photogenic places on the Gulf Coast. Twilight shoots there are particularly strong."),
            ("Do you have drone clearance for Oaks Club?", "Yes — we coordinate with the community for any required notifications before drone flight over the gated estate area."),
            ("How quickly can you book in Osprey?", "Typically 2–3 business days, similar to the rest of the service area.")
        ],
        "related_imgs": [
            {"src": "images/exterior/DSC03249.jpg", "alt": "Screened pool with fountains"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of Sarasota waterway"},
            {"src": "images/interior/_DSC1448.jpg", "alt": "Coffered-ceiling living room"}
        ]
    }
]


def main():
    # Service pages
    for s in SERVICE_PAGES:
        path = SERVICES_DIR / f"{s['slug']}.html"
        html_out = service_page(
            slug=s["slug"], title=s["title"], description=s["description"],
            h1=s["h1"], lede=s["lede"], sections=s["sections"],
            faq_items=s["faq_items"], related_imgs=s["related_imgs"],
            keywords=s["keywords"]
        )
        path.write_text(html_out, encoding="utf-8")
        print(f"Wrote {path}")

    # Area pages
    for a in AREA_PAGES:
        path = AREAS_DIR / f"{a['slug']}.html"
        html_out = area_page(
            slug=a["slug"], area_name=a["area_name"], title=a["title"],
            description=a["description"], h1=a["h1"], lede=a["lede"],
            area_context=a["area_context"],
            neighborhoods_blurb=a["neighborhoods_blurb"],
            faq_items=a["faq_items"], related_imgs=a["related_imgs"],
            keywords=a["keywords"]
        )
        path.write_text(html_out, encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
