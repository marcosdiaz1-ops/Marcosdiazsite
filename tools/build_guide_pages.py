# Gated download pages for the free guides: /guides/ and /es/guias/
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
exec(open(os.path.join(HERE, 'build_pages.py')).read().split('# ---------- Home value pages ----------')[0].split("SRC = 'https://siouxfalls.business")[0])
from guides_content import GUIDES

SITE = 'https://605homesearch.com'
SHEET = 'https://script.google.com/macros/s/AKfycbw5PdoEEaGDAquTmKqO_1SkhtTaJG3G0584Xy4VIqG74FsaaH-tnxYpeIdrqTcCjZ0w/exec'
KEY = 'd0023d26-ed18-4970-8a35-c3de9e5f7e6c'
DESC = {
 'buyer': ("Budget, pre-approval, down payment help (including Give Me Five and VA), offers, inspection and closing, step by step.",
           "Presupuesto, preaprobación, ayuda para el pago inicial (incluidos Give Me Five y VA), ofertas, inspección y cierre, paso a paso."),
 'seller': ("Know your numbers, price it right, prepare your home, and what to expect from offers to closing.",
            "Conozca sus números, ponga el precio correcto, prepare su casa y sepa qué esperar desde las ofertas hasta el cierre."),
 'moving': ("Utilities, driver's license and plates, schools, and the best of Sioux Falls for new residents.",
            "Servicios, licencia y placas, escuelas y lo mejor de Sioux Falls para nuevos residentes."),
}
SHORT = {'buyer': ("Buyer's Guide", 'Guía para Compradores'), 'seller': ("Seller's Guide", 'Guía para Vendedores'),
         'moving': ('Moving to Sioux Falls', 'Mudarse a Sioux Falls')}

def T(es, e, s): return s if es else e

def build(es):
    path = 'es/guias/index.html' if es else 'guides/index.html'
    p = '../' * path.count('/')
    home = p + ('es/' if es else '')
    other = p + ('guides/' if es else 'es/guias/')
    cards = ''
    for k in GUIDES:
        g = GUIDES[k]
        cards += f'''          <label class="guide-pick">
            <input type="checkbox" name="guide" value="{k}" checked>
            <span class="guide-cover"><small>{T(es, 'Free Guide', 'Guía gratis')}</small><b>{g['title_es' if es else 'title_en']}</b></span>
            <span class="guide-desc">{DESC[k][1 if es else 0]}</span>
          </label>
'''
    links = ''.join(f'''          <a class="btn btn-navy guide-dl" data-guide="{k}" href="{p}guides/files/{GUIDES[k]['file_es' if es else 'file_en']}" download>{T(es, 'Download', 'Descargar')}: {SHORT[k][1 if es else 0]}</a>
''' for k in GUIDES)
    body = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{home}">{T(es, 'Home', 'Inicio')}</a> &nbsp;/&nbsp; {T(es, 'Free Guides', 'Guías gratis')}</p>
      <h1>{T(es, 'Free Home Guides', 'Guías gratis para su casa')}</h1>
      <p class="lead">{T(es, 'Simple, local guides for buying, selling, and moving to Sioux Falls. Pick the ones you want and they are yours instantly.', 'Guías sencillas y locales para comprar, vender y mudarse a Sioux Falls. Escoja las que quiera y descárguelas al instante.')}</p>
      <p class="post-meta"><a href="{other}">{T(es, 'Ver en español', 'View in English')}</a></p>
    </div>
  </section>
  <section class="page-body guides-page">
    <div class="wrap">
      <form id="guideForm" action="https://api.web3forms.com/submit" method="POST" data-sheet="{SHEET}" novalidate>
        <input type="hidden" name="access_key" value="{KEY}">
        <input type="hidden" name="subject" value="{T(es, 'Guide download from website', 'Guide download from website (ESPAÑOL)')}">
        <input type="hidden" name="from_name" value="Marcos Diaz Website">
        <input type="checkbox" name="botcheck" class="hidden" tabindex="-1" autocomplete="off">
        <p class="eyebrow">{T(es, '1. Choose your guides', '1. Escoja sus guías')}</p>
        <div class="guides-list">
{cards}        </div>
        <div class="guide-form">
          <p class="eyebrow">{T(es, '2. Where should I send them?', '2. ¿A dónde se las envío?')}</p>
          <div class="guide-fields">
            <label>{T(es, 'First &amp; last name', 'Nombre y apellido')}<input type="text" name="Name" autocomplete="name" required></label>
            <label>{T(es, 'Email', 'Correo electrónico')}<input type="email" name="email" autocomplete="email" required></label>
            <label>{T(es, 'Phone (optional)', 'Teléfono (opcional)')}<input type="tel" name="Phone" autocomplete="tel"></label>
          </div>
          <p class="error" role="alert"></p>
          <button type="submit" class="btn btn-navy">{T(es, 'Get My Free Guides', 'Recibir mis guías gratis')}</button>
          <p class="fine">{T(es, 'Free. Your information goes only to me and is never sold.', 'Gratis. Su información es solo para mí y nunca se vende.')} <a href="{p}{'es/privacidad.html' if es else 'privacy.html'}">{T(es, 'Privacy notice', 'Aviso de privacidad')}</a></p>
        </div>
        <div class="guide-done" hidden aria-live="polite">
          <h2>{T(es, 'Your guides are ready', 'Sus guías están listas')}<span class="sent-name"></span>!</h2>
          <p>{T(es, 'Tap to download. I will also reach out personally in case you have any questions.', 'Toque para descargar. También me comunicaré con usted personalmente por si tiene preguntas.')}</p>
          <div class="guide-links">
{links}          </div>
        </div>
      </form>
    </div>
  </section>'''
    alts = (f'<link rel="alternate" hreflang="en" href="{SITE}/guides/">\n'
            f'<link rel="alternate" hreflang="es" href="{SITE}/es/guias/">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/guides/">\n')
    page(path, T(es, "Free Sioux Falls Home Buyer's, Seller's & Moving Guides | Marcos Diaz", 'Guías gratis para comprar, vender y mudarse a Sioux Falls | Marcos Diaz'),
         T(es, "Download free guides for buying a home, selling a home, and moving to Sioux Falls, SD. In English and Spanish, from bilingual REALTOR® Marcos Diaz.",
              'Descargue guías gratis para comprar casa, vender casa y mudarse a Sioux Falls, SD. En español e inglés, de Marcos Diaz, agente bilingüe.'),
         body, lang='es' if es else 'en', canonical=f'{SITE}/{path[:-10]}',
         alt_es=None if es else other, alt_en=other if es else None, head_extra=alts, news=False)

for es in (False, True):
    build(es)

sm = open(f'{ROOT}/sitemap.xml').read()
for u in ('guides/', 'es/guias/'):
    if f'<loc>{SITE}/{u}</loc>' in sm: continue
    sm = sm.replace('</urlset>', f'''  <url>
    <loc>{SITE}/{u}</loc>
    <lastmod>2026-11-06</lastmod>
    <priority>0.8</priority>
    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/guides/"/>
    <xhtml:link rel="alternate" hreflang="es" href="{SITE}/es/guias/"/>
  </url>
</urlset>''')
open(f'{ROOT}/sitemap.xml', 'w').write(sm)
print('guide pages done')
