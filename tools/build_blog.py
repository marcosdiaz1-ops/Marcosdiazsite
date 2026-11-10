# Blog pages for 605homesearch.com (EN + ES). Uses page() from build_pages.py.
import json, html, re
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'build_pages.py')).read().split('# ---------- Home value pages ----------')[0].split("SRC = 'https://siouxfalls.business")[0])

SITE = 'https://605homesearch.com'
BOOK = 'https://calendar.app.google/rymyVUbd555Y3xSDA'
exec(open(os.path.join(HERE, 'lender.py')).read())

exec(open(os.path.join(HERE, 'blog_posts.py'), encoding='utf-8').read())  # defines POSTS


def side(es, p):
    home = p + ('es/' if es else '')
    hv = p + ('es/valor-de-casa/' if es else 'home-value/')
    if es:
        return f'''        <aside class="side-card">
          <p class="eyebrow">¿Listo para empezar?</p>
          <h3>Hable con Marcos</h3>
          <p class="muted" style="font-size:.95rem">Agente bilingüe con Keller Williams Realty Sioux Falls. Le ayudo a comprar o vender con confianza.</p>
          <a href="{BOOK}" target="_blank" rel="noopener" class="btn btn-gold">Agendar una llamada</a>
          <a href="{SEARCH}" class="btn btn-navy">Buscar casas en venta</a>
          <a href="{hv}" class="btn btn-navy">¿Cuánto vale mi casa?</a>
          <p class="muted">Llame o envíe texto al <a href="tel:+16058389140">605-838-9140</a></p>
        </aside>'''
    return f'''        <aside class="side-card">
          <p class="eyebrow">Ready to talk?</p>
          <h3>Work with Marcos</h3>
          <p class="muted" style="font-size:.95rem">Bilingual REALTOR® with Keller Williams Realty Sioux Falls, helping buyers and sellers move with confidence.</p>
          <a href="{BOOK}" target="_blank" rel="noopener" class="btn btn-gold">Book a 15-Min Call</a>
          <a href="{SEARCH}" class="btn btn-navy">Search Homes</a>
          <a href="{hv}" class="btn btn-navy">What's My Home Worth?</a>
          <p class="muted">Call or text <a href="tel:+16058389140">605-838-9140</a> · Se habla español</p>
        </aside>'''


def blog_ld(post, es, url):
    return ld({"@context": "https://schema.org", "@type": "BlogPosting",
               "headline": post['title_es' if es else 'title'], "description": post['desc_es' if es else 'desc'],
               "inLanguage": 'es' if es else 'en', "datePublished": post['date'], "dateModified": post['date'],
               "mainEntityOfPage": url, "image": SITE + "/images/og-image.jpg",
               "author": {"@type": "Person", "name": "Marcos Diaz", "url": SITE + "/"},
               "publisher": {"@type": "Organization", "name": "Marcos Diaz, Keller Williams Realty Sioux Falls",
                             "logo": {"@type": "ImageObject", "url": SITE + "/images/og-image.jpg"}}})


def alts(en_url, es_url):
    return (f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
            f'<link rel="alternate" hreflang="es" href="{es_url}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{en_url}">\n')


for post in POSTS:
    for es in (False, True):
        path = f"es/blog/{post['es_slug']}/index.html" if es else f"blog/{post['slug']}/index.html"
        depth = path.count('/'); p = '../' * depth
        url = f"{SITE}/{path[:-10]}"
        en_url = f"{SITE}/blog/{post['slug']}/"; es_url = f"{SITE}/es/blog/{post['es_slug']}/"
        home = p + ('es/' if es else '')
        blog = p + ('es/blog/' if es else 'blog/')
        body = post['body_es' if es else 'body'].format(home=home, blog=blog, areas=p + ('es/areas/' if es else 'areas/'), book=BOOK)
        other = (f"{p}blog/{post['slug']}/" if es else f"{p}es/blog/{post['es_slug']}/")
        content = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{home}">{'Inicio' if es else 'Home'}</a> &nbsp;/&nbsp; <a href="{blog}">Blog</a></p>
      <p class="post-tag">{post['tag_es' if es else 'tag']}</p>
      <h1 class="post-title">{post['title_es' if es else 'title']}</h1>
      <p class="post-meta">{'Por' if es else 'By'} Marcos Diaz, REALTOR® · {post['date_es' if es else 'date_en']} · <a href="{other}">{'View in English' if es else 'Ver en español'}</a></p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap">
      <div class="page-grid">
        <article class="prose post">
{body}
        </article>
        <div class="post-side">
{side(es, p)}
{lender(es, p, compact=True)}
        </div>
      </div>
    </div>
  </section>'''
        title = post['title_es' if es else 'title'] + ' | Marcos Diaz'
        page(path, title, post['desc_es' if es else 'desc'], content, lang='es' if es else 'en', canonical=url,
             alt_es=None if es else other, alt_en=other if es else None,
             head_extra=alts(en_url, es_url) + blog_ld(post, es, url))

# Blog index pages
for es in (False, True):
    path = 'es/blog/index.html' if es else 'blog/index.html'
    p = '../' * path.count('/')
    home = p + ('es/' if es else '')
    cards = ''
    for post in sorted(POSTS, key=lambda x: x['date'], reverse=True):
        href = (post['es_slug'] if es else post['slug']) + '/'
        cards += f'''        <a class="post-card" href="{href}">
          <span class="post-tag">{post['tag_es' if es else 'tag']}</span>
          <h2>{post['title_es' if es else 'title']}</h2>
          <p>{post['desc_es' if es else 'desc']}</p>
          <span class="post-more">{'Leer más' if es else 'Read more'} →</span>
        </a>
'''
    content = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{home}">{'Inicio' if es else 'Home'}</a> &nbsp;/&nbsp; Blog</p>
      <h1>{'Blog de bienes raíces' if es else 'Real Estate Blog'}</h1>
      <p class="lead">{'Consejos sencillos para comprar y vender casa en Sioux Falls, Tea, Harrisburg y Brandon. Por Marcos Diaz, REALTOR®.' if es else 'Simple, local advice for buying and selling a home in Sioux Falls, Tea, Harrisburg and Brandon. From Marcos Diaz, REALTOR®.'}</p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap">
      <div class="post-list">
{cards}      </div>
    </div>
  </section>'''
    other = f'{p}blog/' if es else f'{p}es/blog/'
    page(path, ('Blog de bienes raíces en Sioux Falls | Marcos Diaz' if es else 'Sioux Falls Real Estate Blog | Marcos Diaz, REALTOR®'),
         ('Consejos para comprar y vender casa en Sioux Falls: programas de ayuda, préstamos VA, guías para compradores y más.' if es else
          'Tips for buying and selling a home in Sioux Falls: down payment programs, VA loans, buyer guides and more.'),
         content, lang='es' if es else 'en', canonical=f"{SITE}/{path[:-10]}",
         alt_es=None if es else other, alt_en=other if es else None,
         head_extra=alts(f'{SITE}/blog/', f'{SITE}/es/blog/'))

# sitemap entries
sm = open(f'{ROOT}/sitemap.xml').read()
pairs = [('blog/', 'es/blog/')] + [(f"blog/{x['slug']}/", f"es/blog/{x['es_slug']}/") for x in POSTS]
for en, esu in pairs:
    for u in (en, esu):
        if f'<loc>{SITE}/{u}</loc>' in sm: continue
        sm = sm.replace('</urlset>', f'''  <url>
    <loc>{SITE}/{u}</loc>
    <lastmod>2026-11-05</lastmod>
    <priority>0.8</priority>
    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/{en}"/>
    <xhtml:link rel="alternate" hreflang="es" href="{SITE}/{esu}"/>
  </url>
</urlset>''')
open(f'{ROOT}/sitemap.xml', 'w').write(sm)
print('blog done')
