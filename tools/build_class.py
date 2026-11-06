# Free homebuyer class (Spanish) interest list: /es/clase-para-compradores/ and /homebuyer-class/
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'build_pages.py')).read().split('# ---------------- PRIVACY (EN)')[0])
from news import NEWS_SHEET
SITE = 'https://605homesearch.com'
EN, ES = 'homebuyer-class/', 'es/clase-para-compradores/'

def build(es):
    T = lambda e, s: s if es else e
    p = '../../' if es else '../'
    home = p + ('es/' if es else '')
    learn = T(['How much home you can afford, and what your monthly payment really includes',
               'Credit: what lenders look for and simple ways to improve it',
               'Down payment help: Give Me Five, South Dakota Housing programs, VA and FHA',
               'Buying with an ITIN, step by step',
               'Pre-approval, making an offer, inspection and closing',
               'Your questions, answered in plain language'],
              ['Cuánta casa puede comprar y qué incluye realmente su pago mensual',
               'El crédito: qué revisan los prestamistas y cómo mejorarlo',
               'Ayuda para el pago inicial: Give Me Five, programas de South Dakota Housing, VA y FHA',
               'Cómo comprar casa con ITIN, paso a paso',
               'Preaprobación, oferta, inspección y cierre',
               'Sus preguntas, respondidas de forma sencilla'])
    li = ''.join(f'<li>{x}</li>' for x in learn)
    done = T("Thanks{name}! You're on the list. I'll contact you with the date and place of the next class.",
             "¡Gracias{name}! Ya está en la lista. Le aviso la fecha y el lugar de la próxima clase.")
    body = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{home}">{T('Home','Inicio')}</a> &nbsp;/&nbsp; {T('Free Homebuyer Class','Clase gratis para compradores')}</p>
      <h1>{T('Free Homebuyer Class in Spanish','Clase gratis para comprar casa, en español')}</h1>
      <p class="lead">{T('A relaxed, no-pressure class in Sioux Falls for families who want to buy a home. Taught in Spanish by REALTOR® Marcos Diaz. Bring your questions and your family.','Una clase tranquila y sin compromiso en Sioux Falls para familias que quieren comprar casa. En español, con Marcos Diaz, agente de bienes raíces. Traiga sus preguntas y a su familia.')}</p>
      <p class="post-meta"><a href="{p}{EN if es else ES}">{T('Ver en español','View in English')}</a></p>
    </div>
  </section>
  <section class="page-body dpa">
    <div class="wrap page-grid">
      <div class="prose">
        <h2>{T("What you'll learn","Lo que va a aprender")}</h2>
        <ul>{li}</ul>
        <p>{T('The class is free. Dates are set based on interest, so join the list below and I will let you know when and where the next one is. Prefer one-on-one? Call or text me anytime at <a href="tel:+16058389140">605-838-9140</a>.','La clase es gratis. Las fechas se ponen según el interés, así que anótese abajo y le aviso cuándo y dónde será la próxima. ¿Prefiere una cita personal? Llámeme o envíeme un mensaje al <a href="tel:+16058389140">605-838-9140</a>.')}</p>
        <p class="fine">{T('Some down payment programs require a homebuyer education course from an approved provider. This class is general information to help you get started; ask your lender which course your program requires.','Algunos programas de ayuda para el pago inicial piden un curso de educación para compradores de un proveedor aprobado. Esta clase es información general para ayudarle a empezar; pregunte a su prestamista qué curso pide su programa.')}</p>
      </div>
    </div>
  </section>
  <section class="news-band">
    <div class="wrap news-inner">
      <div>
        <p class="eyebrow light">{T('Save my spot','Reservar mi lugar')}</p>
        <h2>{T('Join the list for the next class','Anótese para la próxima clase')}</h2>
        <p>{T('Free. Your information is only for me and is never sold.','Gratis. Su información es solo para mí y nunca se vende.')}</p>
      </div>
      <form class="news-form class-form" action="https://api.web3forms.com/submit" method="POST" data-sheet="{NEWS_SHEET}" data-looking="Homebuyer class (Spanish)" data-timeline="Class interest list" data-done="{done}" novalidate>
        <input type="hidden" name="access_key" value="d0023d26-ed18-4970-8a35-c3de9e5f7e6c">
        <input type="hidden" name="subject" value="{T('Homebuyer class sign-up','Homebuyer class sign-up (ESPAÑOL)')}">
        <input type="hidden" name="from_name" value="Marcos Diaz Website">
        <input type="checkbox" name="botcheck" class="hidden" tabindex="-1" autocomplete="off">
        <label><span class="sr-only">{T('Name','Nombre')}</span><input type="text" name="Name" placeholder="{T('Name','Nombre')}" autocomplete="name" required></label>
        <label><span class="sr-only">{T('Phone','Teléfono')}</span><input type="tel" name="Phone" placeholder="{T('Phone','Teléfono')}" autocomplete="tel" required></label>
        <label><span class="sr-only">Email</span><input type="email" name="email" placeholder="{T('Email (optional)','Correo (opcional)')}" autocomplete="email"></label>
        <button type="submit" class="btn btn-gold">{T('Save My Spot','Reservar')}</button>
        <p class="news-msg" role="status"></p>
      </form>
    </div>
  </section>'''
    path = (ES if es else EN) + 'index.html'
    alts = (f'<link rel="alternate" hreflang="en" href="{SITE}/{EN}">\n<link rel="alternate" hreflang="es" href="{SITE}/{ES}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/{ES}">\n')
    page(path, T('Free Homebuyer Class in Spanish | Sioux Falls | Marcos Diaz','Clase gratis para comprar casa en español | Sioux Falls | Marcos Diaz'),
         T('Free homebuyer class in Spanish in Sioux Falls: budget, credit, down payment help, ITIN loans and the buying process. Join the list for the next date.',
           'Clase gratis en español para comprar casa en Sioux Falls: presupuesto, crédito, ayuda para el pago inicial, préstamos ITIN y el proceso de compra. Anótese.'),
         body, lang='es' if es else 'en', canonical=f'{SITE}/{ES if es else EN}',
         alt_es=None if es else '../es/clase-para-compradores/', alt_en='../../homebuyer-class/' if es else None, head_extra=alts, news=False)

for es in (False, True): build(es)
sm = open(f'{ROOT}/sitemap.xml').read()
for u in (EN, ES):
    if f'<loc>{SITE}/{u}</loc>' in sm: continue
    sm = sm.replace('</urlset>', f'''  <url>
    <loc>{SITE}/{u}</loc>
    <lastmod>2026-11-06</lastmod>
    <priority>0.7</priority>
    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/{EN}"/>
    <xhtml:link rel="alternate" hreflang="es" href="{SITE}/{ES}"/>
  </url>
</urlset>''')
open(f'{ROOT}/sitemap.xml', 'w').write(sm)
print('class done')
