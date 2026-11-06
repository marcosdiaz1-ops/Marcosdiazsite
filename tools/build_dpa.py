# Down payment assistance pages: /down-payment-assistance/ and /es/ayuda-pago-inicial/
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'build_pages.py')).read().split('# ---------------- PRIVACY (EN)')[0])
SITE = 'https://605homesearch.com'
EN, ES = 'down-payment-assistance/', 'es/ayuda-pago-inicial/'

def T(es, e, s): return s if es else e

def card(title, body, tag=''):
    return f'''        <div class="dpa-card">
          {f'<span class="dpa-tag">{tag}</span>' if tag else ''}
          <h3>{title}</h3>
          {body}
        </div>
'''

def build(es):
    p = '../../' if es else '../'
    home = p + ('es/' if es else '')
    progs = ''.join([
      card('Give Me Five', T(es,
        '<p>South Dakota Housing\'s newest program, started November 2, 2026. Eligible first-time buyers can get down payment help equal to <b>5% of their mortgage</b>.</p><ul><li>No monthly payments</li><li>Forgiven after five years if you stay in the home and follow program rules</li><li>Homes up to $410,000; income limits apply (about $103,400 to $144,760 depending on county and household size)</li><li>Temporary: up to 2,500 loans statewide, so do not wait</li></ul>',
        '<p>El programa más nuevo de South Dakota Housing, comenzó el 2 de noviembre de 2026. Los compradores de primera casa que califiquen pueden recibir ayuda igual al <b>5% de su hipoteca</b>.</p><ul><li>Sin pagos mensuales</li><li>Se perdona después de cinco años si sigue viviendo en la casa y cumple las reglas</li><li>Casas de hasta $410,000; hay límites de ingreso (de unos $103,400 a $144,760 según el condado y el tamaño de la familia)</li><li>Temporal: máximo 2,500 préstamos en el estado, no espere</li></ul>'),
        T(es,'New','Nuevo')),
      card(T(es,'SD Housing First-Time Homebuyer Program','Programa de South Dakota Housing para compradores de primera casa'), T(es,
        '<p>Low, fixed-rate loans through participating local lenders, with optional down payment and closing cost help (commonly 3% or 5% of the loan, as a 0% interest loan).</p><ul><li>Works with FHA, Conventional, VA, and USDA loans</li><li>Purchase price and income limits apply</li><li>A Mortgage Credit Certificate (MCC) may lower your federal income tax</li></ul>',
        '<p>Préstamos de tasa fija y baja a través de prestamistas locales participantes, con ayuda opcional para el pago inicial y gastos de cierre (comúnmente 3% o 5% del préstamo, como préstamo sin interés).</p><ul><li>Funciona con préstamos FHA, Convencional, VA y USDA</li><li>Hay límites de precio y de ingreso</li><li>Un Certificado de Crédito Hipotecario (MCC) puede bajar su impuesto federal</li></ul>')),
      card(T(es,'SD Housing Repeat Homebuyer Program','Programa de South Dakota Housing para quienes ya tuvieron casa'), T(es,
        '<p>Already owned a home? This program offers competitive rates, flexible down payment options, possible down payment help, and reduced mortgage insurance for qualified buyers.</p>',
        '<p>¿Ya fue dueño de casa? Este programa ofrece tasas competitivas, opciones flexibles de pago inicial, posible ayuda para el pago inicial y seguro hipotecario reducido para quienes califiquen.</p>')),
      card('GROW South Dakota', T(es,
        '<p>A nonprofit that offers zero-interest, deferred loans for down payment and closing costs to income-qualified buyers across South Dakota. Funds are limited and come in rounds.</p>',
        '<p>Una organización sin fines de lucro que ofrece préstamos sin interés y diferidos para el pago inicial y los gastos de cierre a compradores que califiquen por ingreso en todo South Dakota. Los fondos son limitados y se abren por temporadas.</p>')),
      card(T(es,'City of Sioux Falls: Public Safety','Ciudad de Sioux Falls: Seguridad pública'), T(es,
        '<p>For full-time certified police officers and firefighters. Up to $20,000 or 20% of the price (whichever is less) for homes in certain Sioux Falls neighborhoods, up to $385,000. Apply at least four weeks before closing.</p>',
        '<p>Para policías y bomberos certificados de tiempo completo. Hasta $20,000 o el 20% del precio (lo que sea menor) para casas en ciertos vecindarios de Sioux Falls, de hasta $385,000. Solicítelo al menos cuatro semanas antes del cierre.</p>')),
    ])
    loans = ''.join([
      card(T(es,'VA loan','Préstamo VA'), T(es,'<p><b>$0 down</b> for eligible veterans, service members, and some surviving spouses. No monthly mortgage insurance. <a href="'+p+'blog/va-home-loans-sioux-falls/">Read my VA guide →</a></p>','<p><b>$0 de pago inicial</b> para veteranos, militares y algunos cónyuges sobrevivientes que califiquen. Sin seguro hipotecario mensual. <a href="'+p+'es/blog/prestamos-va-sioux-falls/">Lea mi guía VA →</a></p>')),
      card(T(es,'USDA loan','Préstamo USDA'), T(es,'<p><b>$0 down</b> for homes in eligible rural areas. Some towns around Sioux Falls may qualify; income limits apply. Check any address on the USDA eligibility map.</p>','<p><b>$0 de pago inicial</b> para casas en zonas rurales elegibles. Algunos pueblos alrededor de Sioux Falls pueden calificar; hay límites de ingreso. Revise cualquier dirección en el mapa de elegibilidad de USDA.</p>')),
      card('FHA', T(es,'<p>As little as <b>3.5% down</b> with more flexible credit guidelines. Can be combined with down payment assistance.</p>','<p>Desde <b>3.5% de pago inicial</b> con requisitos de crédito más flexibles. Se puede combinar con ayuda para el pago inicial.</p>')),
      card(T(es,'Conventional','Convencional'), T(es,'<p>As little as <b>3% down</b> for qualified first-time buyers. Mortgage insurance can be removed once you reach 20% equity.</p>','<p>Desde <b>3% de pago inicial</b> para compradores de primera casa que califiquen. El seguro hipotecario se puede quitar al llegar al 20% de capital.</p>')),
    ])
    steps = T(es, ['Talk to a lender who works with South Dakota Housing programs. They check which programs you qualify for.',
                   'Get pre-approved with the assistance built in, so you know your real price range.',
                   'Take a homebuyer education class if your program requires it (Sioux Empire Housing Partnership offers one locally).',
                   'Shop for homes under the program limits with me, then we write a strong offer.'],
                  ['Hable con un prestamista que trabaje con los programas de South Dakota Housing. Ellos revisan para qué programas califica.',
                   'Obtenga su preaprobación con la ayuda incluida, para saber su rango de precio real.',
                   'Tome una clase de educación para compradores si su programa la requiere (Sioux Empire Housing Partnership ofrece una aquí).',
                   'Busque casas dentro de los límites del programa conmigo y hacemos una oferta fuerte.'])
    steps_html = ''.join(f'<li>{x}</li>' for x in steps)
    body = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{home}">{T(es,'Home','Inicio')}</a> &nbsp;/&nbsp; {T(es,'Down Payment Help','Ayuda para el pago inicial')}</p>
      <h1>{T(es,'Down Payment Assistance in Sioux Falls &amp; South Dakota','Ayuda para el pago inicial en Sioux Falls y South Dakota')}</h1>
      <p class="lead">{T(es,'You may need much less saved than you think. Here are the programs that can help you buy in Sioux Falls, explained in plain language.','Puede necesitar mucho menos ahorrado de lo que cree. Estos son los programas que le pueden ayudar a comprar en Sioux Falls, explicados de forma sencilla.')}</p>
      <p class="hero-search"><a href="{home}#lender" class="btn btn-gold">{T(es,'Check What I Qualify For','Ver para qué califico')}</a></p>
    </div>
  </section>
  <section class="page-body dpa">
    <div class="wrap">
      <div class="prose">
        <p>{T(es,'<b>"First-time buyer" usually means you have not owned a home in the past three years</b>, so even past owners may qualify. Most programs have income and price limits, and rules change, so always confirm the current details with a lender before you count on them.','<b>"Comprador de primera casa" normalmente significa que no ha sido dueño de una casa en los últimos tres años</b>, así que incluso quienes ya tuvieron casa pueden calificar. La mayoría de los programas tienen límites de ingreso y precio, y las reglas cambian, así que siempre confirme los detalles actuales con un prestamista.')}</p>
      </div>
      <h2>{T(es,'Down payment help programs','Programas de ayuda para el pago inicial')}</h2>
      <div class="dpa-grid">
{progs}      </div>
      <h2>{T(es,'Low and no down payment loans','Préstamos con poco o nada de pago inicial')}</h2>
      <div class="dpa-grid four">
{loans}      </div>
      <div class="dpa-steps">
        <h2>{T(es,'How to get started','Cómo empezar')}</h2>
        <ol>{steps_html}</ol>
        <div class="dpa-cta">
          <a href="{home}#lender" class="btn btn-navy">{T(es,'Talk to My Bilingual Lender','Hablar con mi prestamista bilingüe')}</a>
          <a href="{home}#contact" class="btn btn-gold">{T(es,'Talk to Marcos','Hablar con Marcos')}</a>
          <a href="{p}{'es/guias/' if es else 'guides/'}" class="calc-link dark">{T(es,'Get my free Buyer&rsquo;s Guide (PDF) →','Mi Guía para Compradores gratis (PDF) →')}</a>
        </div>
      </div>
      <p class="fine dpa-src">{T(es,'Sources','Fuentes')}: South Dakota Housing (sdhousing.org); GROW South Dakota (growsd.org); City of Sioux Falls Public Safety Down Payment Assistance (siouxfalls.gov); VA.gov; USDA Rural Development. {T(es,'Updated November 2026. Program details can change at any time; this is general information, not a loan offer.','Actualizado en noviembre de 2026. Los detalles de los programas pueden cambiar en cualquier momento; esta es información general, no una oferta de préstamo.')}</p>
    </div>
  </section>'''
    path = (ES if es else EN) + 'index.html'
    alts = (f'<link rel="alternate" hreflang="en" href="{SITE}/{EN}">\n<link rel="alternate" hreflang="es" href="{SITE}/{ES}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/{EN}">\n')
    page(path, T(es,'Down Payment Assistance in Sioux Falls, SD (2026) | Give Me Five, VA, FHA | Marcos Diaz','Ayuda para el pago inicial en Sioux Falls, SD (2026) | Give Me Five, VA, FHA | Marcos Diaz'),
         T(es,'Down payment help for Sioux Falls homebuyers: Give Me Five (5%), South Dakota Housing programs, GROW SD, VA and USDA $0 down, FHA 3.5%. Explained by bilingual REALTOR® Marcos Diaz.',
              'Ayuda para el pago inicial en Sioux Falls: Give Me Five (5%), programas de South Dakota Housing, GROW SD, VA y USDA sin pago inicial, FHA 3.5%. Explicado por Marcos Diaz, agente bilingüe.'),
         body, lang='es' if es else 'en', canonical=f'{SITE}/{ES if es else EN}',
         alt_es=None if es else '../es/ayuda-pago-inicial/', alt_en='../../down-payment-assistance/' if es else None, head_extra=alts)

for es in (False, True): build(es)

sm = open(f'{ROOT}/sitemap.xml').read()
for u in (EN, ES):
    if f'<loc>{SITE}/{u}</loc>' in sm: continue
    sm = sm.replace('</urlset>', f'''  <url>
    <loc>{SITE}/{u}</loc>
    <lastmod>2026-11-06</lastmod>
    <priority>0.9</priority>
    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/{EN}"/>
    <xhtml:link rel="alternate" hreflang="es" href="{SITE}/{ES}"/>
  </url>
</urlset>''')
open(f'{ROOT}/sitemap.xml', 'w').write(sm)
print('dpa done')
