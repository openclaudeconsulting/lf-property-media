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
          <li><a href="{rel_root}areas/nokomis.html">Nokomis</a></li>
          <li><a href="{rel_root}areas/venice.html">Venice</a></li>
          <li><a href="{rel_root}areas/osprey.html">Osprey</a></li>
          <li><a href="{rel_root}areas/siesta-key.html">Siesta Key</a></li>
          <li><a href="{rel_root}areas/bird-key.html">Bird Key</a></li>
          <li><a href="{rel_root}areas/longboat-key.html">Longboat Key</a></li>
          <li><a href="{rel_root}areas/lakewood-ranch.html">Lakewood Ranch</a></li>
          <li><a href="{rel_root}areas/palmer-ranch.html">Palmer Ranch</a></li>
          <li><a href="{rel_root}areas/bradenton.html">Bradenton</a></li>
          <li><a href="{rel_root}areas/palmetto.html">Palmetto</a></li>
          <li><a href="{rel_root}areas/parrish.html">Parrish</a></li>
          <li><a href="{rel_root}areas/anna-maria-island.html">Anna Maria Island</a></li>
          <li><a href="{rel_root}areas/tampa.html">Tampa</a></li>
          <li><a href="{rel_root}areas/st-petersburg.html">St. Petersburg</a></li>
          <li><a href="{rel_root}areas/clearwater.html">Clearwater</a></li>
          <li><a href="{rel_root}areas/north-port.html">North Port</a></li>
          <li><a href="{rel_root}areas/port-charlotte.html">Port Charlotte</a></li>
          <li><a href="{rel_root}areas/fort-myers.html">Fort Myers</a></li>
          <li><a href="{rel_root}areas/cape-coral.html">Cape Coral</a></li>
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
        "slug": "nokomis",
        "area_name": "Nokomis",
        "title": "Nokomis FL Real Estate Photographer | LF Property Media — Home Base",
        "description": "Real estate photography in Nokomis, FL — LF Property Media's home base. North Casey Key, Nokomis Beach, Mission Valley, Calusa Lakes. Drone aerials, twilight, 24-hour delivery.",
        "keywords": "Nokomis real estate photographer, Nokomis FL photography, Casey Key real estate photographer, Nokomis Beach photography",
        "h1": "Nokomis FL Real Estate Photography",
        "lede": "This is home base. North Casey Key, Nokomis Beach, Mission Valley, Calusa Lakes — we know every back road. If you're listing in Nokomis, we can usually shoot it on a day's notice.",
        "area_context": """<p>Nokomis is where Locke lives, which means we shoot here more than any other ZIP code outside Sarasota proper. The market is mixed — older Florida-style homes inland, waterfront on North Casey Key and the canals around Mission Valley, gated golf communities like Calusa Lakes. Each requires a different photography approach, and we know all three from regular work.</p>""",
        "neighborhoods_blurb": """<p>Notable Nokomis areas we shoot regularly: <strong>North Casey Key</strong> (barrier-island Gulf-front), <strong>Nokomis Beach</strong>, <strong>Mission Valley Estates</strong>, <strong>Calusa Lakes</strong>, <strong>Sorrento East</strong>, and <strong>The Inlets at Nokomis</strong>. Older established neighborhoods often have mature oaks that we light around carefully — fresh new construction in Esplanade and the Toscana Isles area is more straightforward.</p>""",
        "faq_items": [
            ("Travel fee for Nokomis?", "Zero — Nokomis is the home base. We can usually shoot here on a day's notice if the schedule allows."),
            ("Can you photograph Casey Key Gulf-front?", "Yes — North Casey Key in particular is one of our favorite places to shoot. Twilight Gulf-side is essentially a signature service."),
            ("How about Calusa Lakes golf homes?", "Yes — we photograph the golf-frontage homes regularly. Drone aerials showing the lot's position relative to the fairway are a big selling point."),
            ("Same 24-hour photo turnaround?", "Yes — every market, same standard.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC0964-twilight.jpg", "alt": "Twilight luxury home — Sarasota County, Florida"},
            {"src": "images/interior/_DSC1457.jpg", "alt": "Open-concept living and kitchen, Sarasota County"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-21.jpg", "alt": "Top-down aerial of single-family home, Sarasota County"}
        ]
    },
    {
        "slug": "bradenton",
        "area_name": "Bradenton",
        "title": "Bradenton Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Bradenton, FL. Manatee County listings, downtown Riverwalk, Cortez waterfront, gateway to Anna Maria Island. Drone, twilight, 24-hour delivery.",
        "keywords": "Bradenton real estate photographer, Bradenton FL photography, Manatee County real estate photographer, Cortez waterfront photography, Bradenton MLS photos",
        "h1": "Bradenton Real Estate Photography",
        "lede": "Manatee County's hub — Downtown Bradenton, the Riverwalk, Cortez fishing village, plus the gateway to Anna Maria Island. More variety than people realize, all within 40 minutes of our Nokomis base.",
        "area_context": """<p>Bradenton is bigger and more layered than its quiet reputation suggests. The historic downtown around Old Main Street has seen serious investment — new mid-rise condos along the Manatee River, restored craftsman homes in the historic district. Cortez to the west is one of Florida's last working fishing villages, with waterfront character that genuinely can't be replicated. And inland, the master-planned communities of Lakewood Ranch (technically half in Bradenton) keep pushing east.</p>""",
        "neighborhoods_blurb": """<p>Sub-areas we shoot regularly in Bradenton: <strong>Downtown / Riverwalk</strong>, <strong>Cortez</strong>, <strong>Palma Sola</strong>, <strong>Bayshore Gardens</strong>, <strong>Tara Country Club</strong>, <strong>River Wilderness</strong>, and the <strong>Manatee River waterfront</strong>. For listings west of US-41, mornings are usually the best light. East of the city, the new construction reads cleaner at midday.</p>""",
        "faq_items": [
            ("Travel fee for Bradenton?", "No — Bradenton is in our standard service area."),
            ("Can you photograph Cortez waterfront properties?", "Yes. Cortez has unique character — working docks, weathered buildings, the fishing-village feel. We approach it differently than the more polished Sarasota waterfront work."),
            ("Drone over downtown Bradenton?", "Most of downtown Bradenton is clear for Part 107 flight, though we always check for events and TFRs. We file LAANC when required."),
            ("Same-day or rush availability in Bradenton?", "Usually yes — we're 40 minutes south. Call us directly at (941) 387-5399 for rush bookings.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC1542.jpg", "alt": "Modern two-story luxury home in Bradenton area"},
            {"src": "images/exterior/_DSC1496.jpg", "alt": "Lakefront lanai with fireplace, Bradenton area"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of Manatee waterway"}
        ]
    },
    {
        "slug": "palmetto",
        "area_name": "Palmetto",
        "title": "Palmetto FL Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Palmetto, FL — waterfront homes on the Manatee River, Snead Island canals, Terra Ceia. FAA Part 107 drone, twilight, 24-hour delivery.",
        "keywords": "Palmetto FL real estate photographer, Snead Island photography, Terra Ceia photographer, Palmetto waterfront photography, Manatee River real estate",
        "h1": "Palmetto FL Real Estate Photography",
        "lede": "A quieter alternative to Bradenton, just across the Manatee River. Snead Island canals, Terra Ceia, downtown Palmetto historic homes — under-photographed waterfront we shoot regularly.",
        "area_context": """<p>Palmetto is small — only about 13,000 people — but it's perched on some of the best waterfront in the area. The Manatee River frontage is mature, with established homes and old-Florida character. Snead Island is a hidden canal community at the river's mouth. Terra Ceia to the north has a salt-flat island feel that's nearly impossible to find this close to Tampa Bay.</p>""",
        "neighborhoods_blurb": """<p>Notable Palmetto areas: <strong>Snead Island</strong> (deep-water canal homes), <strong>Terra Ceia</strong> (waterfront Florida-keys feel), <strong>downtown Palmetto historic district</strong>, <strong>Bayshore Gardens</strong> (technically just south of the line), and <strong>Riviera Dunes</strong> (boating community). The Skyway Bridge view is a frequent drone composition for listings along the north Palmetto waterfront.</p>""",
        "faq_items": [
            ("Travel fee for Palmetto?", "No — Palmetto is about 50 minutes from our home base and within standard service area."),
            ("Can you do twilight shoots on the Manatee River?", "Yes — the west-facing river makes Palmetto twilight shoots particularly strong. Sky reflects in the water."),
            ("Drone in Palmetto?", "Most of Palmetto is clear for Part 107 flight. The Sunshine Skyway and Tampa Bay airspace require some attention — we check before quoting."),
            ("Do you photograph Snead Island homes regularly?", "Yes — Snead Island is small but the listings benefit hugely from drone aerials showing the deep-water canal access.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC1505.jpg", "alt": "Lakefront fire pit at a waterfront home"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-17.jpg", "alt": "Angled drone aerial of waterfront home, Manatee County"},
            {"src": "images/exterior/_DSC1496.jpg", "alt": "Waterfront lanai with lake view"}
        ]
    },
    {
        "slug": "parrish",
        "area_name": "Parrish",
        "title": "Parrish FL Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Parrish, FL — North River Ranch, Crosscreek, Foxbrook. New construction in Manatee County's fastest-growing area. Drone, twilight, 24-hour delivery.",
        "keywords": "Parrish FL real estate photographer, North River Ranch photography, Crosscreek photographer, new construction photography Parrish, Parrish drone photography",
        "h1": "Parrish FL Real Estate Photography",
        "lede": "One of Florida's fastest-growing ZIP codes. North River Ranch, Crosscreek, Foxbrook — new construction means new listings competing for the same buyer's eye. Photography is non-negotiable.",
        "area_context": """<p>Parrish is the suburban growth story of Manatee County. Master-planned communities are going up on what were citrus groves a decade ago. The challenge for any listing here is differentiation — when the floor plan and finishes are similar to the model next door, the photography has to do the work of showing what's different. Upgrades, landscaping, view, light.</p>""",
        "neighborhoods_blurb": """<p>Active Parrish communities we shoot in: <strong>North River Ranch</strong>, <strong>Crosscreek</strong>, <strong>Foxbrook</strong>, <strong>River Wilderness</strong>, <strong>Forest Creek</strong>, <strong>Twin Rivers</strong>, and <strong>Silverleaf</strong>. Each builder favors a slightly different aesthetic — Lennar's color palettes differ from MI Homes' or Mattamy's — and the photography adapts.</p>""",
        "faq_items": [
            ("Travel fee for Parrish?", "No — Parrish is roughly 50 minutes from our base, inside standard service area."),
            ("Do you work with builders for model home photography?", "Yes — we photograph builder model homes regularly. Different deliverables than a typical MLS shoot (more lifestyle staging, brand-consistent edits), priced per-project."),
            ("Drone in Parrish?", "Most of Parrish is clear for Part 107 flight — open development means few obstacles. We notify the HOA when required."),
            ("How quickly can you shoot a Parrish listing?", "Usually 2–3 business days. With new construction volume here, we keep a buffer for builder clients.")
        ],
        "related_imgs": [
            {"src": "images/interior/DSC05344.jpg", "alt": "Open-concept new construction interior — Parrish area"},
            {"src": "images/exterior/DSC05428.jpg", "alt": "Modern new construction exterior, Manatee County"},
            {"src": "images/exterior/_DSC1542.jpg", "alt": "Two-story luxury home, Manatee County"}
        ]
    },
    {
        "slug": "anna-maria-island",
        "area_name": "Anna Maria Island",
        "title": "Anna Maria Island Real Estate Photographer | LF Property Media",
        "description": "Real estate photography on Anna Maria Island, FL — Anna Maria, Holmes Beach, Bradenton Beach. Vacation rentals, beach cottages, drone aerials of the Gulf. FAA Part 107 certified.",
        "keywords": "Anna Maria Island real estate photographer, Holmes Beach photography, Bradenton Beach photographer, Anna Maria vacation rental photography, AMI drone photography",
        "h1": "Anna Maria Island Real Estate Photography",
        "lede": "Three cities, one barrier island, all photogenic in completely different ways. AMI is to Bradenton what Siesta Key is to Sarasota — and the vacation-rental market makes the thumbnail the entire selling tool.",
        "area_context": """<p>Anna Maria Island is seven miles of barrier island west of Bradenton, divided among three small cities: Anna Maria on the north end, Holmes Beach in the middle, Bradenton Beach to the south. The architecture is intentionally low-rise — strict height regulations preserve the old-Florida feel. Vacation rentals dominate the market, which means listings compete on Vrbo and Airbnb where the lead photo decides everything.</p>""",
        "neighborhoods_blurb": """<p>Photography strategy varies by city: <strong>Anna Maria</strong> (north end) has the quieter beach cottages, often near Pine Avenue's restaurants. <strong>Holmes Beach</strong> has the largest mix — Gulf-front, canal-front, and inland. <strong>Bradenton Beach</strong> (south end) is condo-heavy with pier and historic-district character. Gulf-side twilight is essentially a signature service for all three cities — the west-facing exposure was made for it.</p>""",
        "faq_items": [
            ("Travel fee for Anna Maria Island?", "No — AMI is inside standard service area, about 60 minutes from our base."),
            ("Do you photograph vacation rentals specifically?", "Yes — frequently. Vacation rentals need different shot strategies than MLS listings (more lifestyle, more bedrooms-occupied, more sunset). We price the same."),
            ("Drone over AMI beaches?", "Most of AMI is clear for Part 107 flight. We always check for active TFRs and notify the city when required for over-beach flight."),
            ("Best time of year to shoot AMI?", "October through May is ideal — clear skies, calmer Gulf, less seaweed on the beach. We can shoot year-round but coastal storms are common June–September.")
        ],
        "related_imgs": [
            {"src": "images/exterior/Twilight-1.jpg", "alt": "Single-story Florida home at twilight"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of Florida waterway"},
            {"src": "images/exterior/_DSC1496.jpg", "alt": "Covered patio with TV and fireplace, Gulf coast Florida"}
        ]
    },
    {
        "slug": "tampa",
        "area_name": "Tampa",
        "title": "Tampa Real Estate Photographer | LF Property Media — Drive Up From Sarasota",
        "description": "Real estate photography in Tampa, FL by LF Property Media. South Tampa, Davis Islands, Hyde Park, Westshore, downtown. Drone, twilight, 24-hour delivery. We drive up from Sarasota.",
        "keywords": "Tampa real estate photographer, South Tampa photography, Davis Islands real estate photographer, Hyde Park Tampa photography, Tampa drone photography",
        "h1": "Tampa Real Estate Photography",
        "lede": "We drive up from Sarasota. South Tampa bungalows, Davis Islands waterfront, Hyde Park craftsman, downtown high-rises — Tampa real estate photography that doesn't compromise on the things that make Sarasota work.",
        "area_context": """<p>Tampa is about 75 minutes north of our Nokomis base. We travel up regularly for downtown high-rise listings, South Tampa waterfront, and the historic neighborhoods like Hyde Park and Seminole Heights. It's a bigger, more competitive market — which is exactly why strong photography matters more, not less.</p>""",
        "neighborhoods_blurb": """<p>Tampa neighborhoods we shoot regularly: <strong>South Tampa</strong> (Bayshore Boulevard, Beach Park, Sunset Park, Culbreath Isles), <strong>Davis Islands</strong>, <strong>Hyde Park</strong> (north and south), <strong>Westshore / Westchase</strong>, <strong>Downtown / Channelside high-rises</strong>, <strong>Seminole Heights</strong>, <strong>Carrollwood</strong>, and <strong>New Tampa</strong>. Each has its own architectural lineage — bungalows, modern, mid-century, contemporary new construction — and we adapt the shot list.</p>""",
        "faq_items": [
            ("Do you charge a travel fee for Tampa?", "Yes — modest travel fee for Tampa shoots to cover the 75-minute drive each way. Quoted up front when you send the property details."),
            ("Drone restrictions near Tampa International?", "Significant portions of Tampa fall inside TPA controlled airspace. We file LAANC authorizations in advance for every shoot that needs them — no surprises on shoot day."),
            ("Can you handle high-rise downtown condos?", "Yes — we shoot in downtown high-rises regularly. Window-light balancing is the key technique for upper-floor units, and that's what we do."),
            ("Same 24-hour photo turnaround for Tampa?", "Yes — same standard regardless of distance. We deliver photos in 24 hours from every shoot.")
        ],
        "related_imgs": [
            {"src": "images/interior/_DSC1448.jpg", "alt": "Coffered-ceiling living room — Tampa Bay luxury home"},
            {"src": "images/interior/_DSC1481.jpg", "alt": "Chef's kitchen with custom hood, Tampa Bay area"},
            {"src": "images/exterior/_DSC1542.jpg", "alt": "Modern luxury home facade, Tampa Bay"}
        ]
    },
    {
        "slug": "st-petersburg",
        "area_name": "St. Petersburg",
        "title": "St. Petersburg FL Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in St. Petersburg, FL — downtown high-rises, Snell Isle, Old Northeast, beach communities. FAA Part 107 drone, twilight, 24-hour delivery.",
        "keywords": "St. Petersburg real estate photographer, St Pete photography, Snell Isle photographer, Old Northeast St Pete photography, downtown St Pete real estate photographer",
        "h1": "St. Petersburg Real Estate Photography",
        "lede": "A 90-minute drive from Sarasota and worth every mile. Downtown St. Pete's growth has transformed the listings market — and the buyers reaching for them expect photography to match the architecture.",
        "area_context": """<p>St. Petersburg has gone through one of the most dramatic real estate transformations of any Florida city in the past decade. Downtown high-rises with bay views, historic neighborhoods like Old Northeast getting bid up beyond projections, beach communities on the barrier islands holding their own. Photography here has to keep up with what's actually being sold — both the architecture and the lifestyle.</p>""",
        "neighborhoods_blurb": """<p>St. Pete sub-areas we shoot regularly: <strong>Downtown</strong> (high-rises with bay views, Beach Drive corridor), <strong>Snell Isle</strong> (waterfront estates), <strong>Old Northeast</strong> (historic craftsman and Mediterranean), <strong>Coffee Pot Bayou</strong>, <strong>Allendale</strong>, <strong>Crescent Lake</strong>, plus the barrier-island beach communities: <strong>Pass-a-Grille</strong>, <strong>St. Pete Beach</strong>, <strong>Treasure Island</strong>, and <strong>Madeira Beach</strong>.</p>""",
        "faq_items": [
            ("Travel fee for St. Pete?", "Yes — modest travel fee. Quoted up front when you send the property details."),
            ("Drone in downtown St. Pete?", "Downtown St. Pete falls inside Albert Whitted Airport's controlled airspace. We file LAANC for every flight that requires it."),
            ("Can you shoot Old Northeast historic homes?", "Yes — this is some of our favorite work. The Mediterranean and craftsman architecture rewards careful exterior framing and warm interior light."),
            ("Same turnaround as Sarasota?", "Yes — 24-hour photo delivery from every shoot.")
        ],
        "related_imgs": [
            {"src": "images/interior/_DSC1448.jpg", "alt": "Coffered-ceiling living room with chandelier — St. Petersburg luxury home"},
            {"src": "images/exterior/_DSC1542.jpg", "alt": "Modern luxury home facade in Tampa Bay area"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of Tampa Bay waterway"}
        ]
    },
    {
        "slug": "clearwater",
        "area_name": "Clearwater",
        "title": "Clearwater Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Clearwater, FL — Clearwater Beach, Belleair, Sand Key, Island Estates. Waterfront condos, beachfront estates, drone aerials, twilight shoots.",
        "keywords": "Clearwater real estate photographer, Clearwater Beach photography, Belleair photographer, Sand Key photography, Clearwater drone photography",
        "h1": "Clearwater Real Estate Photography",
        "lede": "Clearwater Beach is rated America's #1 beach most years for a reason — and the photography has to do that justice. We travel up for Belleair, Sand Key, and the waterfront condos along the Intracoastal.",
        "area_context": """<p>Clearwater's coastline is the draw — Clearwater Beach's white sand, the barrier-island condo corridor, the bayfront and Intracoastal homes on the mainland side. Inland Clearwater is more mixed (Countryside, Belleair), but the listings that move on photography are almost always water-adjacent in some way.</p>""",
        "neighborhoods_blurb": """<p>Clearwater sub-areas we shoot in: <strong>Clearwater Beach</strong>, <strong>Sand Key</strong>, <strong>Island Estates</strong>, <strong>Belleair</strong> (and Belleair Bluffs), <strong>Harbor Oaks</strong>, <strong>Countryside</strong>, and the downtown waterfront. Belleair in particular has some of the most established old-Florida estate properties on the Gulf coast.</p>""",
        "faq_items": [
            ("Travel fee for Clearwater?", "Yes — modest travel fee. Quoted up front."),
            ("Drone over Clearwater Beach?", "Most of Clearwater Beach is clear for Part 107 flight outside of TFRs (which we always check). The beach itself has occasional event-related restrictions."),
            ("Best time to shoot Gulf-side?", "Twilight, every time, for west-facing Gulf exteriors. We coordinate around sunset."),
            ("Do you photograph Sand Key condos?", "Yes — high-rise condo work is something we do regularly. Window-light balancing for upper-floor units is the key technique.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC0964-twilight.jpg", "alt": "Twilight luxury home with painted Florida sky"},
            {"src": "images/exterior/_DSC1496.jpg", "alt": "Waterfront lanai with TV and fireplace"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-17.jpg", "alt": "Angled drone aerial of waterfront luxury home"}
        ]
    },
    {
        "slug": "north-port",
        "area_name": "North Port",
        "title": "North Port FL Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in North Port, FL — Sarasota County's fast-growing south end. New construction listings, golf communities, Heron Creek, Talon Bay. Drone, twilight, 24-hour delivery.",
        "keywords": "North Port real estate photographer, North Port FL photography, Heron Creek photographer, Talon Bay photography, North Port new construction photographer",
        "h1": "North Port FL Real Estate Photography",
        "lede": "Sarasota County's fastest-growing city. Heron Creek, Talon Bay, Bobcat Trail — newer construction listings that benefit from confident, MLS-ready photography.",
        "area_context": """<p>North Port has been a growth story for two decades, and the pace has only accelerated. It's the largest city in Sarasota County by area. The market is heavily new-construction, which means listings benefit hugely from photography that differentiates — same floor plan, same finishes, but better light and better composition wins.</p>""",
        "neighborhoods_blurb": """<p>Notable North Port communities: <strong>Heron Creek Golf & Country Club</strong>, <strong>Talon Bay</strong>, <strong>Bobcat Trail</strong>, <strong>Lakeside Plantation</strong>, <strong>The Cove at West Port</strong>, <strong>Cedar Grove</strong>, and the older sections along Sumter Boulevard. Lots of golf-frontage homes, which makes drone aerials a high-value add-on.</p>""",
        "faq_items": [
            ("Travel fee for North Port?", "No — North Port is in our standard service area, about 30 minutes south."),
            ("Do you photograph builder model homes?", "Yes — we work with builders regularly. Different deliverables than a standard MLS shoot (more lifestyle staging, brand-consistent edits)."),
            ("Drone over golf course communities?", "Yes — we capture the home's relationship to the fairway, which is often a major selling point."),
            ("Same turnaround as Sarasota proper?", "Yes — 24-hour photo delivery, every shoot.")
        ],
        "related_imgs": [
            {"src": "images/interior/DSC05344.jpg", "alt": "Open-concept new construction interior — North Port area"},
            {"src": "images/exterior/DSC05428.jpg", "alt": "Modern new construction exterior, Sarasota County"},
            {"src": "images/aerial/DJI_0976-Enhanced-NR.jpg", "alt": "Golf course clubhouse aerial — Sarasota County"}
        ]
    },
    {
        "slug": "port-charlotte",
        "area_name": "Port Charlotte",
        "title": "Port Charlotte FL Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Port Charlotte, FL — Gulf-access canal homes, Charlotte Harbor waterfront, drone aerials. FAA Part 107 certified. 24-hour photo delivery.",
        "keywords": "Port Charlotte real estate photographer, Port Charlotte FL photography, Charlotte Harbor real estate photographer, Gulf-access canal homes photography",
        "h1": "Port Charlotte FL Real Estate Photography",
        "lede": "Charlotte Harbor canal homes with direct Gulf access are some of the best photographs we shoot. Port Charlotte has more waterfront mileage per dollar than almost anywhere else in Southwest Florida.",
        "area_context": """<p>Port Charlotte's defining feature is the canal system — miles of saltwater canals running off Charlotte Harbor, most with Gulf access. That's the selling point for a huge percentage of listings here, and capturing it well takes drone aerials. Inland Port Charlotte has its own character (older Florida ranch homes, mature landscaping), but the waterfront is the headline.</p>""",
        "neighborhoods_blurb": """<p>Port Charlotte sub-areas we shoot regularly: <strong>Waterfront canal communities</strong> (most of the city's south and west), <strong>Deep Creek</strong>, <strong>Section 15</strong>, <strong>The Cape</strong>, plus nearby <strong>Charlotte Park</strong>. Direct-Gulf-access listings get full drone treatment showing the canal-to-harbor route.</p>""",
        "faq_items": [
            ("Travel fee for Port Charlotte?", "Modest travel fee — about 50 minutes south. Quoted up front."),
            ("Are drone aerials especially important here?", "Yes — for canal-front and waterfront listings, the aerial showing Gulf access can be the single most important photo in the listing."),
            ("Best time for waterfront shoots?", "Morning for east-facing canals (sun reflecting on water), evening twilight for west-facing exposures and Gulf-side shots."),
            ("Same 24-hour turnaround?", "Yes — same standard regardless of distance.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC1505.jpg", "alt": "Lakefront patio with fire pit, Southwest Florida"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of waterway"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-17.jpg", "alt": "Angled drone aerial of waterfront luxury home"}
        ]
    },
    {
        "slug": "fort-myers",
        "area_name": "Fort Myers",
        "title": "Fort Myers Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Fort Myers, FL — McGregor Boulevard estates, downtown river district, Gulf-access homes. Drone, twilight, 24-hour photo delivery.",
        "keywords": "Fort Myers real estate photographer, McGregor Boulevard photography, Fort Myers downtown photographer, Fort Myers drone photography",
        "h1": "Fort Myers Real Estate Photography",
        "lede": "90 minutes south of Sarasota. We drive down for McGregor Boulevard estates, downtown river-district condos, and Gulf-access waterfront. Different city, same standards.",
        "area_context": """<p>Fort Myers has its own real-estate personality — different from the keys, different from Sarasota. McGregor Boulevard's royal palm-lined corridor is iconic. Downtown's River District has seen serious revival with high-rise condos and renovated historic blocks. East of the city, gated golf communities like Verandah and Cypress Cove keep expanding. We travel down regularly for the variety.</p>""",
        "neighborhoods_blurb": """<p>Fort Myers sub-areas we shoot in: <strong>McGregor Boulevard / Edison Park / Seminole Park</strong> (historic estates), <strong>Downtown / River District</strong>, <strong>Whiskey Creek</strong>, <strong>Iona</strong>, <strong>Sanibel-adjacent</strong> mainland communities, <strong>Cape Coral border areas</strong>, and gated communities like <strong>Verandah</strong>, <strong>Cypress Cove</strong>, and <strong>Pelican Preserve</strong>.</p>""",
        "faq_items": [
            ("Travel fee for Fort Myers?", "Yes — modest travel fee for the 90-minute drive each way. Quoted up front."),
            ("Can you photograph Sanibel-adjacent properties?", "Yes — mainland Fort Myers and the causeway-area listings, definitely. Sanibel proper has restrictions we work through case-by-case."),
            ("Drone over McGregor Boulevard?", "Yes — we file LAANC when required near Page Field airport. Royal palms make for some of the most distinctive aerials in Southwest Florida."),
            ("Same turnaround as closer markets?", "Yes — 24-hour photo delivery from every shoot.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC0964-twilight.jpg", "alt": "Twilight luxury home with painted Florida sky"},
            {"src": "images/interior/_DSC1448.jpg", "alt": "Coffered-ceiling living room — luxury home"},
            {"src": "images/exterior/_DSC1542.jpg", "alt": "Modern two-story luxury home facade"}
        ]
    },
    {
        "slug": "cape-coral",
        "area_name": "Cape Coral",
        "title": "Cape Coral Real Estate Photographer | LF Property Media",
        "description": "Real estate photography in Cape Coral, FL — Gulf-access canal homes, waterfront listings, drone aerials. 400+ miles of canals. FAA Part 107 certified. 24-hour photo delivery.",
        "keywords": "Cape Coral real estate photographer, Cape Coral FL photography, Cape Coral canal homes, Cape Coral drone photographer, Gulf access photography Cape Coral",
        "h1": "Cape Coral Real Estate Photography",
        "lede": "400 miles of canals — more than any city in the world. Cape Coral listings are won and lost on the waterfront shot. We've shot enough of them to know exactly how to frame it.",
        "area_context": """<p>Cape Coral's canal system is the defining feature of essentially every listing here. Direct-Gulf-access homes, freshwater-canal homes, off-water inland — the distinction matters hugely to buyers, and the photography has to communicate it. Drone aerials aren't optional; they're the most important shot in the listing.</p>""",
        "neighborhoods_blurb": """<p>Cape Coral neighborhoods we shoot in: <strong>SW Cape Coral</strong> (gulf-access concentration), <strong>SE Cape Coral</strong> (mix of Gulf and freshwater canals), <strong>NW Cape Coral</strong> (newer construction, more freshwater), <strong>Tarpon Point</strong>, <strong>Cape Harbour</strong>, and the canals around <strong>El Dorado</strong> and <strong>Pelican</strong>. We always confirm whether the property is Gulf-access before quoting — the shot list depends on it.</p>""",
        "faq_items": [
            ("Travel fee for Cape Coral?", "Yes — modest travel fee for the drive. Quoted up front when you send the property details."),
            ("Are drone aerials critical for Cape Coral listings?", "Yes — more than almost any other market we serve. Buyers want to see the canal, the seawall, the boat lift if applicable, and the route to open water."),
            ("Can you photograph the boat lift / dock setup?", "Yes — we treat the dock and lift as a feature, not an afterthought. Drone + ground-level shots together tell the full waterfront story."),
            ("Same 24-hour turnaround?", "Yes — same standard, regardless of distance.")
        ],
        "related_imgs": [
            {"src": "images/exterior/_DSC1505.jpg", "alt": "Lakefront patio with fire pit at waterfront home"},
            {"src": "images/aerial/Bert-Smith-Subaru-Drone-17.jpg", "alt": "Angled drone aerial of waterfront home with canal access"},
            {"src": "images/aerial/DJI_0030.jpg", "alt": "Wide drone aerial of canal community"}
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


def areas_hub_page():
    """Index page at /areas/index.html — lists all 20 area pages with cards."""
    canonical = f"{SITE_URL}/areas/"
    rel = "../"
    schema = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "Service Areas — LF Property Media",
  "url": "https://lfpropertymedia.org/areas/",
  "description": "All cities and neighborhoods served by LF Property Media for real estate photography in Sarasota, Tampa Bay, and Southwest Florida."
}
</script>"""

    cards = ""
    for a in AREA_PAGES:
        cards += f"""        <a class="alacarte-item reveal" href="{a['slug']}.html" style="text-decoration:none;">
          <h4>{html.escape(a['area_name'])}</h4>
          <p>{html.escape(a['lede'])}</p>
        </a>
"""

    return (
        shared_head(
            "Service Areas | Sarasota, Tampa Bay & Southwest Florida | LF Property Media",
            "All cities and neighborhoods served by LF Property Media: Sarasota, Tampa, St. Petersburg, Clearwater, Bradenton, Palmetto, Parrish, Anna Maria Island, Lakewood Ranch, Siesta Key, Longboat Key, Venice, Fort Myers, Cape Coral, and more.",
            canonical, rel_root=rel,
            extra_keywords="real estate photographer service areas, Sarasota photographer coverage, Tampa Bay real estate photography, Southwest Florida photographer",
            extra_schema=schema
        )
        + shared_header(rel)
        + f"""
<section class="hero" style="padding:100px 0 60px;">
  <div class="container">
    <div class="section-head" style="margin-bottom:0;">
      <span class="kicker">Service Areas</span>
      <h1 style="font-size:clamp(2.4rem,5vw,3.6rem);">Sarasota, Tampa Bay & all of Southwest Florida.</h1>
      <p class="lede-large" style="margin:24px auto 0;max-width:760px;">Locke is based in Nokomis, FL — between Sarasota and Venice — and travels up to 90 minutes in any direction for shoots. That's an enormous service footprint, from Cape Coral in the south to Clearwater in the north.</p>
      <div class="btn-row" style="justify-content:center;margin-top:32px;">
        <a href="{rel}contact.html" class="btn btn-primary">Get a Quote</a>
        <a href="{rel}packages.html" class="btn btn-secondary">View Packages</a>
      </div>
    </div>
  </div>
</section>

<section class="bg-cream">
  <div class="container">
    <div class="section-head reveal"><span class="kicker">Browse</span><h2>Every city we shoot in</h2><span class="divider"></span></div>
    <div class="alacarte-grid">
{cards}    </div>
  </div>
</section>

<section class="cta-banner">
  <div class="container">
    <h2>Outside this list?</h2>
    <p>If your property is within 90 minutes of Nokomis, we'll travel. Send the address and we'll quote.</p>
    <a href="{rel}contact.html" class="btn btn-light">Send a Property</a>
  </div>
</section>
"""
        + shared_footer(rel)
    )


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

    # Areas hub page
    hub_path = AREAS_DIR / "index.html"
    hub_path.write_text(areas_hub_page(), encoding="utf-8")
    print(f"Wrote {hub_path}")


if __name__ == "__main__":
    main()
