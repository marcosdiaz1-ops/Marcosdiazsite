"""Add a post card to the EN/ES blog indexes and sitemap. Usage: add_listing.py cfg.json (keys: en_slug, es_slug, date, en_tag, en_title, en_blurb, es_tag, es_title, es_blurb)"""
import sys, json, pathlib, html
c = json.loads(pathlib.Path(sys.argv[1]).read_text())
root = pathlib.Path(__file__).resolve().parents[2]
def card(slug, tag, title, blurb, more):
    return f'''        <a class="post-card" href="{slug}/">
          <span class="post-tag">{tag}</span>
          <h2>{title}</h2>
          <p>{blurb}</p>
          <span class="post-more">{more}</span>
        </a>
'''
for f, slug, tag, title, blurb, more in [
    (root/"blog/index.html", c["en_slug"], c["en_tag"], c["en_title"], c["en_blurb"], "Read more →"),
    (root/"es/blog/index.html", c["es_slug"], c["es_tag"], c["es_title"], c["es_blurb"], "Leer más →")]:
    t = f.read_text()
    if f'href="{slug}/"' in t: continue
    t = t.replace('<div class="post-list">\n', '<div class="post-list">\n' + card(slug, tag, title, blurb, more), 1)
    f.write_text(t)
en = f"https://605homesearch.com/blog/{c['en_slug']}/"; es = f"https://605homesearch.com/es/blog/{c['es_slug']}/"
sm = root/"sitemap.xml"; t = sm.read_text()
if en not in t:
    entry = ""
    for loc in (en, es):
        entry += f'''  <url>
    <loc>{loc}</loc>
    <lastmod>{c["date"]}</lastmod>
    <priority>0.7</priority>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
    <xhtml:link rel="alternate" hreflang="es" href="{es}"/>
  </url>
'''
    t = t.replace("</urlset>", entry + "</urlset>")
    sm.write_text(t)
print("ok")
