# Spanish-first resource pages: ITIN mortgages and buying with low credit (ES + EN)
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'build_pages.py')).read().split('# ---------------- PRIVACY (EN)')[0])
SITE = 'https://605homesearch.com'

def card(title, body, tag=''):
    t = f'<span class="dpa-tag">{tag}</span>' if tag else ''
    return f'        <div class="dpa-card">{t}<h3>{title}</h3>{body}</div>\n'

def faq_ld(pairs):
    import json, re
    strip = lambda s: re.sub('<[^>]+>', '', s)
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in pairs]}, ensure_ascii=False) + '</script>\n'

def build(spec, es):
    S = spec['es' if es else 'en']
    path = (spec['es_path'] if es else spec['en_path'])
    p = '../' * path.count('/')
    home = p + ('es/' if es else '')
    other = p + (spec['en_path'] if es else spec['es_path'])
    T = lambda e, s: s if es else e
    cards = ''.join(card(*c) for c in S['cards'])
    steps = ''.join(f'<li>{x}</li>' for x in S['steps'])
    faqs = ''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in S['faq'])
    body = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{home}">{T('Home','Inicio')}</a> &nbsp;/&nbsp; {S['crumb']}</p>
      <h1>{S['h1']}</h1>
      <p class="lead">{S['lead']}</p>
      <p class="hero-search"><a href="{home}#contact" class="btn btn-gold">{T('Talk to Marcos','Hablar con Marcos')}</a></p>
      <p class="post-meta"><a href="{other}">{T('Ver en español','View in English')}</a></p>
    </div>
  </section>
  <section class="page-body dpa">
    <div class="wrap">
      <div class="prose">{S['intro']}</div>
      <h2>{S['cards_h']}</h2>
      <div class="dpa-grid">
{cards}      </div>
      <div class="dpa-steps">
        <h2>{T('Your next steps','Sus próximos pasos')}</h2>
        <ol>{steps}</ol>
        <div class="dpa-cta">
          <a href="{home}#contact" class="btn btn-navy">{T('Talk to Marcos','Hablar con Marcos')}</a>
          <a href="sms:+16058389140" class="btn btn-gold">{T('Text 605-838-9140','Mensaje al 605-838-9140')}</a>
          <a href="{p}{'es/clase-para-compradores/' if es else 'homebuyer-class/'}" class="calc-link dark">{T('Free homebuyer class in Spanish →','Clase gratis para compradores →')}</a>
          <a href="{p}{'es/ayuda-pago-inicial/' if es else 'down-payment-assistance/'}" class="calc-link dark">{T('Down payment help programs →','Programas de ayuda para el pago inicial →')}</a>
        </div>
      </div>
      <h2>{T('Common questions','Preguntas frecuentes')}</h2>
      <div class="faq-list">{faqs}</div>
      <p class="fine dpa-src">{S['src']}</p>
    </div>
  </section>'''
    alts = (f'<link rel="alternate" hreflang="en" href="{SITE}/{spec["en_path"]}">\n<link rel="alternate" hreflang="es" href="{SITE}/{spec["es_path"]}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/{spec["en_path"]}">\n') + faq_ld(S['faq'])
    page(path + 'index.html', S['title'], S['desc'], body, lang='es' if es else 'en', canonical=f'{SITE}/{path}',
         alt_es=None if es else other, alt_en=other if es else None, head_extra=alts)

ITIN = dict(en_path='itin-mortgage-sioux-falls/', es_path='es/prestamo-itin-sioux-falls/',
 es=dict(
  title='Préstamo ITIN en Sioux Falls: cómo comprar casa sin número de Seguro Social | Marcos Diaz',
  desc='¿Se puede comprar casa en Sioux Falls con ITIN? Sí. Requisitos, documentos, pago inicial y prestamistas locales. Agente de bienes raíces que habla español.',
  crumb='Préstamo ITIN', h1='Comprar casa en Sioux Falls con ITIN',
  lead='Sí, se puede comprar casa sin número de Seguro Social. Le explico cómo funciona un préstamo ITIN, en español y paso a paso.',
  intro='<p>El <b>ITIN</b> (Número de Identificación Personal del Contribuyente) lo emite el IRS para personas que pagan impuestos y no tienen número de Seguro Social. Algunos bancos ofrecen hipotecas para personas con ITIN. No son préstamos del gobierno (FHA, VA o USDA): cada banco pone sus propias reglas, tasas y requisitos.</p><p>En el área de Sioux Falls hay al menos un banco local, <b>Sunrise Banks</b>, que anuncia hipotecas ITIN para Sioux Falls y sus alrededores, con asesores que hablan español. Yo le ayudo a encontrar el prestamista correcto y a buscar casa con confianza.</p>',
  cards_h='Lo que normalmente piden',
  cards=[
   ('Su ITIN vigente','<p>Un número ITIN activo del IRS. Si se venció, renuévelo antes de solicitar.</p>'),
   ('Declaraciones de impuestos','<p>Normalmente sus <b>últimos dos años</b> de declaraciones de impuestos federales presentadas con su ITIN.</p>'),
   ('Pago inicial','<p>Se requiere un pago inicial (enganche). La cantidad depende del banco; suele ser más alta que en un préstamo FHA. Pregunte si puede combinarlo con programas de ayuda.</p>'),
   ('Historial de pagos','<p>Algunos bancos aceptan crédito tradicional y otros revisan pagos de renta, servicios o teléfono. Algunos ofrecen programas para construir crédito.</p>'),
   ('Documentos de ingreso','<p>Talones de pago, W-2 o comprobantes de su negocio, estados de cuenta bancarios e identificación.</p>'),
   ('Clase para compradores','<p>Muchos programas piden una clase de educación para compradores antes de cerrar.</p>'),
  ],
  steps=['Junte sus declaraciones de impuestos con ITIN y sus estados de cuenta de los últimos meses.',
         'Hable con un prestamista que ofrezca préstamos ITIN y obtenga su preaprobación.',
         'Conozca su presupuesto real: pago mensual, impuestos de la propiedad y seguro.',
         'Busque casa conmigo. Le explico cada documento en español antes de firmar.'],
  faq=[('¿Puedo comprar casa en Sioux Falls sin número de Seguro Social?','Sí. Algunos bancos ofrecen préstamos hipotecarios para personas con ITIN. Las reglas y tasas cambian según el banco.'),
       ('¿Cuánto necesito de pago inicial con un préstamo ITIN?','Depende del banco. Suele ser más que en un préstamo FHA. Su prestamista le dará la cantidad exacta según su situación.'),
       ('¿Las tasas de un préstamo ITIN son más altas?','A menudo sí, porque el banco guarda el préstamo y asume el riesgo. Más adelante, algunas personas refinancian a una tasa mejor.'),
       ('¿Usted habla español durante todo el proceso?','Sí. Le acompaño en español desde la primera llamada hasta el día del cierre.')],
  src='Fuentes: Sunrise Banks, programa Pathway2Home ITIN (sunrisebanks.com); IRS, información sobre el ITIN (irs.gov). Actualizado en noviembre de 2026. Esto es información general, no una oferta de préstamo; cada banco fija sus propios requisitos. Marcos Diaz no es prestamista.',
 ),
 en=dict(
  title='ITIN Mortgage in Sioux Falls: Buying a Home Without a Social Security Number | Marcos Diaz',
  desc='Can you buy a home in Sioux Falls with an ITIN? Yes. Requirements, documents, down payment and local lenders, explained by bilingual REALTOR® Marcos Diaz.',
  crumb='ITIN Mortgage', h1='Buying a Home in Sioux Falls with an ITIN',
  lead='Yes, you can buy a home without a Social Security number. Here is how an ITIN mortgage works, step by step.',
  intro='<p>An <b>ITIN</b> (Individual Taxpayer Identification Number) is issued by the IRS to people who pay taxes but don\'t have a Social Security number. Some banks offer mortgages to ITIN holders. These are not government loans (FHA, VA or USDA): each bank sets its own rules, rates and requirements.</p><p>In the Sioux Falls area, at least one local bank, <b>Sunrise Banks</b>, advertises ITIN mortgages for Sioux Falls and the surrounding area, with bilingual loan officers. I\'ll help you find the right lender and shop with confidence.</p>',
  cards_h='What lenders usually ask for',
  cards=[
   ('A current ITIN','<p>An active ITIN from the IRS. If it expired, renew it before you apply.</p>'),
   ('Tax returns','<p>Usually your <b>two most recent years</b> of federal tax returns filed with your ITIN.</p>'),
   ('Down payment','<p>A down payment is required. The amount depends on the bank and is usually higher than an FHA loan. Ask if it can be combined with assistance programs.</p>'),
   ('Payment history','<p>Some banks use traditional credit; others review rent, utility or phone payments. Some offer credit-builder programs.</p>'),
   ('Income documents','<p>Pay stubs, W-2s or business records, bank statements and ID.</p>'),
   ('Homebuyer class','<p>Many programs require a homebuyer education class before closing.</p>'),
  ],
  steps=['Gather your ITIN tax returns and recent bank statements.',
         'Talk to a lender that offers ITIN loans and get pre-approved.',
         'Know your real budget: monthly payment, property taxes and insurance.',
         'Shop for homes with me. I explain every document in English or Spanish before you sign.'],
  faq=[('Can I buy a house in Sioux Falls without a Social Security number?','Yes. Some banks offer mortgages to people with an ITIN. Rules and rates vary by bank.'),
       ('How much down payment do I need for an ITIN loan?','It depends on the lender and is usually more than an FHA loan. Your lender will give you the exact amount.'),
       ('Are ITIN mortgage rates higher?','Often yes, because the bank keeps the loan and takes on the risk. Some buyers refinance to a better rate later.'),
       ('Do you work in Spanish?','Yes. I can guide you in Spanish or English from the first call to closing day.')],
  src='Sources: Sunrise Banks Pathway2Home ITIN program (sunrisebanks.com); IRS ITIN information (irs.gov). Updated November 2026. General information, not a loan offer; each lender sets its own requirements. Marcos Diaz is not a lender.',
 ))

CREDIT = dict(en_path='buy-a-home-with-low-credit/', es_path='es/comprar-casa-con-poco-credito/',
 es=dict(
  title='Comprar casa con poco crédito o mal crédito en Sioux Falls | Marcos Diaz',
  desc='¿Se puede comprar casa con mal crédito o sin crédito? Puntajes mínimos de FHA, VA y convencional, y cómo subir su crédito. Agente que habla español en Sioux Falls.',
  crumb='Comprar con poco crédito', h1='Comprar casa con poco crédito o mal crédito',
  lead='Muchas personas creen que necesitan crédito perfecto para comprar casa. No es así. Esto es lo que realmente piden los préstamos más comunes.',
  intro='<p>Su puntaje de crédito ayuda a decidir qué préstamo puede usar, cuánto pago inicial necesita y su tasa de interés. Pero hay opciones para casi cada situación, y muchas veces unos meses de buenos hábitos hacen una gran diferencia.</p>',
  cards_h='Puntajes de crédito por tipo de préstamo',
  cards=[
   ('FHA','<p>Las reglas de FHA permiten <b>580 o más con 3.5% de pago inicial</b>, o <b>500 a 579 con 10%</b>. Muchos bancos piden un poco más, así que vale la pena comparar.</p>','Más flexible'),
   ('Convencional','<p>Normalmente se pide alrededor de <b>620 o más</b>. Con mejor crédito, la tasa y el seguro hipotecario suelen bajar.</p>'),
   ('VA','<p>Para veteranos y militares. El VA no fija un mínimo, pero cada banco pone el suyo (muchas veces alrededor de 620).</p>'),
   ('Sin historial de crédito','<p>Algunos prestamistas aceptan pagos de renta, servicios o teléfono para demostrar que usted paga a tiempo.</p>'),
   ('¿Tiene ITIN?','<p>Hay préstamos para personas con ITIN y sin número de Seguro Social. <a href="../prestamo-itin-sioux-falls/">Vea cómo funciona →</a></p>'),
  ],
  steps=['Revise su reporte de crédito gratis en annualcreditreport.com y corrija cualquier error.',
         'Pague todas sus cuentas a tiempo y baje los saldos de sus tarjetas (idealmente menos del 30% del límite).',
         'No abra cuentas nuevas ni compre carro antes de comprar casa.',
         'Hable con un prestamista: le dirá exactamente qué mejorar y cuánto tiempo tomará.'],
  faq=[('¿Cuál es el crédito mínimo para comprar casa?','Con FHA, las reglas permiten desde 500 con 10% de pago inicial, o 580 con 3.5%. Muchos bancos piden más, como 620.'),
       ('¿Puedo comprar casa sin historial de crédito?','A veces sí. Algunos prestamistas aceptan pagos de renta, servicios o teléfono como historial.'),
       ('¿Cuánto tiempo tarda en subir mi crédito?','Depende de su situación. Muchas personas ven cambios en unos meses pagando a tiempo y bajando saldos.'),
       ('¿Me puede ayudar en español?','Sí. Le explico todo en español y le presento a una prestamista bilingüe.')],
  src='Fuentes: guías de FHA/HUD sobre puntaje mínimo (Manual HUD 4000.1); annualcreditreport.com. Actualizado en noviembre de 2026. Información general; cada prestamista fija sus propios requisitos.',
 ),
 en=dict(
  title='Buying a Home with Low or Bad Credit in Sioux Falls | Marcos Diaz',
  desc='Can you buy a house with bad credit or no credit? Minimum scores for FHA, VA and conventional loans, and how to raise your score. Sioux Falls REALTOR® Marcos Diaz.',
  crumb='Buying with Low Credit', h1='Buying a Home with Low or Bad Credit',
  lead='Many people think they need perfect credit to buy a home. They don\'t. Here is what the most common loans actually ask for.',
  intro='<p>Your credit score helps decide which loan you can use, how much you put down and your interest rate. But there are options for almost every situation, and a few months of good habits can make a big difference.</p>',
  cards_h='Credit scores by loan type',
  cards=[
   ('FHA','<p>FHA rules allow <b>580+ with 3.5% down</b>, or <b>500–579 with 10% down</b>. Many lenders set a slightly higher minimum, so it pays to compare.</p>','Most flexible'),
   ('Conventional','<p>Usually around <b>620 or higher</b>. Better credit usually means a lower rate and cheaper mortgage insurance.</p>'),
   ('VA','<p>For veterans and service members. The VA has no set minimum, but lenders set their own (often around 620).</p>'),
   ('No credit history','<p>Some lenders accept rent, utility or phone payments to show you pay on time.</p>'),
   ('Have an ITIN?','<p>There are loans for ITIN holders without a Social Security number. <a href="../itin-mortgage-sioux-falls/">See how it works →</a></p>'),
  ],
  steps=['Check your credit report free at annualcreditreport.com and dispute any errors.',
         'Pay every bill on time and pay card balances down (ideally under 30% of the limit).',
         'Don\'t open new accounts or buy a car right before buying a home.',
         'Talk to a lender: they\'ll tell you exactly what to improve and how long it may take.'],
  faq=[('What is the minimum credit score to buy a house?','FHA rules allow from 500 with 10% down, or 580 with 3.5% down. Many lenders ask for more, such as 620.'),
       ('Can I buy a house with no credit history?','Sometimes. Some lenders accept rent, utility or phone payments as history.'),
       ('How long does it take to raise my credit score?','It depends. Many people see changes within a few months by paying on time and lowering balances.'),
       ('Can you help in Spanish?','Yes. I work in English and Spanish and can introduce you to a bilingual lender.')],
  src='Sources: FHA/HUD credit score guidelines (HUD Handbook 4000.1); annualcreditreport.com. Updated November 2026. General information; each lender sets its own requirements.',
 ))

for spec in (ITIN, CREDIT):
    for es in (False, True):
        build(spec, es)

sm = open(f'{ROOT}/sitemap.xml').read()
for spec in (ITIN, CREDIT):
    for u in (spec['en_path'], spec['es_path']):
        if f'<loc>{SITE}/{u}</loc>' in sm: continue
        sm = sm.replace('</urlset>', f'''  <url>
    <loc>{SITE}/{u}</loc>
    <lastmod>2026-11-06</lastmod>
    <priority>0.8</priority>
    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/{spec['en_path']}"/>
    <xhtml:link rel="alternate" hreflang="es" href="{SITE}/{spec['es_path']}"/>
  </url>
</urlset>''')
open(f'{ROOT}/sitemap.xml', 'w').write(sm)
print('resources done')
