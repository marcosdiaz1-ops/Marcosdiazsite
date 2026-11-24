# Builds the ad landing pages (for Meta / Facebook / Instagram ads) in English and Spanish.
# Run: python3 tools/build_landing_pages.py   → writes lp/<page>/index.html and es/lp/<page>/index.html
#
# Each page has one job and one form. No menu, so ad visitors don't wander off.
# Pages are hidden from Google (noindex) and left out of the sitemap, so they don't compete with the main pages.
# Leads go to the same Website Leads sheet + email alert + auto-reply as the main contact form.
# Use links like https://605homesearch.com/lp/first-home/?utm_source=facebook&utm_campaign=first-home
# so the lead is tagged "FB ad" in the sheet.
import os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET = 'https://script.google.com/macros/s/AKfycbw5PdoEEaGDAquTmKqO_1SkhtTaJG3G0584Xy4VIqG74FsaaH-tnxYpeIdrqTcCjZ0w/exec'
KEY = 'd0023d26-ed18-4970-8a35-c3de9e5f7e6c'


def legal(es):
    src = open(os.path.join(ROOT, 'es/valor-de-casa/index.html' if es else 'home-value/index.html')).read()
    block = re.search(r'<div class="wrap legal">.*?</div>\s*</footer>', src, re.S).group(0)
    priv = '/es/privacidad.html' if es else '/privacy.html'
    block = re.sub(r'<a href="[^"]*privac[^"]*">', f'<a href="{priv}">', block)
    return block


LP_JS = '''<script>
// Put the extra answers into the lead sheet's Notes column (the sheet only has Looking to / Timeline / Notes)
document.getElementById('leadForm').addEventListener('wizard:submit', function (e) {
  var fd = e.detail.fd, bits = ['Ad page ' + fd.get('Page')];
  ['Area', 'Price range', 'Pre-approved', 'Address'].forEach(function (k) { if (fd.get(k)) bits.push(k + ': ' + fd.get(k)); });
  var c = new URLSearchParams(location.search).get('utm_campaign'); if (c) bits.push('Campaign: ' + c.slice(0, 40));
  fd.set('message', bits.join(' · '));
  if (!fd.get('Timeline') && fd.get('Price range')) fd.set('Timeline', 'Price: ' + fd.get('Price range'));
});
</script>
'''

CSS = '''<style>
.lp-header{position:absolute;top:0;left:0;right:0;z-index:5;padding:18px 0}
.lp-header .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px}
.lp-header .brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:#fff}
.lp-call{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.5);border-radius:999px;padding:8px 16px;font-size:.95rem;white-space:nowrap}
.lp .hv-hero{padding-top:110px}
.lp-trust{display:flex;flex-wrap:wrap;gap:8px 18px;margin:18px 0 0;padding:0;list-style:none;color:#e6e0d4;font-size:.92rem}
.lp-trust li::before{content:"★ ";color:var(--gold-soft)}
.lp .site-footer{padding-top:28px}
@media (max-width:760px){.lp .hv-hero{padding-top:84px}.lp .hv-hero .hv-points{display:grid;margin:14px 0}.lp .hv-hero h1{font-size:2.1rem}.lp-header .brand-text small{display:none}}
</style>'''

FINE = {
    False: ('By sending, you agree that Marcos Diaz may contact you by call, text or email at the phone and email you gave, which may include automated messages. '
            'Consent is not required to buy or sell a home. Message and data rates may apply. Reply STOP to opt out of texts.',
            'Free and no obligation. Your information goes only to me and is never sold. <a href="/privacy.html">Privacy notice</a>'),
    True: ('Al enviar, acepta que Marcos Diaz le contacte por llamada, mensaje de texto o correo al teléfono y correo que proporcionó, lo cual puede incluir mensajes automatizados. '
           'Su consentimiento no es requisito para comprar o vender una casa. Pueden aplicar tarifas de mensajes y datos. Responda STOP para dejar de recibir textos.',
           'Gratis y sin compromiso. Su información es solo para mí y nunca se vende. <a href="/es/privacidad.html">Aviso de privacidad</a>'),
}


def choices(name, opts):
    return '<div class="choices">' + ''.join(
        f'<label class="choice"><input type="radio" name="{name}" value="{html.escape(v)}"><span><strong>{a}</strong><small>{b}</small></span></label>'
        for v, a, b in opts) + '</div>'


def page(es, slug, other, p):
    L = (lambda en, sp: sp if es else en)
    back = L('← Back', '← Atrás'); cont = L('Continue', 'Continuar')
    steps = []
    n = len(p['steps']) + 1
    for k, st in enumerate(p['steps']):
        left = '<span></span>' if k == 0 else f'<button type="button" class="btn-back back">{back}</button>'
        steps.append(f'''        <fieldset class="step{' active' if k == 0 else ''}" data-step="{k + 1}">
          <legend>{st['q']}</legend>
          {st['body']}
          <div class="nav-btns">{left}<button type="button" class="btn btn-gold next" disabled>{cont}</button></div>
        </fieldset>''')
    fine1, fine2 = FINE[es]
    steps.append(f'''        <fieldset class="step" data-step="{n}">
          <legend>{p['last_q']}</legend>
          <label class="full">{L('First &amp; last name', 'Nombre y apellido')}<input type="text" name="Name" autocomplete="name" required></label>
          <div class="two">
            <label>{L('Phone', 'Teléfono')}<input type="tel" name="Phone" autocomplete="tel" required></label>
            <label>{L('Email', 'Correo electrónico')}<input type="email" name="email" autocomplete="email" required></label>
          </div>
          <p class="error" role="alert"></p>
          <div class="nav-btns"><button type="button" class="btn-back back">{back}</button><button type="submit" class="btn btn-gold">{p['button']}</button></div>
          <p class="fine">{fine1}</p>
          <p class="fine">{fine2}</p>
        </fieldset>''')
    lang = 'es' if es else 'en'
    url = f'https://605homesearch.com/{"es/" if es else ""}lp/{slug}/'
    other_url = f'/{"" if es else "es/"}lp/{other}/'
    points = ''.join(f'<li>{x}</li>' for x in p['points'])
    trust = ''.join(f'<li>{x}</li>' for x in L(['5.0 on Google', 'Keller Williams Realty Sioux Falls', 'English &amp; Español'],
                                              ['5.0 en Google', 'Keller Williams Realty Sioux Falls', 'Español e inglés']))
    hidden = ''.join(f'<input type="hidden" name="{html.escape(k)}" value="{html.escape(v)}">' for k, v in p.get('hidden', {}).items())
    kind = p.get('kind', 'ad-' + slug)
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{p['title']}</title>
<meta name="description" content="{p['desc']}">
<meta name="robots" content="noindex, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{p['title']}">
<meta property="og:description" content="{p['desc']}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://605homesearch.com/images/og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="icon" href="/images/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/fonts/fonts.css?v=BUILD">
<link rel="stylesheet" href="/styles.css?v=BUILD">
{CSS}
</head>
<body class="lp">

<header class="lp-header">
  <div class="wrap">
    <a href="{'/es/' if es else '/'}" class="brand">
      <img src="/images/logo.svg" alt="Marcos Diaz MD monogram logo" width="34" height="34">
      <span class="brand-text light">Marcos Diaz<small>Keller Williams Realty Sioux Falls</small></span>
    </a>
    <a class="lp-call" href="tel:+16058389140">{L('Call / Text', 'Llamar / Texto')}</a>
  </div>
</header>

<main>
  <section class="contact hv-hero">
    <div class="wrap contact-grid">
      <div class="contact-text">
        <p class="eyebrow light">{p['eyebrow']}</p>
        <h1>{p['h1']}</h1>
        <p>{p['lead']}</p>
        <ul class="hv-points">{points}</ul>
        <ul class="lp-trust">{trust}</ul>
        <p class="hv-lang"><a href="{other_url}" lang="{'en' if es else 'es'}">{L('Ver en español', 'View in English')}</a></p>
      </div>
      <form action="https://api.web3forms.com/submit" method="POST" class="form wizard" id="leadForm" data-kind="{kind}" data-sheet="{SHEET}" novalidate>
        <input type="hidden" name="access_key" value="{KEY}">
        <input type="hidden" name="subject" value="{html.escape(p['subject'])}">
        <input type="hidden" name="from_name" value="Marcos Diaz Website">
        <input type="hidden" name="Page" value="{'/es' if es else ''}/lp/{slug}/">
        {hidden}
        <input type="checkbox" name="botcheck" class="hidden" tabindex="-1" autocomplete="off">

        <div class="progress" aria-hidden="true"><span></span></div>
        <p class="step-count">{L('Step', 'Paso')} <b>1</b> {L('of', 'de')} {n}</p>

{chr(10).join(steps)}

        <div class="step sent" data-step="{n + 1}" aria-live="polite">
          <div class="check" aria-hidden="true"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24"/><path d="M15 27l7 7 15-16"/></svg></div>
          <h3>{L('Thank you', 'Gracias')}<span class="sent-name"></span>!</h3>
          <p>{p['thanks']}</p>
          <p class="fine">{L('Need me sooner? Call or text', '¿Me necesita antes? Llame o mande un texto al')} <a href="tel:+16058389140">605-838-9140</a>.</p>
        </div>
      </form>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap">
      <div class="hv-steps">
{''.join(f'        <div><span class="step-n">{i + 1}</span><h3>{h}</h3><p>{t}</p></div>' + chr(10) for i, (h, t) in enumerate(p['how']))}      </div>
    </div>
  </section>
</main>

<footer class="site-footer">
  {legal(es)}
{LP_JS}<script src="/site.js?v=BUILD" defer></script>
</body>
</html>
'''


EN_TIMELINE = [('0-3 months', 'In the next 3 months', 'Ready to start looking'), ('3-6 months', '3–6 months', 'Planning ahead'),
               ('6-12 months', '6–12 months', 'Getting ready'), ('Just starting', 'Just starting', 'Learning how it works')]
ES_TIMELINE = [('0-3 months', 'Pronto', 'Listo para buscar'), ('3-6 months', 'En unos meses', 'Planeando'),
               ('6-12 months', 'Este año', 'Preparándome'), ('Just starting', 'Apenas empiezo', 'Quiero aprender')]
EN_PRE = [('Yes', 'Yes', 'I have a pre-approval letter'), ('Not yet', 'Not yet', 'I can help you get started'),
          ('Not sure', 'Not sure', "That's okay")]
ES_PRE = [('Yes', 'Sí', 'Ya tengo mi carta'), ('Not yet', 'Todavía no', 'Le ayudo a empezar'),
          ('Not sure', 'No sé', 'No hay problema')]
EN_AREA = [('Sioux Falls', 'Sioux Falls', 'Any part of town'), ('Tea', 'Tea', ''), ('Harrisburg', 'Harrisburg', ''),
           ('Brandon', 'Brandon', ''), ('Anywhere nearby', 'Open to anywhere', 'Show me it all')]
ES_AREA = [('Sioux Falls', 'Sioux Falls', 'Cualquier parte'), ('Tea', 'Tea', ''), ('Harrisburg', 'Harrisburg', ''),
           ('Brandon', 'Brandon', ''), ('Anywhere nearby', 'Cualquier lugar', 'Muéstreme todo')]
EN_PRICE = [('Under $250k', 'Under $250k', ''), ('$250k–$350k', '$250k–$350k', ''), ('$350k–$500k', '$350k–$500k', ''),
            ('$500k+', '$500k and up', ''), ('Not sure yet', 'Not sure yet', 'I can help you figure it out')]
ES_PRICE = [('Under $250k', 'Menos de $250k', ''), ('$250k–$350k', '$250k–$350k', ''), ('$350k–$500k', '$350k–$500k', ''),
            ('$500k+', 'Más de $500k', ''), ('Not sure yet', 'No sé todavía', 'Le ayudo a calcular')]

PAGES = [
    ('first-home', 'primera-casa', {
        False: dict(
            title='Buy Your First Home in Sioux Falls | Marcos Diaz, Keller Williams',
            desc='Free help buying your first home in Sioux Falls: down payment help, VA loans and a simple plan, in English or Spanish.',
            eyebrow='First-Time Home Buyers', h1='You may need less down than you think.',
            lead='Many first-time buyers in Sioux Falls wait years longer than they need to. I&rsquo;ll show you what you qualify for, the down payment help that&rsquo;s out there, and a simple plan to get the keys.',
            points=['South Dakota down payment help, like Give Me Five', 'VA loans with $0 down for eligible veterans', 'Some loans need as little as 3% down', 'A free plan made for you, with no pressure'],
            steps=[dict(q='When would you like to buy?', body=choices('Timeline', EN_TIMELINE)),
                   dict(q='Are you pre-approved for a loan?', body=choices('Pre-approved', EN_PRE))],
            last_q='Where should I send your free plan?', button='Get My Free Plan',
            subject='New first-time buyer lead (ad page)', hidden={'Looking to': 'Buy: first home'},
            thanks='I&rsquo;ll look over your answers and reach out personally, usually within one business day, with your next steps.',
            how=[('Answer 3 quick questions', 'It takes about 30 seconds.'), ('We talk for 15 minutes', 'I learn what you want and what you can spend.'),
                 ('You get a plan', 'Down payment help, a lender, and homes that fit. All free.')]),
        True: dict(
            title='Compre su primera casa en Sioux Falls | Marcos Diaz, Keller Williams',
            desc='Ayuda gratis para comprar su primera casa en Sioux Falls: ayuda para el pago inicial, préstamos VA y un plan sencillo, en español.',
            eyebrow='Compradores de primera casa', h1='Puede necesitar menos dinero de lo que cree.',
            lead='Muchas personas en Sioux Falls esperan años sin necesidad. Le muestro para qué califica, la ayuda que hay para el pago inicial y un plan sencillo para recibir sus llaves.',
            points=['Ayuda para el pago inicial en Dakota del Sur, como Give Me Five', 'Préstamos VA sin pago inicial para veteranos que califican', 'Algunos préstamos piden muy poco de pago inicial', 'Un plan gratis para usted, sin presión'],
            steps=[dict(q='¿Cuándo le gustaría comprar?', body=choices('Timeline', ES_TIMELINE)),
                   dict(q='¿Ya tiene aprobación para un préstamo?', body=choices('Pre-approved', ES_PRE))],
            last_q='¿A dónde le envío su plan gratis?', button='Recibir mi plan gratis',
            subject='New first-time buyer lead (ad page, ESPAÑOL)', hidden={'Looking to': 'Buy: first home'},
            thanks='Voy a revisar sus respuestas y le contacto personalmente, casi siempre en un día hábil, con sus próximos pasos.',
            how=[('Conteste 3 preguntas', 'Toma menos de un minuto.'), ('Hablamos un rato', 'Conozco lo que busca y lo que puede pagar.'),
                 ('Recibe su plan', 'Ayuda para el pago inicial, un prestamista y casas para usted. Todo gratis.')]),
    }),
    ('home-value', 'valor-de-casa', {
        False: dict(
            title="What's My Sioux Falls Home Worth? Free Report | Marcos Diaz",
            desc='Free, no-obligation home value report based on real recent sales near you, from a local Sioux Falls agent.',
            eyebrow='Free Home Value Report', h1='What&rsquo;s your home worth today?',
            lead='Online estimates can be off by tens of thousands. Get a free report based on real recent sales near you, from a local agent, not an algorithm.',
            points=['Recent sales and active listings near you', 'A realistic price range for today&rsquo;s market', 'Simple tips to get the most when you sell', 'No obligation to list'],
            steps=[dict(q='What&rsquo;s the property address?', body='<label class="full">Street address, city<input type="text" name="Address" autocomplete="street-address" placeholder="123 Main St, Sioux Falls" required></label>'),
                   dict(q='When are you thinking of selling?', body=choices('Timeline', [('Ready to sell now', 'Ready to sell now', "Let's get it on the market"), ('1-3 months', '1–3 months', 'Planning the move now'), ('3-6 months', '3–6 months', 'Getting prepared'), ('Just curious', 'Just curious', 'Want to know my equity')]))],
            last_q='Where should I send your report?', button='Get My Home Value',
            subject='Home value request (ad page)', hidden={'Looking to': 'Home value'}, kind='home-value',
            thanks='I&rsquo;m on it. I&rsquo;ll review recent sales near your home and reach out personally, usually within one business day.',
            how=[('Tell me about your home', 'Share the address and your timeline. About 30 seconds.'), ('I run the numbers', 'Recent sales, active listings and buyer demand near you.'),
                 ('You get your report', 'I walk you through your value and options, with no pressure to list.')]),
        True: dict(
            title='¿Cuánto vale su casa en Sioux Falls? Reporte gratis | Marcos Diaz',
            desc='Reporte gratis y sin compromiso del valor de su casa, basado en ventas reales cerca de usted, de un agente local en Sioux Falls.',
            eyebrow='Reporte gratis del valor de su casa', h1='¿Cuánto vale su casa hoy?',
            lead='Los cálculos en línea pueden fallar por miles de dólares. Reciba un reporte gratis basado en ventas reales cerca de usted, hecho por un agente local.',
            points=['Ventas recientes y casas a la venta cerca de usted', 'Un precio realista para el mercado de hoy', 'Consejos sencillos para ganar más al vender', 'Sin compromiso de vender'],
            steps=[dict(q='¿Cuál es la dirección de la casa?', body='<label class="full">Dirección y ciudad<input type="text" name="Address" autocomplete="street-address" placeholder="123 Main St, Sioux Falls" required></label>'),
                   dict(q='¿Cuándo piensa vender?', body=choices('Timeline', [('Ready to sell now', 'Listo para vender', 'Quiero empezar ya'), ('1-3 months', 'Pronto', 'Planeando la mudanza'), ('3-6 months', 'En unos meses', 'Preparándome'), ('Just curious', 'Solo por curiosidad', 'Quiero saber cuánto vale')]))],
            last_q='¿A dónde le envío su reporte?', button='Recibir mi reporte',
            subject='Home value request (ad page, ESPAÑOL)', hidden={'Looking to': 'Home value'}, kind='home-value',
            thanks='Ya estoy trabajando en su reporte. Reviso las ventas cerca de su casa y le contacto personalmente, casi siempre en un día hábil.',
            how=[('Cuénteme de su casa', 'La dirección y cuándo piensa vender.'), ('Yo hago los números', 'Ventas recientes y casas a la venta cerca de usted.'),
                 ('Recibe su reporte', 'Le explico el valor y sus opciones, sin presión.')]),
    }),
    ('new-listings', 'casas-nuevas', {
        False: dict(
            title='New Sioux Falls Homes for Sale, Sent to You First | Marcos Diaz',
            desc='Get new Sioux Falls, Tea, Harrisburg and Brandon homes sent to you as soon as they hit the market, from a local agent.',
            eyebrow='New Listings', h1='See new Sioux Falls homes before everyone else.',
            lead='Good homes can go fast. Tell me what you want and I&rsquo;ll send you the homes that match as soon as they hit the market, plus a heads-up on homes coming soon.',
            points=['New homes for sale, picked for you', 'Price drops and homes coming soon', 'Help setting up showings any day', 'Free, and you can stop anytime'],
            steps=[dict(q='Where do you want to live?', body=choices('Area', EN_AREA)),
                   dict(q='What price range?', body=choices('Price range', EN_PRICE))],
            last_q='Where should I send the homes?', button='Send Me Homes',
            subject='New home buyer lead: new listings (ad page)', hidden={'Looking to': 'Buy: new listings'},
            thanks='I&rsquo;ll pull the homes that match and reach out personally, usually within one business day. Want to look now? <a href="/search/">Search all homes</a>.',
            how=[('Tell me what you want', 'Area and price. About 30 seconds.'), ('I find the homes', 'Straight from the MLS, including homes coming soon.'),
                 ('You see them first', 'Then we go see the ones you like.')]),
        True: dict(
            title='Casas nuevas en venta en Sioux Falls, primero para usted | Marcos Diaz',
            desc='Reciba las casas nuevas en venta en Sioux Falls, Tea, Harrisburg y Brandon en cuanto salen al mercado, de un agente local.',
            eyebrow='Casas nuevas en venta', h1='Vea las casas nuevas antes que los demás.',
            lead='Las buenas casas se venden rápido. Dígame lo que busca y le mando las casas que le quedan en cuanto salen al mercado.',
            points=['Casas nuevas en venta, escogidas para usted', 'Bajas de precio y casas que vienen pronto', 'Ayuda para ver casas cualquier día', 'Gratis, y puede parar cuando quiera'],
            steps=[dict(q='¿Dónde quiere vivir?', body=choices('Area', ES_AREA)),
                   dict(q='¿Cuánto quiere gastar?', body=choices('Price range', ES_PRICE))],
            last_q='¿A dónde le mando las casas?', button='Mándeme casas',
            subject='New home buyer lead: new listings (ad page, ESPAÑOL)', hidden={'Looking to': 'Buy: new listings'},
            thanks='Voy a buscar las casas que le quedan y le contacto personalmente, casi siempre en un día hábil. ¿Quiere ver ya? <a href="/es/buscar-casas/">Buscar casas</a>.',
            how=[('Dígame lo que busca', 'Lugar y precio. Menos de un minuto.'), ('Yo busco las casas', 'Directo del MLS, también las que vienen pronto.'),
                 ('Usted las ve primero', 'Y vamos a ver las que le gusten.')]),
    }),
]

if __name__ == '__main__':
    for en_slug, es_slug, pp in PAGES:
        for es in (False, True):
            slug, other = (es_slug, en_slug) if es else (en_slug, es_slug)
            out = os.path.join(ROOT, 'es/lp' if es else 'lp', slug, 'index.html')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'w').write(page(es, slug, other, pp[es]))
            print('wrote', os.path.relpath(out, ROOT))
