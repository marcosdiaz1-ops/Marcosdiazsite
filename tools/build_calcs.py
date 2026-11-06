# Affordability calculator + seller net sheet pages (EN + ES)
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'build_pages.py')).read().split('# ---------- Home value pages ----------')[0].split("SRC = 'https://siouxfalls.business")[0])
exec(open(os.path.join(HERE, 'lender.py')).read())

SITE = 'https://605homesearch.com'
BOOK = 'https://calendar.app.google/rymyVUbd555Y3xSDA'
RATE = '7.25'  # default rate; Freddie Mac PMMS 30-yr avg was 7.24% on Oct 29, 2026

PAGES = {
 'afford': {
   'en': 'calculators/affordability/index.html', 'es': 'es/calculadoras/cuanto-puedo-comprar/index.html'},
 'net': {
   'en': 'calculators/seller-net-sheet/index.html', 'es': 'es/calculadoras/hoja-neta-vendedor/index.html'},
}

def T(es, e, s):
    return s if es else e

def alts(key):
    en, es = PAGES[key]['en'][:-10], PAGES[key]['es'][:-10]
    return (f'<link rel="alternate" hreflang="en" href="{SITE}/{en}">\n'
            f'<link rel="alternate" hreflang="es" href="{SITE}/{es}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/{en}">\n')

def hero(es, p, title, lead, other):
    home = p + ('es/' if es else '')
    return f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{home}">{T(es, 'Home', 'Inicio')}</a> &nbsp;/&nbsp; {T(es, 'Calculators', 'Calculadoras')}</p>
      <h1>{title}</h1>
      <p class="lead">{lead}</p>
      <p class="post-meta"><a href="{other}">{T(es, 'Ver en español', 'View in English')}</a></p>
    </div>
  </section>'''

def afford(es):
    key = 'afford'; path = PAGES[key]['es' if es else 'en']; p = '../' * path.count('/')
    other = p + PAGES[key]['en' if es else 'es'][:-10]
    netlink = p + PAGES['net']['es' if es else 'en'][:-10]
    body = hero(es, p, T(es, 'How Much House Can I Afford?', '¿Cuánta casa puedo comprar?'),
                T(es, 'Enter your income and monthly debts to see an estimated price range for a home in Sioux Falls.',
                  'Escriba su ingreso y sus deudas mensuales para ver un rango de precio estimado para una casa en Sioux Falls.'), other)
    body += f'''
  <section class="calculator tool-page">
    <div class="wrap calc-grid" id="affordCalc">
      <div class="calc-inputs">
        <p class="eyebrow">{T(es, 'Affordability Calculator', 'Calculadora de presupuesto')}</p>
        <h2>{T(es, 'Your numbers', 'Sus números')}</h2>
        <div class="two">
          <label>{T(es, 'Household income ($/yr, before taxes)', 'Ingreso del hogar ($/año, antes de impuestos)')}<input type="text" inputmode="numeric" name="income" value="75,000"></label>
          <label>{T(es, 'Monthly debt payments ($)', 'Pagos mensuales de deudas ($)')}<input type="text" inputmode="numeric" name="debts" value="400"></label>
        </div>
        <p class="calc-hint">{T(es, 'Debts: car loans, student loans, credit card minimums, child support. Not rent, utilities or groceries.', 'Deudas: préstamos de auto, préstamos estudiantiles, pagos mínimos de tarjetas, manutención. No incluya renta, servicios ni comida.')}</p>
        <div class="two">
          <label>{T(es, 'Cash for down payment ($)', 'Dinero para el pago inicial ($)')}<input type="text" inputmode="numeric" name="down" value="15,000"></label>
          <label>{T(es, 'Interest rate (%)', 'Tasa de interés (%)')}<input type="number" name="rate" value="{RATE}" min="0" max="20" step="0.125"></label>
        </div>
        <div class="two three">
          <label>{T(es, 'Budget style', 'Tipo de presupuesto')}
            <select name="dti">
              <option value="36">{T(es, 'Comfortable', 'Cómodo')}</option>
              <option value="43" selected>{T(es, 'Typical', 'Típico')}</option>
              <option value="45">{T(es, 'Stretch', 'Al máximo')}</option>
            </select>
          </label>
          <label>{T(es, 'Property tax (%/yr)', 'Impuesto a la propiedad (%/año)')}<input type="number" name="tax" value="1.2" min="0" max="5" step="0.05"></label>
          <label>{T(es, 'Insurance ($/yr)', 'Seguro ($/año)')}<input type="text" inputmode="numeric" name="insurance" value="1,800"></label>
        </div>
        <p class="calc-note">{T(es,
          'An estimate only, not a loan approval. It uses a 30-year fixed loan, your chosen share of income for all monthly debts (36%, 43% or 45%), and adds an estimated 0.5%/yr mortgage insurance when the down payment is under 20%. The default rate is near the Freddie Mac national average for late October 2026; use your lender’s quote. Property taxes vary by home.',
          'Solo es un estimado, no una aprobación de préstamo. Usa un préstamo fijo a 30 años, el porcentaje de su ingreso que escoja para todas sus deudas mensuales (36%, 43% o 45%) y suma un seguro hipotecario estimado de 0.5% al año si el pago inicial es menor al 20%. La tasa inicial está cerca del promedio nacional de Freddie Mac de fines de octubre de 2026; use la cotización de su prestamista. Los impuestos varían según la casa.')}</p>
      </div>
      <div class="calc-result">
        <p class="calc-label">{T(es, 'Estimated home price you can afford', 'Precio estimado de casa que puede pagar')}</p>
        <p class="calc-total" data-out="price">$0</p>
        <dl class="calc-lines">
          <div><dt>{T(es, 'Monthly payment', 'Pago mensual')}</dt><dd data-out="payment">$0</dd></div>
          <div><dt>{T(es, 'Principal &amp; interest', 'Capital e interés')}</dt><dd data-out="pi">$0</dd></div>
          <div><dt>{T(es, 'Taxes, insurance &amp; PMI', 'Impuestos, seguro y PMI')}</dt><dd data-out="tip">$0</dd></div>
        </dl>
        <dl class="calc-lines small">
          <div><dt>{T(es, 'Loan amount', 'Monto del préstamo')}</dt><dd data-out="loan">$0</dd></div>
          <div><dt>{T(es, 'Down payment', 'Pago inicial')}</dt><dd data-out="downPct">0%</dd></div>
        </dl>
        <p class="calc-warn" data-out="warn" hidden>{T(es, 'Your monthly debts are high compared to your income. A lender can show you ways to improve your numbers.', 'Sus deudas mensuales son altas comparadas con su ingreso. Un prestamista le puede mostrar cómo mejorar sus números.')}</p>
        <a href="#lender" class="btn btn-gold">{T(es, 'Get Pre-Approved', 'Obtener mi preaprobación')}</a>
        <a href="{p}{'es/blog/give-me-five-ayuda-pago-inicial/' if es else 'blog/give-me-five-down-payment-assistance/'}" class="calc-link">{T(es, 'First-time buyer? See the 5% down payment help program →', '¿Primera casa? Vea el programa de 5% de ayuda para el pago inicial →')}</a>
      </div>
    </div>
  </section>
  <section id="lender" class="lender-sec tool-lender">
    <div class="wrap">
{lender(es, p)}
    </div>
  </section>
  <section class="page-body tool-more">
    <div class="wrap narrow">
      <h2>{T(es, 'What this number means', 'Qué significa este número')}</h2>
      <p>{T(es, 'Lenders look at how much of your monthly income goes to debts, including your new house payment. Keeping that share lower gives you more breathing room for savings, repairs and life. Credit score, loan type and down payment programs can all change what you qualify for, so a quick pre-approval is the best next step.',
             'Los prestamistas revisan qué parte de su ingreso mensual se va en deudas, incluido el nuevo pago de la casa. Mientras más bajo sea ese porcentaje, más espacio le queda para ahorrar, reparaciones y la vida diaria. Su crédito, el tipo de préstamo y los programas de ayuda pueden cambiar para cuánto califica, así que una preaprobación rápida es el mejor siguiente paso.')}</p>
      <p><a href="{p}{'es/' if es else ''}#calculator">{T(es, 'Already have a price in mind? Try the mortgage payment calculator →', '¿Ya tiene un precio en mente? Use la calculadora de pago mensual →')}</a><br>
         <a href="{netlink}">{T(es, 'Selling too? Estimate your net proceeds →', '¿También va a vender? Calcule cuánto le queda →')}</a></p>
    </div>
  </section>'''
    page(path, T(es, 'How Much House Can I Afford? Sioux Falls Calculator | Marcos Diaz', '¿Cuánta casa puedo comprar? Calculadora Sioux Falls | Marcos Diaz'),
         T(es, 'Free home affordability calculator for Sioux Falls buyers. Enter your income, debts and down payment to see an estimated price range and monthly payment.',
              'Calculadora gratis para compradores en Sioux Falls. Escriba su ingreso, deudas y pago inicial para ver un rango de precio y pago mensual estimado.'),
         body, lang='es' if es else 'en', canonical=f'{SITE}/{path[:-10]}',
         alt_es=None if es else other, alt_en=other if es else None, head_extra=alts(key))

def net(es):
    key = 'net'; path = PAGES[key]['es' if es else 'en']; p = '../' * path.count('/')
    other = p + PAGES[key]['en' if es else 'es'][:-10]
    hv = p + ('es/valor-de-casa/' if es else 'home-value/')
    body = hero(es, p, T(es, 'Seller Net Sheet Calculator', 'Calculadora para vendedores'),
                T(es, 'Estimate how much you could walk away with when you sell your Sioux Falls area home.',
                  'Calcule cuánto dinero le podría quedar al vender su casa en el área de Sioux Falls.'), other)
    body += f'''
  <section class="calculator tool-page">
    <div class="wrap calc-grid" id="netSheet">
      <div class="calc-inputs">
        <p class="eyebrow">{T(es, 'Net Proceeds', 'Ganancia neta')}</p>
        <h2>{T(es, 'Your sale', 'Su venta')}</h2>
        <div class="two">
          <label>{T(es, 'Sale price ($)', 'Precio de venta ($)')}<input type="text" inputmode="numeric" name="price" value="345,000"></label>
          <label>{T(es, 'Mortgage payoff ($)', 'Saldo de su hipoteca ($)')}<input type="text" inputmode="numeric" name="payoff" value="180,000"></label>
        </div>
        <div class="two">
          <label>{T(es, 'Agent commissions (%)', 'Comisiones de agentes (%)')}<input type="number" name="commission" value="5" min="0" max="10" step="0.25"></label>
          <label>{T(es, 'Title &amp; closing fees ($)', 'Título y costos de cierre ($)')}<input type="text" inputmode="numeric" name="closing" value="1,500"></label>
        </div>
        <div class="two three">
          <label>{T(es, 'Help to buyer ($)', 'Ayuda al comprador ($)')}<input type="text" inputmode="numeric" name="concessions" value="0"></label>
          <label>{T(es, 'Repairs ($)', 'Reparaciones ($)')}<input type="text" inputmode="numeric" name="repairs" value="0"></label>
          <label>{T(es, 'Property tax proration ($)', 'Prorrateo de impuestos ($)')}<input type="text" inputmode="numeric" name="taxes" value="0"></label>
        </div>
        <p class="calc-note">{T(es,
          'An estimate only. Commissions are negotiable and shown here as a total for all agents. The South Dakota real estate transfer fee (50¢ per $500 of value, paid by the seller under SDCL 43-4-21) is added for you. Title, closing fees and property tax proration vary by sale, so ask me for an exact net sheet before you list.',
          'Solo es un estimado. Las comisiones son negociables y aquí se muestran como un total para todos los agentes. La tarifa estatal de transferencia de Dakota del Sur (50¢ por cada $500 de valor, que paga el vendedor según SDCL 43-4-21) se suma automáticamente. El título, los costos de cierre y el prorrateo de impuestos varían, así que pídame una hoja neta exacta antes de vender.')}</p>
      </div>
      <div class="calc-result">
        <p class="calc-label">{T(es, 'Estimated cash to you at closing', 'Dinero estimado para usted al cierre')}</p>
        <p class="calc-total" data-out="net">$0</p>
        <dl class="calc-lines">
          <div><dt>{T(es, 'Sale price', 'Precio de venta')}</dt><dd data-out="price">$0</dd></div>
          <div><dt>{T(es, 'Mortgage payoff', 'Pago de hipoteca')}</dt><dd data-out="payoff">$0</dd></div>
          <div><dt>{T(es, 'Commissions', 'Comisiones')}</dt><dd data-out="commission">$0</dd></div>
          <div><dt>{T(es, 'SD transfer fee', 'Tarifa de transferencia SD')}</dt><dd data-out="transfer">$0</dd></div>
          <div><dt>{T(es, 'Closing, repairs &amp; other', 'Cierre, reparaciones y otros')}</dt><dd data-out="other">$0</dd></div>
        </dl>
        <a href="{hv}" class="btn btn-gold">{T(es, 'Get My Exact Home Value', 'Recibir el valor exacto de mi casa')}</a>
        <a href="{BOOK}" target="_blank" rel="noopener" class="calc-link">{T(es, 'Talk it through with Marcos: book a 15-min call →', 'Hable con Marcos: agende una llamada de 15 min →')}</a>
      </div>
    </div>
  </section>'''
    page(path, T(es, 'Seller Net Sheet Calculator: Sioux Falls, SD | Marcos Diaz', 'Calculadora para vendedores en Sioux Falls, SD | Marcos Diaz'),
         T(es, 'Free seller net sheet calculator for Sioux Falls, Tea, Harrisburg and Brandon. Estimate your cash at closing after payoff, commissions and the SD transfer fee.',
              'Calculadora gratis para vendedores en Sioux Falls. Calcule cuánto dinero le queda al cierre después de la hipoteca, comisiones y la tarifa de transferencia.'),
         body, lang='es' if es else 'en', canonical=f'{SITE}/{path[:-10]}',
         alt_es=None if es else other, alt_en=other if es else None, head_extra=alts(key))

for es in (False, True):
    afford(es); net(es)

# sitemap
sm = open(f'{ROOT}/sitemap.xml').read()
for key in PAGES:
    en, esu = PAGES[key]['en'][:-10], PAGES[key]['es'][:-10]
    for u in (en, esu):
        if f'<loc>{SITE}/{u}</loc>' in sm: continue
        sm = sm.replace('</urlset>', f'''  <url>
    <loc>{SITE}/{u}</loc>
    <lastmod>2026-11-06</lastmod>
    <priority>0.8</priority>
    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/{en}"/>
    <xhtml:link rel="alternate" hreflang="es" href="{SITE}/{esu}"/>
  </url>
</urlset>''')
open(f'{ROOT}/sitemap.xml', 'w').write(sm)
print('calcs done')
