"""
Build the Journal (blog) for LF Property Media.

Source:  content/blog/*.md   (Markdown with a small YAML-style front matter block)
Output:  blog/index.html     (journal index)
         blog/<slug>.html    (one page per post)
         sitemap.xml         (the <!-- journal --> block is rewritten)

Run after adding or editing a post:

    python3 tools/build-blog.py

No dependencies. Header, footer and <head> come from tools/build-pages.py so the
journal stays identical to every other generated page.

Front matter fields (one per line, `key: value`):
  title        Headline (also <title>, og:title)
  slug         URL slug -> blog/<slug>.html
  description  Meta description, under ~160 characters
  date         YYYY-MM-DD
  category     Short label shown as the kicker (e.g. "Vacation Rentals")
  cover        Site-relative image path, e.g. images/exterior/DSC03243.jpg
  cover_alt    Alt text for the cover
  keywords     Comma-separated, or a [bracketed, list]
  related      Optional site-relative link shown under the article, e.g. services/drone-photography.html
  related_label  Text for that link
  featured     true to lead the journal index (otherwise the newest post leads)
  draft        true to skip the post (not built, not listed)

Markdown supported: ## / ### headings, paragraphs, - and 1. lists, **bold**, *italic*,
[links](/path.html), ![alt](images/x.jpg "Optional caption") on its own line,
> pull quotes, and --- rules. Links/images starting with "/" or "images/" are made
relative to the page. The first "# H1" line in the body is ignored (title comes
from front matter).
"""
from pathlib import Path
import html
import importlib.util
import json
import re
from datetime import date

ROOT = Path(__file__).parent.parent
SRC = ROOT / "content" / "blog"
OUT = ROOT / "blog"
SITE_URL = "https://lfpropertymedia.org"

_spec = importlib.util.spec_from_file_location("build_pages", Path(__file__).parent / "build-pages.py")
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)


# ---------- front matter + markdown ----------

def parse(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                v = v.strip().strip('"').strip("'")
                meta[k.strip()] = v
        body = m.group(2)
    kw = meta.get("keywords", "")
    meta["keywords"] = [k.strip().strip('"') for k in kw.strip("[]").split(",") if k.strip()]
    meta["date"] = date.fromisoformat(meta["date"])
    meta["draft"] = meta.get("draft", "").lower() == "true"
    meta["body"] = body
    return meta


def fix_url(url, rel):
    if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return url
    return rel + url.lstrip("/")


def inline(s, rel):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{html.escape(fix_url(m.group(2), rel))}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = s.replace(" -- ", " &mdash; ")
    return s


def markdown(md, rel):
    out, para, lst = [], [], None  # lst = ("ul"|"ol", [items])

    def flush():
        nonlocal para, lst
        if para:
            out.append(f"<p>{inline(' '.join(para), rel)}</p>")
            para = []
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i, rel)}</li>" for i in items) + f"</{tag}>")
            lst = None

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("<!--") or (line.startswith("# ") and not out):
            continue
        img = re.match(r'^!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)$', line)
        ul = re.match(r"^[-*]\s+(.*)$", line)
        ol = re.match(r"^\d+\.\s+(.*)$", line)
        if not line.strip():
            flush()
        elif line.startswith("### "):
            flush(); out.append(f"<h3>{inline(line[4:], rel)}</h3>")
        elif line.startswith("## "):
            flush(); out.append(f"<h2>{inline(line[3:], rel)}</h2>")
        elif line.strip() == "---":
            flush(); out.append('<hr />')
        elif line.startswith("> "):
            flush(); out.append(f'<blockquote><p>{inline(line[2:], rel)}</p></blockquote>')
        elif img:
            flush()
            alt, src, cap = img.groups()
            fig = (f'<figure class="post-figure"><img src="{html.escape(fix_url(src, rel))}" '
                   f'alt="{html.escape(alt)}" loading="lazy" decoding="async" />')
            if cap:
                fig += f"<figcaption>{inline(cap, rel)}</figcaption>"
            out.append(fig + "</figure>")
        elif ul or ol:
            if para:
                flush()
            tag = "ul" if ul else "ol"
            if not lst or lst[0] != tag:
                flush(); lst = (tag, [])
            lst[1].append((ul or ol).group(1))
        elif lst and raw.startswith(("  ", "\t")):
            lst[1][-1] += " " + line.strip()
        else:
            if lst:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(out)


def words(md):
    return len(re.findall(r"\w+", re.sub(r"<!--.*?-->", "", md, flags=re.S)))


def read_time(md):
    return max(2, round(words(md) / 230))


def nice_date(d):
    return d.strftime("%B %-d, %Y")


# ---------- shared pieces ----------

def mark_active(page_html):
    return page_html.replace('<li><a href="../blog/index.html">Journal</a></li>',
                             '<li><a class="active" href="../blog/index.html">Journal</a></li>', 1)


def card(p, featured=False):
    """Journal card. Every page that shows cards lives in blog/, so paths are local."""
    url = f"{p['slug']}.html"
    cls = "journal-card journal-card--featured" if featured else "journal-card"
    return f"""<article class="{cls} reveal">
  <a class="journal-card-image" href="{url}" tabindex="-1" aria-hidden="true">
    <img src="../{p['cover']}" alt="" loading="{'eager' if featured else 'lazy'}" decoding="async" />
  </a>
  <div class="journal-card-body">
    <span class="journal-meta"><span class="journal-category">{html.escape(p['category'])}</span><span aria-hidden="true">&middot;</span>{p['read']} min read</span>
    <h3><a href="{url}">{html.escape(p['title'])}</a></h3>
    <p class="journal-card-excerpt">{html.escape(p["description"])}</p>
    <a class="btn-ghost" href="{url}">Read the article</a>
  </div>
</article>"""


def cta():
    return """<section class="cta-banner">
  <div class="container">
    <h2>Have a property to <em>photograph</em>?</h2>
    <p>Send the address and square footage. We'll come back with a quote in under 24 hours.</p>
    <a href="../contact.html" class="btn btn-light">Get a Quote</a>
  </div>
</section>
"""


# ---------- pages ----------

def post_page(p, others):
    rel = "../"
    canonical = f"{SITE_URL}/blog/{p['slug']}.html"
    cover_abs = f"{SITE_URL}/{p['cover']}"
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": p["title"],
        "description": p["description"],
        "image": cover_abs,
        "datePublished": p["date"].isoformat(),
        "dateModified": p["date"].isoformat(),
        "mainEntityOfPage": canonical,
        "url": canonical,
        "wordCount": p["words"],
        "keywords": ", ".join(p["keywords"]),
        "author": {"@type": "Person", "name": "Lochlann Fourquin", "url": f"{SITE_URL}/about.html"},
        "publisher": {"@type": "Organization", "name": "LF Property Media", "url": f"{SITE_URL}/",
                      "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/images/og-image.jpg"}},
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Journal", "item": f"{SITE_URL}/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": canonical},
        ],
    }
    extra = (f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>\n'
             f'<script type="application/ld+json">\n{json.dumps(crumbs, indent=2, ensure_ascii=False)}\n</script>\n'
             f'<meta property="article:published_time" content="{p["date"].isoformat()}" />\n'
             f'<meta property="article:author" content="Lochlann Fourquin" />')
    head = bp.shared_head(f"{p['title']} | LF Property Media", p["description"], canonical,
                          og_image=cover_abs, rel_root=rel, extra_keywords=", ".join(p["keywords"]),
                          extra_schema=extra)
    head = head.replace('<meta property="og:type" content="website" />', '<meta property="og:type" content="article" />')
    # cover images are not 1200x630; drop the fixed size hints
    head = re.sub(r'<meta property="og:image:(width|height)" content="\d+" />\n', "", head)

    related = ""
    if p.get("related"):
        related = (f'<p class="post-related">Related service: '
                   f'<a href="{rel}{p["related"]}">{html.escape(p.get("related_label", "Learn more"))}</a></p>')

    more = "".join(card(o) for o in others[:2])
    body = f"""
<article class="post">
  <header class="post-header">
    <div class="container-narrow">
      <nav class="post-crumbs" aria-label="Breadcrumb"><a href="index.html">Journal</a><span aria-hidden="true">/</span><span>{html.escape(p['category'])}</span></nav>
      <h1>{html.escape(p['title'])}</h1>
      <p class="post-dek">{html.escape(p['description'])}</p>
      <p class="post-byline">By <a href="{rel}about.html">Lochlann Fourquin</a><span aria-hidden="true">&middot;</span><time datetime="{p['date'].isoformat()}">{nice_date(p['date'])}</time><span aria-hidden="true">&middot;</span>{p['read']} min read</p>
    </div>
  </header>

  <figure class="post-cover">
    <div class="container"><img src="{rel}{p['cover']}" alt="{html.escape(p['cover_alt'])}" fetchpriority="high" decoding="async" /></div>
  </figure>

  <div class="post-body container-narrow">
{markdown(p['body'], rel)}
    {related}
  </div>

  <aside class="post-author container-narrow" aria-label="About the author">
    <img src="{rel}images/about-portrait.jpg" alt="Lochlann Fourquin" loading="lazy" decoding="async" />
    <div>
      <span class="kicker">Written by</span>
      <p><strong>Lochlann Fourquin</strong> photographs homes, rentals and land across Sarasota and Southwest Florida. FAA Part 107 certified drone pilot. Photos delivered within 24 hours.</p>
      <a class="btn-ghost" href="{rel}about.html">More about LF Property Media</a>
    </div>
  </aside>
</article>

<section class="bg-cream journal-more">
  <div class="container">
    <div class="section-head reveal"><span class="kicker">Keep reading</span><h2>More from the <em>journal</em></h2><span class="divider"></span></div>
    <div class="journal-grid">
{more}
    </div>
  </div>
</section>

{cta()}"""
    return head + "\n" + mark_active(bp.shared_header(rel)) + body + bp.shared_footer(rel)


def index_page(posts):
    rel = "../"
    canonical = f"{SITE_URL}/blog/"
    desc = ("Practical advice on listing photos, drone aerials, twilight shoots and vacation rental "
            "photography from LF Property Media in Sarasota, Florida.")
    schema = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "The LF Journal",
        "url": canonical,
        "description": desc,
        "publisher": {"@type": "Organization", "name": "LF Property Media", "url": f"{SITE_URL}/"},
        "blogPost": [{"@type": "BlogPosting", "headline": p["title"],
                      "url": f"{SITE_URL}/blog/{p['slug']}.html",
                      "datePublished": p["date"].isoformat()} for p in posts],
    }
    extra = f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
    head = bp.shared_head("Journal: Real Estate Photography Advice | LF Property Media", desc, canonical,
                          rel_root=rel,
                          extra_keywords="real estate photography tips, vacation rental photography, Sarasota listing photos, drone photography, twilight photography",
                          extra_schema=extra)
    lead, rest = posts[0], posts[1:]
    grid = "\n".join(card(p) for p in rest)
    body = f"""
<section class="hero journal-hero">
  <div class="container">
    <div class="section-head" style="margin-bottom:0;">
      <span class="kicker">The LF Journal</span>
      <h1>Notes on homes that <em>sell</em> and rentals that <em>book</em></h1>
      <p class="lede-large" style="margin:24px auto 0;">Practical advice for agents, sellers and hosts across Sarasota and Southwest Florida. What to shoot, when it's worth it, and how to get a property ready for the camera.</p>
    </div>
  </div>
</section>

<section class="bg-white journal-lead-section">
  <div class="container">
{card(lead, featured=True)}
  </div>
</section>
""" + (f"""
<section class="journal-list">
  <div class="container">
    <div class="journal-grid">
{grid}
    </div>
  </div>
</section>
""" if rest else "") + cta()
    return head + "\n" + mark_active(bp.shared_header(rel)) + body + bp.shared_footer(rel)


def update_sitemap(posts):
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    entries = ["  <!-- journal:start (generated by tools/build-blog.py) -->",
               f"  <url>\n    <loc>{SITE_URL}/blog/</loc>\n    <lastmod>{posts[0]['date'].isoformat()}</lastmod>\n"
               f"    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>\n  </url>"]
    for p in posts:
        entries.append(
            f"  <url>\n    <loc>{SITE_URL}/blog/{p['slug']}.html</loc>\n    <lastmod>{p['date'].isoformat()}</lastmod>\n"
            f"    <changefreq>yearly</changefreq>\n    <priority>0.6</priority>\n"
            f"    <image:image>\n      <image:loc>{SITE_URL}/{p['cover']}</image:loc>\n"
            f"      <image:title>{html.escape(p['cover_alt'])}</image:title>\n    </image:image>\n  </url>")
    entries.append("  <!-- journal:end -->")
    block = "\n".join(entries)
    if "<!-- journal:start" in xml:
        xml = re.sub(r"  <!-- journal:start.*?<!-- journal:end -->", lambda _: block, xml, flags=re.S)
    else:
        xml = xml.replace("</urlset>", block + "\n\n</urlset>")
    path.write_text(xml, encoding="utf-8")


def main():
    posts = []
    for f in sorted(SRC.glob("*.md")):
        if f.name.startswith(("_", ".")):
            continue
        p = parse(f)
        if p["draft"]:
            continue
        p["words"] = words(p["body"])
        p["read"] = read_time(p["body"])
        posts.append(p)
    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)
    # an optional `featured: true` post leads the index; otherwise the newest does
    posts.sort(key=lambda p: p.get("featured", "").lower() != "true")
    OUT.mkdir(exist_ok=True)
    for p in posts:
        others = [o for o in posts if o is not p]
        (OUT / f"{p['slug']}.html").write_text(post_page(p, others), encoding="utf-8")
        print(f"  blog/{p['slug']}.html")
    (OUT / "index.html").write_text(index_page(posts), encoding="utf-8")
    print("  blog/index.html")
    update_sitemap(posts)
    print("  sitemap.xml")


if __name__ == "__main__":
    main()
