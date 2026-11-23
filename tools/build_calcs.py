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

AFFORD_CSS = '''<style>
  .af { background: var(--ivory); padding: 70px 0 90px; }
  .af-grid { display: grid; grid-template-columns: 7fr 5fr; gap: 56px; align-items: start; }
  .af-in h2 { margin-bottom: 6px; }
  .af-sub { color: var(--text); margin-bottom: 26px; }
  .af-f { margin-bottom: 26px; }
  .af-f label { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: .72rem; letter-spacing: .2em; text-transform: uppercase; color: var(--gold-ink); font-weight: 500; margin-bottom: 6px; }
  .af-f input[type=text], .af-f input[type=number], .af-f select { font: inherit; font-size: 1.35rem; font-weight: 400; color: var(--ink); background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 10px 14px; width: 100%; }
  .af-f input:focus, .af-f select:focus { outline: 2px solid var(--gold); border-color: var(--gold); }
  .af-row { display: grid; grid-template-columns: 1fr; gap: 10px; }
  .af-f input[type=range] { width: 100%; accent-color: var(--gold); height: 30px; cursor: pointer; }
  .af-hint { font-size: .85rem; color: #6b665b; margin-top: 4px; }
  .af-tune { border-top: 1px solid var(--line); padding-top: 14px; margin-top: 8px; }
  .af-tune summary { cursor: pointer; font-weight: 500; color: var(--ink); list-style: none; display: flex; align-items: center; gap: 8px; }
  .af-tune summary::-webkit-details-marker { display: none; }
  .af-tune .af-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 18px; }
  .af-tune .af-f input { font-size: 1.1rem; }
  .af-rate { font-size: .85rem; color: var(--text); margin-top: 6px; }
  .af-note { font-size: .82rem; color: #6b665b; margin-top: 18px; }
  .af-out { background: var(--navy); color: #d9d2c6; padding: 34px 32px; border-radius: 18px; position: sticky; top: 100px; }
  .af-tabs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; background: rgba(255,255,255,.07); border-radius: 12px; padding: 5px; margin-bottom: 22px; }
  .af-tabs button { font: inherit; color: #d9d2c6; background: none; border: 0; border-radius: 9px; padding: 8px 4px; cursor: pointer; line-height: 1.25; }
  .af-tabs button b { display: block; color: #fff; font-weight: 500; font-size: 1.05rem; }
  .af-tabs button span { font-size: .78rem; }
  .af-tabs button.on { background: var(--gold-btn); color: #fff; }
  .af-tabs button.on span { color: #fff; }
  .af-label { font-size: .72rem; letter-spacing: .24em; text-transform: uppercase; color: var(--gold-soft); }
  .af-price { font-family: var(--serif); font-size: clamp(3rem, 6vw, 4.2rem); color: #fff; line-height: 1.05; margin: 4px 0 6px; }
  .af-what { font-size: .92rem; margin-bottom: 18px; }
  .af-lines { display: grid; gap: 8px; padding: 16px 0; border-top: 1px solid rgba(255,255,255,.12); border-bottom: 1px solid rgba(255,255,255,.12); margin-bottom: 18px; }
  .af-lines div { display: flex; justify-content: space-between; gap: 12px; }
  .af-lines dd { color: #fff; margin: 0; }
  .af-lines .big dd, .af-lines .big dt { color: #fff; font-weight: 500; }
  .af-btn { display: block; text-align: center; text-decoration: none; border-radius: 10px; padding: 14px; font-weight: 500; font-size: 1rem; margin-top: 10px; }
  .af-b1 { background: var(--gold-btn); color: #fff !important; }
  .af-b1:hover { background: var(--gold-ink); }
  .af-b2 { background: #fff; color: var(--navy) !important; }
  .af-b3 { border: 1px solid rgba(255,255,255,.4); color: #fff !important; }
  .af-dpa { background: rgba(215,180,140,.14); border: 1px solid rgba(215,180,140,.45); border-radius: 12px; padding: 12px 14px; margin: 16px 0 4px; font-size: .92rem; color: #f3e6d4; }
  .af-dpa a { color: var(--gold-soft); }
  .af-warn { background: rgba(243,214,180,.12); border-radius: 10px; padding: 12px 14px; font-size: .92rem; color: #f3d6b4; margin-bottom: 14px; }
  @media (max-width: 900px) {
    .af { padding: 40px 0 70px; }
    .af-grid { grid-template-columns: 1fr; gap: 30px; }
    .af-out { position: static; padding: 28px 22px; }
    .af-tune .af-3 { grid-template-columns: 1fr; }
  }
</style>'''

AFFORD_JS = r'''<script>
(function () {
  var c = document.getElementById('afCalc'); if (!c) return;
  var ES = document.documentElement.lang === 'es', LOC = ES ? 'es-US' : 'en-US';
  var SEARCH = c.dataset.search, DPA = c.dataset.dpa;
  var $ = function (n) { return c.querySelector('[name="' + n + '"]'); };
  var out = function (k) { return c.querySelector('[data-out="' + k + '"]'); };
  var num = function (el) { return parseFloat(String(el.value).replace(/[^0-9.]/g, '')) || 0; };
  var money = function (v) { return '$' + Math.round(Math.max(v, 0)).toLocaleString(LOC); };
  var k3 = function (v) { return v >= 1e6 ? '$' + (v / 1e6).toFixed(2).replace(/0$/, '') + 'M' : '$' + Math.round(v / 1000) + 'K'; };
  var DTI = [36, 43, 45], pick = 0, rateTouched = false;

  // keep number boxes and sliders in step; format with commas
  ['income', 'debts', 'down'].forEach(function (n) {
    var box = $(n), sl = c.querySelector('[data-slider="' + n + '"]');
    box.addEventListener('input', function () { sl.value = num(box); update(); });
    box.addEventListener('blur', function () { box.value = Math.round(num(box)).toLocaleString(LOC); });
    sl.addEventListener('input', function () { box.value = Number(sl.value).toLocaleString(LOC); update(); });
  });
  $('rate').addEventListener('input', function () { rateTouched = true; });
  c.addEventListener('input', update); c.addEventListener('change', update);
  c.querySelectorAll('.af-tabs button').forEach(function (b, i) {
    b.addEventListener('click', function () { pick = i; update(); });
  });

  function solve(dti) {
    var income = num($('income')), debts = num($('debts')), down = num($('down'));
    var rate = num($('rate')), taxPct = num($('tax')) / 100, ins = num($('insurance'));
    var maxPay = income / 12 * dti / 100 - debts;
    var r = rate / 100 / 12, n = 360, k = r === 0 ? 1 / n : r / (1 - Math.pow(1 + r, -n));
    var price = 0, pmiRate = 0.005;
    for (var i = 0; i < 3; i++) {
      var pm = price > 0 && down / price >= 0.2 ? 0 : pmiRate;
      price = Math.max((maxPay - ins / 12 + down * (k + pm / 12)) / (k + taxPct / 12 + pm / 12), 0);
    }
    var pmi = price > 0 && down / price >= 0.2 ? 0 : pmiRate;
    price = Math.floor(price / 1000) * 1000;
    var loan = Math.max(price - down, 0), pi = loan * k;
    var tax = price * taxPct / 12, insm = ins / 12, pmim = loan * pmi / 12;
    return { ok: maxPay > ins / 12 && price > down, price: price, loan: loan, pi: pi, tax: tax, ins: insm, pmi: pmim, pay: pi + tax + insm + pmim, down: down, income: income, debts: debts };
  }

  function update() {
    var all = DTI.map(solve);
    c.querySelectorAll('.af-tabs button').forEach(function (b, i) {
      b.classList.toggle('on', i === pick);
      b.querySelector('b').textContent = all[i].ok ? k3(all[i].price) : '—';
    });
    var s = all[pick];
    out('price').textContent = s.ok ? money(s.price) : '$0';
    out('pay').textContent = s.ok ? money(s.pay) : '$0';
    out('pi').textContent = s.ok ? money(s.pi) : '$0';
    out('tax').textContent = s.ok ? money(s.tax) : '$0';
    out('ins').textContent = s.ok ? money(s.ins) : '$0';
    out('pmi').textContent = s.ok ? money(s.pmi) : '$0';
    out('pmirow').hidden = !(s.ok && s.pmi > 0);
    out('downpct').textContent = s.ok && s.price ? (s.down / s.price * 100).toFixed(1) + '%' : '0%';
    out('warn').hidden = s.ok;
    out('what').textContent = [
      ES ? 'Deja más espacio para ahorros y gastos de la casa.' : 'Leaves room for savings and surprise repairs.',
      ES ? 'Lo que muchos prestamistas aprueban.' : 'What many lenders will approve.',
      ES ? 'El máximo para muchos préstamos. Presupuesto apretado.' : 'The top of what many loans allow. Tight budget.'
    ][pick];
    // search button
    var sb = out('search');
    sb.hidden = !s.ok;
    sb.href = SEARCH + '?maxprice=' + s.price;
    sb.textContent = (ES ? 'Ver casas hasta ' : 'See homes up to ') + money(s.price);
    // down payment help
    var dpa = s.ok && s.price <= 410000 && s.income <= 144760;
    out('dpa').hidden = !dpa;
    if (dpa) out('dpaamt').textContent = money(s.loan * 0.05);
    // text Marcos with their numbers
    var msg = ES
      ? 'Hola Marcos, usé su calculadora. Ingreso: ' + money(s.income) + ' al año. Deudas: ' + money(s.debts) + ' al mes. Ahorros: ' + money(s.down) + '. Me dio unos ' + money(s.price) + '. ¿Me ayuda a preaprobarme?'
      : 'Hi Marcos, I used your calculator. Income: ' + money(s.income) + '/yr. Debts: ' + money(s.debts) + '/mo. Saved: ' + money(s.down) + '. It says about ' + money(s.price) + '. Can you help me get pre-approved?';
    out('sms').href = 'sms:+16058389140?&body=' + encodeURIComponent(msg);
  }

  // this week's average rate (updated every Thursday from Freddie Mac)
  fetch('/data/rate.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }).then(function (d) {
    if (!d || !d.rate) return;
    if (!rateTouched) { $('rate').value = d.rate; update(); }
    var dt = new Date(d.date + 'T12:00:00');
    out('ratenote').textContent = (ES ? 'Promedio nacional de 30 años esta semana: ' : "This week's national 30-year average: ") + d.rate + '% (Freddie Mac, ' + dt.toLocaleDateString(LOC, { month: 'short', day: 'numeric', year: 'numeric' }) + '). ' + (ES ? 'Su tasa puede ser diferente.' : 'Your rate may be different.');
  }).catch(function () {});
  update();
})();
</script>'''

def afford(es, preview=False):
    key = 'afford'
    path = ('calculators/affordability-preview/index.html' if preview else PAGES[key]['es' if es else 'en'])
    p = '../' * path.count('/')
    other = p + PAGES[key]['en' if es else 'es'][:-10]
    netlink = p + PAGES['net']['es' if es else 'en'][:-10]
    dpa = p + ('es/blog/give-me-five-ayuda-pago-inicial/' if es else 'blog/give-me-five-down-payment-assistance/')
    search = '/search-preview/' if preview else ('/es/buscar-casas/' if es else '/search/')
    try:
        import json as _j
        rate = str(_j.load(open(f'{ROOT}/data/rate.json'))['rate'])
    except Exception:
        rate = RATE
    def F(name, label, val, mn, mx, step, hint=''):
        return f'''        <div class="af-f">
          <label for="af-{name}">{label}</label>
          <div class="af-row">
            <input type="text" inputmode="numeric" id="af-{name}" name="{name}" value="{val:,}">
            <input type="range" data-slider="{name}" min="{mn}" max="{mx}" step="{step}" value="{val}" aria-label="{label}">
          </div>{f'<p class="af-hint">{hint}</p>' if hint else ''}
        </div>
'''
    body = hero(es, p, T(es, 'How Much House Can I Afford?', '¿Cuánta casa puedo comprar?'),
                T(es, 'Three quick numbers. See your price range, then see homes for sale in that range.',
                  'Tres números rápidos. Vea su rango de precio y luego las casas en venta en ese rango.'), other)
    body += f'''
  <section class="af">
    <div class="wrap af-grid" id="afCalc" data-search="{search}">
      <div class="af-in">
        <p class="eyebrow">{T(es, 'Affordability Calculator', 'Calculadora de presupuesto')}</p>
        <h2>{T(es, 'Your numbers', 'Sus números')}</h2>
        <p class="af-sub">{T(es, 'Type a number or drag the bar.', 'Escriba el número o mueva la barra.')}</p>
{F('income', T(es, 'Household income per year (before taxes)', 'Ingreso del hogar al año (antes de impuestos)'), 75000, 20000, 300000, 1000)}{F('debts', T(es, 'Monthly debt payments', 'Pagos de deudas al mes'), 400, 0, 4000, 25, T(es, 'Car loans, student loans, credit card minimums, child support. Not rent, utilities or groceries.', 'Préstamos de auto, estudiantiles, pagos mínimos de tarjetas, manutención. No incluya renta, servicios ni comida.'))}{F('down', T(es, 'Cash saved for down payment', 'Dinero ahorrado para el pago inicial'), 15000, 0, 150000, 500)}        <details class="af-tune">
          <summary>{T(es, 'Fine-tune (rate, taxes, insurance)', 'Ajustar (tasa, impuestos, seguro)')}</summary>
          <div class="af-3">
            <div class="af-f"><label for="af-rate">{T(es, 'Interest rate %', 'Tasa de interés %')}</label><input type="number" id="af-rate" name="rate" value="{rate}" min="0" max="20" step="0.125"></div>
            <div class="af-f"><label for="af-tax">{T(es, 'Property tax %/yr', 'Impuesto %/año')}</label><input type="number" id="af-tax" name="tax" value="1.2" min="0" max="5" step="0.05"></div>
            <div class="af-f"><label for="af-ins">{T(es, 'Insurance $/yr', 'Seguro $/año')}</label><input type="text" inputmode="numeric" id="af-ins" name="insurance" value="1,800"></div>
          </div>
        </details>
        <p class="af-rate" data-out="ratenote"></p>
        <p class="af-note">{T(es,
          'An estimate only, not a loan approval. It uses a 30-year fixed loan and the share of your income going to all monthly debts: Comfortable 36%, Stretch 43%, Max 45%. It adds an estimated 0.5%/yr mortgage insurance when the down payment is under 20%. Property taxes vary by home. Your lender will give you your real numbers.',
          'Solo es un estimado, no una aprobación de préstamo. Usa un préstamo fijo a 30 años y la parte de su ingreso para todas sus deudas al mes: Cómodo 36%, Apretado 43%, Máximo 45%. Suma un seguro hipotecario estimado de 0.5% al año si el pago inicial es menor al 20%. Los impuestos varían según la casa. Su prestamista le dará sus números reales.')}</p>
      </div>
      <div class="af-out" aria-live="polite">
        <div class="af-tabs" role="group" aria-label="{T(es, 'Budget', 'Presupuesto')}">
          <button type="button" class="on"><b>—</b><span>{T(es, 'Comfortable', 'Cómodo')}</span></button>
          <button type="button"><b>—</b><span>{T(es, 'Stretch', 'Apretado')}</span></button>
          <button type="button"><b>—</b><span>{T(es, 'Max', 'Máximo')}</span></button>
        </div>
        <p class="af-label">{T(es, 'Estimated home price', 'Precio estimado de casa')}</p>
        <p class="af-price" data-out="price">$0</p>
        <p class="af-what" data-out="what"></p>
        <p class="af-warn" data-out="warn" hidden>{T(es, 'Your monthly debts are high compared to your income. A lender can show you ways to improve your numbers.', 'Sus deudas mensuales son altas comparadas con su ingreso. Un prestamista le puede mostrar cómo mejorar sus números.')}</p>
        <dl class="af-lines">
          <div class="big"><dt>{T(es, 'Monthly payment', 'Pago mensual')}</dt><dd data-out="pay">$0</dd></div>
          <div><dt>{T(es, 'Principal &amp; interest', 'Capital e interés')}</dt><dd data-out="pi">$0</dd></div>
          <div><dt>{T(es, 'Property taxes', 'Impuestos')}</dt><dd data-out="tax">$0</dd></div>
          <div><dt>{T(es, 'Home insurance', 'Seguro de casa')}</dt><dd data-out="ins">$0</dd></div>
          <div data-out="pmirow"><dt>{T(es, 'Mortgage insurance', 'Seguro hipotecario')}</dt><dd data-out="pmi">$0</dd></div>
          <div><dt>{T(es, 'Down payment', 'Pago inicial')}</dt><dd data-out="downpct">0%</dd></div>
        </dl>
        <a class="af-btn af-b1" data-out="search" href="{search}">{T(es, 'See homes in my budget', 'Ver casas en mi presupuesto')}</a>
        <a class="af-btn af-b2" data-out="sms" href="sms:+16058389140">{T(es, 'Text Marcos my numbers', 'Enviarle mis números a Marcos')}</a>
        <a class="af-btn af-b3" href="#lender">{T(es, 'Talk to a lender', 'Hablar con un prestamista')}</a>
        <p class="af-dpa" data-out="dpa" hidden>{T(es, 'Buying your first home? You may qualify for <b>Give Me Five</b>: about <b data-out="dpaamt"></b> toward your down payment.', '¿Es su primera casa? Puede calificar para <b>Give Me Five</b>: unos <b data-out="dpaamt"></b> para su pago inicial.')} <a href="{dpa}">{T(es, 'See if you qualify →', 'Vea si califica →')}</a></p>
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
  </section>
{AFFORD_JS}'''
    extra = AFFORD_CSS + '\n' + ('<meta name="robots" content="noindex, nofollow">\n' if preview else alts(key))
    page(path, T(es, 'How Much House Can I Afford? Sioux Falls Calculator | Marcos Diaz', '¿Cuánta casa puedo comprar? Calculadora Sioux Falls | Marcos Diaz'),
         T(es, 'Free home affordability calculator for Sioux Falls buyers. Enter your income, debts and down payment to see your price range and homes for sale in it.',
              'Calculadora gratis para compradores en Sioux Falls. Escriba su ingreso, deudas y pago inicial para ver su rango de precio y casas en venta.'),
         body, lang='es' if es else 'en', canonical=f'{SITE}/{PAGES[key]["es" if es else "en"][:-10]}',
         alt_es=None if es else other, alt_en=other if es else None, head_extra=extra)

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

import sys
if '--preview' in sys.argv:
    afford(False, preview=True); print('preview done'); sys.exit()
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
