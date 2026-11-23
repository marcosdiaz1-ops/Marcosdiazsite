"""Google-friendly listing pages, built from the live RASE feed every time the site publishes.

Runs inside .github/workflows/deploy.yml (never committed), only after the new search is live
(the file data/listing-pages-on exists; tools/go_live_search.py creates it).

Makes, from every active listing the feed allows on the internet:
  /homes/<address>-<mlsId>/  and  /es/casas/<address>-<mlsId>/      one page per home (EN + ES)
  /homes-for-sale/<town>/    and  /es/casas-en-venta/<town>/        town pages
     .../<town>/under-300k/, .../<town>/3-bedrooms/                  price and bedroom pages per town
  /homes-for-sale/acreage/, new-construction/, condos-townhomes/, under-300k/ ...   area-wide searches
  /homes-for-sale/neighborhoods/<name>/, /homes-for-sale/school-districts/<name>/
  (every page in English and Spanish; Spanish pages live under /es/casas-en-venta/)
  /homes-sitemap.xml (+ a line in robots.txt) so Google finds them
and points the "See homes for sale" buttons on the area pages at the new town pages.

Test without the feed:  LISTINGS_FILE=sample.json python3 tools/build_listing_pages.py
"""
import os, re, sys, json, html, datetime, urllib.request, urllib.parse, io, contextlib
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path: sys.path.insert(0, HERE)
# Reuse the site's page shell (menu, footer, legal lines) from build_pages.py without running the rest of it
_src = open(os.path.join(HERE, 'build_pages.py')).read().split('# ---------------- PRIVACY (EN)')[0]
_quiet = {'__file__': os.path.join(HERE, 'build_pages.py')}
exec(_src, _quiet)
_page_raw = _quiet['page']
def _page(*a, **k):
    with contextlib.redirect_stdout(io.StringIO()): _page_raw(*a, **k)
_quiet['SEARCH'] = '/search/'

SITE = 'https://605homesearch.com'
API = os.environ.get('LISTINGS_API', 'https://listings.605homesearch.com')
BOOK = 'https://calendly.com/marcosdiaz1-kw/home-showing'
MAX_TOWN_CARDS = 60
ALERTS_URL = 'https://script.google.com/macros/s/AKfycbxklqP-b5JNN1e2hsuwLXQvC0P6_4ZmJBORJLDojLWMwqWiUx5JFn0oiKDVXvu4c-6-/exec'
DPA_LIMIT = 410000  # South Dakota Housing "Give Me Five" purchase price limit
try:
    RATE = float(json.load(open(os.path.join(ROOT, 'data/rate.json')))['rate'])
except Exception:
    RATE = 7.25
DOWN, INS_YR, TAX_PCT = 0.05, 1800, 0.012  # same defaults as the homepage payment calculator

def payment(h):
    """Estimated monthly payment: 5% down, 30-year fixed at this week's average rate, taxes, insurance, HOA."""
    price = h.get('listPrice') or 0
    if not price: return 0
    loan, r, n = price * (1 - DOWN), RATE / 100 / 12, 360
    pi = loan * r / (1 - (1 + r) ** -n)
    tx = (h.get('tax') or {}).get('taxAnnualAmount') or price * TAX_PCT
    ass = h.get('association') or {}
    fee, fq = ass.get('fee') or 0, str(ass.get('frequency') or 'monthly').lower()
    hoa = fee / 12 if 'ann' in fq or 'year' in fq else fee / 3 if 'quarter' in fq else fee
    return int(round((pi + tx / 12 + INS_YR / 12 + hoa) / 10.0) * 10)

def pay_note(es=False):
    if es:
        return (f'Estimado con 5% de enganche y préstamo fijo a 30 años al {RATE}% (promedio nacional de esta semana, Freddie Mac); '
                'incluye impuestos, seguro y cuota HOA si hay. No es una oferta de préstamo ni la APR. Su tasa, APR y pago serán diferentes.')
    return (f'Estimate assumes 5% down and a 30-year fixed loan at {RATE}% (this week’s national average, Freddie Mac), plus taxes, '
            'insurance and any HOA. Not a loan offer or APR. Your rate, APR and payment will be different.')

def is_dpa(h):
    ty = str((h.get('property') or {}).get('type') or '')
    return bool(h.get('listPrice')) and h['listPrice'] <= DPA_LIMIT and not re.search(r'LND|land|MLF|multi', ty, re.I)
e = lambda s: html.escape(str(s if s is not None else ''), quote=True)
money = lambda n: '${:,.0f}'.format(n) if n else ''

# Towns with an area page on the site: feed city name -> (page slug, area page slug)
TOWNS = {
    'Sioux Falls': ('sioux-falls-sd', 'sioux-falls'), 'Tea': ('tea-sd', 'tea'), 'Harrisburg': ('harrisburg-sd', 'harrisburg'),
    'Brandon': ('brandon-sd', 'brandon'), 'Garretson': ('garretson-sd', 'garretson'), 'Hartford': ('hartford-sd', 'hartford'),
    'Crooks': ('crooks-sd', 'crooks'), 'Lennox': ('lennox-sd', 'lennox'), 'Canton': ('canton-sd', 'canton'),
}
AREA_TO_TOWN = {'sioux-falls': 'sioux-falls-sd', 'southwest-sioux-falls': 'sioux-falls-sd', 'southeast-sioux-falls': 'sioux-falls-sd',
                'tea': 'tea-sd', 'harrisburg': 'harrisburg-sd', 'brandon': 'brandon-sd', 'garretson': 'garretson-sd',
                'hartford': 'hartford-sd', 'crooks': 'crooks-sd', 'lennox': 'lennox-sd', 'canton': 'canton-sd'}

SUFFIX = {'rd': 'road', 'dr': 'drive', 'st': 'street', 'ave': 'avenue', 'av': 'avenue', 'ln': 'lane', 'ct': 'court', 'cir': 'circle',
          'pl': 'place', 'blvd': 'boulevard', 'trl': 'trail', 'pkwy': 'parkway', 'ter': 'terrace', 'hwy': 'highway', 'cv': 'cove',
          'pt': 'point', 'sq': 'square', 'xing': 'crossing'}

def clean_addr(full):  # same fix as the search page: "508 E Plum Creek Rd Road" -> "508 E Plum Creek Rd"
    out = []
    for w in str(full or '').split():
        prev = out[-1].rstrip('.').lower() if out else ''
        if prev in SUFFIX and SUFFIX[prev] == w.lower(): continue
        out.append(w)
    return ' '.join(out)

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

# ---------- Get the listings ----------
def fetch_listings():
    if os.environ.get('LISTINGS_FILE'):
        return json.load(open(os.environ['LISTINGS_FILE']))
    out, offset = [], 0
    while True:
        url = API + '/properties?' + urllib.parse.urlencode({'limit': 500, 'offset': offset})
        req = urllib.request.Request(url, headers={'User-Agent': '605homesearch-builder', 'Accept': 'application/json'})
        batch = json.load(urllib.request.urlopen(req, timeout=60))
        out += batch
        if len(batch) < 500 or offset > 20000: break
        offset += 500
    return out

def last_update():
    if os.environ.get('LISTINGS_FILE'): return ''
    try:
        o = json.load(urllib.request.urlopen(urllib.request.Request(API + '/last-update', headers={'User-Agent': '605homesearch-builder'}), timeout=30))
        u = o.get('lastUpdate') or sorted(v for v in (o.get('updates') or {}).values() if v)[-1]
        d = datetime.datetime.fromisoformat(u.replace('Z', '+00:00')).astimezone(datetime.timezone(datetime.timedelta(hours=-6)))
        return d.strftime('%b %-d, %Y at %-I:%M %p') + ' CT'
    except Exception:
        return ''

# ---------- Small helpers ----------
NUM_FIELDS = ('bedrooms', 'bathrooms', 'bathsFull', 'bathsHalf', 'bathsThreeQuarter', 'area', 'acres', 'lotSizeArea', 'garageSpaces', 'yearBuilt', 'stories', 'fireplaces')
def _num(v):
    if isinstance(v, (int, float)) or v is None: return v
    try:
        f = float(str(v).replace(',', '').strip())
        return int(f) if f.is_integer() else f
    except ValueError:
        return None
def numbers(h):
    """The MLS sometimes sends numbers as text ("2.5"); make them real numbers so math and formatting work."""
    p = h.get('property') or {}
    for k in NUM_FIELDS:
        if k in p: p[k] = _num(p[k])
    for k in ('listPrice', 'originalListPrice'):
        if k in h: h[k] = _num(h[k])
    return h

def baths(p):
    b = (p.get('bathsFull') or 0) + (p.get('bathsThreeQuarter') or 0) + 0.5 * (p.get('bathsHalf') or 0)
    b = b or p.get('bathrooms') or 0
    return ('%g' % b) if b else ''

def show_addr(h): return h.get('internetAddressDisplay') is not False

def street(h): return clean_addr((h.get('address') or {}).get('full')) if show_addr(h) else ''

def town_of(h): return ((h.get('address') or {}).get('city') or '').strip().title()

def url_of(h, es=False):
    a = h.get('address') or {}
    base = (street(h) + ' ' if street(h) else 'home ') + f"{town_of(h)} {a.get('state') or 'SD'} {a.get('postalCode') or ''}"
    return ('/es/casas/' if es else '/homes/') + f"{slugify(base)}-{h['mlsId']}/"

def attribution(h):  # RASE IDX Policy 18.2.12: listing firm + listing agent + contact
    ag, of = h.get('agent') or {}, h.get('office') or {}
    name = ' '.join(x for x in [ag.get('firstName'), ag.get('lastName')] if x)
    c = (of.get('contact') or {}); ac = (ag.get('contact') or {})
    contact = c.get('office') or c.get('email') or ac.get('office') or ac.get('email') or ''
    return ' · '.join(x for x in [of.get('name') or of.get('servingName') or '', name, contact] if x)

def lot(p):
    if p.get('lotSizeArea'):
        return '{:,} {}'.format(p['lotSizeArea'], p.get('lotSizeAreaUnits') or ('sq ft' if p['lotSizeArea'] > 200 else 'acres'))
    if p.get('acres'): return '%s acres' % p['acres']
    return ''

def as_list(v): return ', '.join(v) if isinstance(v, list) else (v or '')

# What's special about a home (same rules as the search page), read from its MLS features and description
def highlights(h, es=False):
    p = h.get('property') or {}
    lc = lambda v: (','.join(v) if isinstance(v, list) else str(v or '')).lower()
    x = ' | '.join(lc(v) for v in [p.get('exteriorFeatures'), p.get('interiorFeatures'), p.get('lotDescription'), p.get('fencing'), (p.get('parking') or {}).get('description')])
    r = str(h.get('remarks') or '').lower()
    T2 = lambda en, sp: sp if es else en
    out = []
    if re.search(r'walk-?out', x + ' ' + r): out.append(T2('Walkout basement', 'Sótano con salida'))
    if re.search(r'\bshop\b|pole barn|outbuilding|quonset', x + ' ' + r): out.append(T2('Shop / outbuilding', 'Taller o bodega'))
    if p.get('pool') or re.search(r'\bpool\b', x) or re.search(r'(in-?ground|above-?ground|heated) pool', r): out.append(T2('Pool', 'Alberca'))
    try: ac = float(p.get('acres') or 0)
    except Exception: ac = 0
    if ac >= 1:
        n = round(ac) if ac >= 10 else round(ac, 1)
        out.append(f"{n:g} acre" + ('' if n == 1 else 's'))
    if (p.get('yearBuilt') or 0) >= THIS_YEAR - 1: out.append(T2('New construction', 'Construcción nueva'))
    if (p.get('garageSpaces') or 0) >= 3: out.append(f"{round(p['garageSpaces'])}" + T2('-car garage', ' autos de garaje'))
    if re.search(r'(updated|new|remodell?ed|renovated|brand-new) kitchen', r): out.append(T2('Updated kitchen', 'Cocina renovada'))
    if 'cul-de-sac' in x + ' ' + r: out.append(T2('Cul-de-sac', 'Calle cerrada'))
    if re.search(r'privacy fence|fence [–-] other|wood fence|chain link|fenced', x) or re.search(r'fenced[- ]in|fenced (back ?)?yard|privacy fenc', r): out.append(T2('Fenced yard', 'Patio cercado'))
    elif 'partial fence' in x: out.append(T2('Partly fenced yard', 'Patio cercado en parte'))
    if 'finished lower level' in r or 'finished basement' in r.replace('unfinished basement', ''): out.append(T2('Finished basement', 'Sótano terminado'))
    if re.search(r'master bed main level|primary bed(room)? main', x): out.append(T2('Main-floor primary suite', 'Recámara principal en planta baja'))
    if re.search(r'main[- ](floor|level) laundry', x + ' ' + r): out.append(T2('Main-floor laundry', 'Lavandería en planta baja'))
    if 'hardwood' in lc(p.get('flooring')): out.append(T2('Hardwood floors', 'Pisos de madera'))
    if 'vaulted' in x: out.append(T2('Vaulted ceilings', 'Techos altos'))
    if 'sprinkler' in x: out.append(T2('Sprinkler system', 'Riego automático'))
    if (p.get('fireplaces') or 0) > 0: out.append(T2('Fireplace', 'Chimenea'))
    return out

def px(u, w):
    """Smaller copy of an MLS photo (they come at ~3000px / 1 MB). The two numbers after the photo number are max width/height."""
    return re.sub(r'(/ParagonImages/Property/[^/]+/[^/]+/\d+/\d+/)\d+/\d+/', lambda m: f'{m.group(1)}{w}/{round(w * 3 / 4)}/', str(u or ''))

def card(h, href, es=False):
    p, ph = h.get('property') or {}, (h.get('photos') or [None])[0]
    dom = (h.get('mls') or {}).get('daysOnMarket')
    tag = ('<span class="lp-new">' + ('Nueva' if es else 'New') + '</span>') if is_new_week(h) else ''
    if price_cut(h): tag += f'<span class="lp-cut">↓ {money(price_cut(h))}</span>'
    elif not tag and highlights(h, es): tag = f'<span class="lp-new lp-hl">{e(highlights(h, es)[0])}</span>'
    bd = f"{p.get('bedrooms') or 0} {'rec' if es else 'bd'} · {baths(p) or 0} {'baños' if es else 'ba'}" + (f" · {p['area']:,} {'pies²' if es else 'sq ft'}" if p.get('area') else '')
    where = (street(h) + ', ' if street(h) else '') + town_of(h)
    alt = ('Casa en venta: ' if es else 'Home for sale: ') + where
    return (f'<a class="lp-card" href="{href}">'
            + (f'<span class="lp-img"><img src="{e(px(ph, 640))}" alt="{e(alt)}" loading="lazy" width="400" height="267">{tag}</span>' if ph else f'<span class="lp-img lp-noimg">{tag}</span>')
            + f'<span class="lp-body"><b>{money(h.get("listPrice"))}</b>' + (f'<em class="lp-mo">{"Aprox." if es else "Est."} {money(payment(h))}{"/mes" if es else "/mo"}*</em>' if payment(h) else '') + f'<span>{e(bd)}</span><span>{e(where)}</span>'
            + f'<small>{e(("Cortesía de " if es else "Listing courtesy of ") + attribution(h))}</small></span></a>')

CSS = '''<style>
.lp-wrap{max-width:1120px;margin:0 auto;padding:0 20px}
.lp-hero{background:var(--navy);color:#d9d2c6;padding:118px 0 28px}
.lp-hero h1{color:#fff;font-weight:400;font-size:clamp(1.8rem,4vw,2.7rem);margin:4px 0 6px}
.lp-hero p{margin:0}.lp-hero a{color:var(--gold-soft)}
.lp-crumbs{font-size:.85rem;letter-spacing:.04em}
.lp-price{font-size:clamp(1.6rem,3.4vw,2.2rem);color:#fff;font-weight:500}
.lp-stats{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:6px;font-size:1.02rem}
.lp-attr{font-size:1rem;color:var(--ink);margin:18px 0 0}
.lp-gal{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:22px 0 8px}
.lp-gal img{width:100%;height:clamp(90px,14vw,170px);object-fit:cover;border-radius:10px;display:block}
.lp-gal img:first-child{grid-column:1/-1;height:clamp(220px,52vw,560px)}
.lp-btns{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.lp-btn{display:inline-block;padding:12px 18px;border-radius:10px;font-weight:500;text-decoration:none;border:1.5px solid var(--navy);color:var(--navy)}
.lp-btn.gold{background:var(--gold-btn,#9a6b3c);border-color:var(--gold-btn,#9a6b3c);color:#fff}
.lp-sec{margin:30px 0}.lp-sec h2{font-size:1.5rem;margin-bottom:10px}
.lp-facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:6px 24px;list-style:none;padding:0}
.lp-facts li{border-bottom:1px solid var(--line);padding:7px 0}
.lp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px;margin:22px 0}
.lp-card{display:block;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;color:var(--ink);text-decoration:none}
.lp-card:hover{box-shadow:0 8px 24px rgba(19,32,59,.12)}
.lp-img{display:block;position:relative;aspect-ratio:3/2;background:#e9e3d8}
.lp-img{overflow:hidden}.lp-img img{width:100%;height:100%;object-fit:cover;display:block}
.lp-new{position:absolute;left:10px;top:10px;background:var(--gold-btn,#9a6b3c);color:#fff;font-size:12px;padding:3px 8px;border-radius:6px}
.lp-hl{background:#fff;color:var(--navy);box-shadow:0 1px 4px rgba(0,0,0,.25);font-weight:600}
.lp-hls{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0}.lp-hls span{background:#f1ebe2;color:var(--navy);border-radius:20px;padding:6px 12px;font-size:.92rem;font-weight:500}
.lp-cut{position:absolute;right:10px;top:10px;background:#1f6b45;color:#fff;font-size:12px;padding:3px 8px;border-radius:6px}
.lp-body{display:flex;flex-direction:column;gap:2px;padding:12px 14px}
.lp-body b{font-size:1.25rem;color:var(--navy)}.lp-body small{color:#555;margin-top:6px;line-height:1.4}
.lp-towns{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}
.lp-groups{margin-top:36px}.lp-gh{font-size:20px;margin:26px 0 4px}.lp-quick{margin:4px 0 20px}.lp-more summary{cursor:pointer;color:var(--navy);font-weight:600;margin:10px 0}
.lp-towns a{border:1px solid var(--line);background:#fff;border-radius:10px;padding:10px 14px;text-decoration:none;color:var(--navy)}
.lp-disc{font-size:.85rem;color:#555;border-top:1px solid var(--line);padding-top:14px;margin:30px 0}
.lp-body-sec{padding:10px 0 40px}
.lp-mo{font-style:normal;font-size:.9rem;color:var(--gold-ink,#8a6237)}
.lp-pay{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin:18px 0}
.lp-box{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.lp-box h3{font-size:1.15rem;margin:0 0 4px}.lp-box .big{font-size:1.6rem;color:var(--navy);font-weight:500}
.lp-box small{display:block;color:#555;line-height:1.45;margin-top:6px}
.lp-g5{border-left:4px solid var(--gold)}
.lp-alert{background:var(--navy);color:#d9d2c6;border-radius:16px;padding:22px 20px;margin:30px 0}
.lp-alert h2{color:#fff;margin:0 0 4px}.lp-alert a{color:var(--gold-soft)}
.lp-alert form{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));margin-top:14px}
.lp-alert input[type=text],.lp-alert input[type=email],.lp-alert input[type=tel]{font:inherit;font-size:16px;padding:11px 12px;border-radius:10px;border:0;width:100%}
.lp-alert .ok{grid-column:1/-1;display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.45}.lp-alert .ok input{margin-top:3px;flex:none;accent-color:var(--gold)}
.lp-alert button{grid-column:1/-1;font:inherit;font-weight:500;background:var(--gold-btn,#9a6b3c);color:#fff;border:0;border-radius:10px;padding:13px;cursor:pointer}
.lp-alert .msg{grid-column:1/-1;margin:0;min-height:1em}
.lp-foot{font-size:.8rem;color:#666}
</style>
'''


ALERT_JS = """<script>
(function () {
  var URL_ = '""" + ALERTS_URL + """', RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  var ES = document.documentElement.lang === 'es', t = function (en, es) { return ES ? es : en; };
  function getAid() { try { var v = localStorage.getItem('mdAlertId'); return RE.test(v || '') ? v : ''; } catch (e) { return ''; } }
  function newId() { return (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) { var r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); }); }
  var f = document.getElementById('lp-al'); if (!f) return;
  var aid = getAid();
  if (aid && f.dataset.mls) { var v = new URLSearchParams(); v.set('action', 'view'); v.set('id', aid); v.set('mlsId', f.dataset.mls); fetch(URL_, { method: 'POST', mode: 'no-cors', body: v, keepalive: true }).catch(function () {}); }
  var msg = f.querySelector('.msg');
  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var name = f.name.value.trim(), email = f.email.value.trim();
    if (!name || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(email)) { msg.textContent = t('Please add your name and a good email.', 'Escriba su nombre y un correo válido.'); return; }
    if (!f.consent.checked) { msg.textContent = t('Please check the box so I can email you.', 'Marque la casilla para poder enviarle correos.'); return; }
    var d = new URLSearchParams(), id = getAid() || newId();
    d.set('name', name); d.set('email', email); d.set('phone', f.phone.value.trim()); d.set('freq', 'Daily'); d.set('consent', 'yes');
    d.set('botcheck', f.botcheck.value); d.set('id', id); d.set('lang', ES ? 'es' : 'en'); d.set('source', location.href.slice(0, 200));
    ['q', 'minprice', 'maxprice', 'minbeds', 'type'].forEach(function (k) { if (f.dataset[k]) d.set(k, f.dataset[k]); });
    f.querySelector('button').disabled = true;
    fetch(URL_, { method: 'POST', mode: 'no-cors', body: d }).then(function () {
      try { localStorage.setItem('mdAlertId', id); } catch (e) {} if (window.gtag) gtag('event', 'generate_lead', { method: 'listing_alert' });
      f.innerHTML = '<p style="grid-column:1/-1;margin:0;color:#fff"><b>' + t('You’re all set!', '¡Listo!') + '</b> ' + t('Check your email. I sent you the homes that match right now.', 'Revise su correo. Le mandé las casas que hay ahora.') + '</p>';
    }).catch(function () { msg.textContent = t('That didn’t go through. Please try again, or text me at 605-838-9140.', 'No se pudo enviar. Intente de nuevo o envíeme un texto al 605-838-9140.'); f.querySelector('button').disabled = false; });
  });
})();
</script>"""

def T(es, en, sp): return sp if es else en

def disclaimer(es, updated):
    if es:
        return ('La información se considera confiable pero no está garantizada y debe verificarse. '
                + (f'Información actualizada el {e(updated)}. ' if updated else '')
                + 'Las casas son cortesía de la oficina indicada en cada una. Información de las casas proporcionada por el MLS de la REALTOR® Association of the Sioux Empire.')
    return ('Listing information is deemed reliable but not guaranteed and should be independently verified. '
            + (f'Listing data last updated {e(updated)}. ' if updated else '')
            + 'Listings shown are courtesy of the listing brokerage named on each listing. Listing data provided by the REALTOR® Association of the Sioux Empire MLS.')

def alert_box(es, q='', minp='', maxp='', beds='', ptype='', mls='', lead=''):
    return f'''<div class="lp-alert" id="alerts"><h2>{T(es, 'Get new homes like these by email', 'Reciba casas nuevas como estas por correo')}</h2>
      <p style="margin:0">{lead}</p>
      <form id="lp-al" novalidate data-q="{e(q)}" data-minprice="{minp}" data-maxprice="{maxp}" data-minbeds="{beds}" data-type="{ptype}" data-mls="{mls}">
        <input type="text" name="name" placeholder="{T(es, 'Name', 'Nombre')}" aria-label="{T(es, 'Name', 'Nombre')}" autocomplete="name" maxlength="100">
        <input type="email" name="email" placeholder="{T(es, 'Email', 'Correo')}" aria-label="{T(es, 'Email', 'Correo')}" autocomplete="email" maxlength="120">
        <input type="tel" name="phone" placeholder="{T(es, 'Phone (optional)', 'Teléfono (opcional)')}" aria-label="{T(es, 'Phone (optional)', 'Teléfono (opcional)')}" autocomplete="tel" maxlength="40">
        <input type="text" name="botcheck" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
        <label class="ok"><input type="checkbox" name="consent" value="yes"><span>{T(es,
          'Yes, email me new listings from Marcos Diaz, and use the homes I open on this site to fine-tune my alerts. If I add my phone, Marcos may call or text me about homes. I can unsubscribe anytime. <a href="/privacy.html" target="_blank">Privacy</a>',
          'Sí, envíenme casas nuevas de Marcos Diaz por correo, y usen las casas que abro en este sitio para ajustar mis alertas. Si doy mi teléfono, Marcos me puede llamar o mandar textos sobre casas. Puedo cancelar cuando quiera. <a href="/es/privacidad.html" target="_blank">Privacidad</a>')}</span></label>
        <button type="submit">{T(es, 'Start my alerts', 'Empezar mis alertas')}</button><p class="msg" role="alert"></p>
      </form></div>'''

def alts(en_url, es_url):
    return (f'<link rel="alternate" hreflang="en" href="{SITE}{en_url}">\n<link rel="alternate" hreflang="es" href="{SITE}{es_url}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}{en_url}">\n')

def set_og_image(path, photo, alt):
    fp = os.path.join(ROOT, path); doc = open(fp).read()
    doc = re.sub(r'<meta property="og:image" content="[^"]*">', lambda m: f'<meta property="og:image" content="{e(photo)}">\n<meta property="og:image:alt" content="{e(alt)}">', doc, count=1)
    open(fp, 'w').write(doc)

# ---------- One page per home (EN + ES) ----------
def home_page(h, same_town, updated, es, links):
    """links: dict with optional 'town', 'sub', 'district' -> (label, en_url, es_url)"""
    p, a, s, tx, ass, m = (h.get(k) or {} for k in ('property', 'address', 'school', 'tax', 'association', 'mls'))
    st, town = street(h), town_of(h)
    full = (st + ', ' if st else '') + f"{town}, {a.get('state') or 'SD'} {a.get('postalCode') or ''}".strip()
    en_url, es_url = url_of(h), url_of(h, True)
    url = es_url if es else en_url; path = url.strip('/') + '/index.html'
    lp = h.get('listPrice') or 0
    price = money(lp)
    bd, ba, sq = p.get('bedrooms') or 0, baths(p), p.get('area')
    condo = p.get('type') == 'CND' or re.search(r'condo|town', str(p.get('subTypeText') or ''), re.I)
    kind = T(es, p.get('subTypeText') or ('Condo/townhome' if condo else 'Home'), 'Condominio o casa adosada' if condo else 'Casa')
    mls_no = h.get('listingId')
    if es:
        title = f"{st or 'Casa en venta'}, {town}, SD | {price} | {bd} rec"
        desc = (f"{price} · casa de {bd} recámaras y {ba} baños" + (f", {sq:,} pies²" if sq else '') + f" en venta en {town}, SD"
                + (f" (MLS #{mls_no})" if mls_no else '') + '. Vea fotos y pida una visita con Marcos Diaz, agente que habla español.')
    else:
        title = f"{st or kind + ' for sale'}, {town}, SD {a.get('postalCode') or ''} | {price} | {bd} bd".strip()
        desc = (f"{price} · {bd} bed, {ba} bath" + (f", {sq:,} sq ft" if sq else '') + f" {kind.lower()} for sale in {town}, SD"
                + (f" (MLS #{mls_no})" if mls_no else '') + '. See photos, details and schedule a showing with Marcos Diaz, Keller Williams Realty Sioux Falls.')
    photos = h.get('photos') or []
    gal = ''.join(f'<img src="{e(px(u, 1600 if i == 0 else 1200))}" alt="{e(T(es, "Photo %d of ", "Foto %d de ") % (i + 1) + full)}" width="1200" height="800"' + (' loading="lazy"' if i else ' fetchpriority="high"') + '>'
                  for i, u in enumerate(photos[:7]))
    live = T(es, '/search/', '/es/buscar-casas/') + f"#home={h['mlsId']}"
    which = st or 'MLS #' + str(mls_no)
    book = BOOK + '?' + urllib.parse.urlencode({'a1': T(es, 'Home: ', 'Casa: ') + which + ', ' + town + (f" (MLS #{mls_no})" if mls_no else '')})
    sms = 'sms:+16058389140?&body=' + urllib.parse.quote(T(es, "Hi Marcos, I'd like to see ", 'Hola Marcos, quiero ver ') + which + (f" (MLS #{mls_no})" if mls_no and st else ''))
    dom = m.get('daysOnMarket')
    yes = lambda v: v not in (None, '', 0)
    facts = [(T(es, 'Bedrooms', 'Recámaras'), bd), (T(es, 'Full baths', 'Baños completos'), p.get('bathsFull')), (T(es, '3/4 baths', 'Baños 3/4'), p.get('bathsThreeQuarter')),
             (T(es, 'Half baths', 'Medios baños'), p.get('bathsHalf')), (T(es, 'Finished sq ft', 'Pies² terminados'), sq and f'{sq:,}'),
             (T(es, 'Price per sq ft', 'Precio por pie²'), sq and lp and money(lp / sq)), (T(es, 'Type', 'Tipo'), kind), (T(es, 'Style', 'Estilo'), p.get('style')),
             (T(es, 'Year built', 'Año de construcción'), p.get('yearBuilt')), (T(es, 'Stories', 'Pisos'), p.get('stories')),
             (T(es, 'Garage', 'Garaje'), p.get('garageSpaces') and T(es, '%d-car', 'para %d autos') % round(p['garageSpaces'])),
             (T(es, 'Lot', 'Terreno'), lot(p)), (T(es, 'Heating', 'Calefacción'), p.get('heating')), (T(es, 'Cooling', 'Aire acondicionado'), p.get('cooling')),
             (T(es, 'Foundation', 'Cimientos'), p.get('foundation')), (T(es, 'Flooring', 'Pisos'), as_list(p.get('flooring'))),
             (T(es, 'Interior', 'Interior'), as_list(p.get('interiorFeatures'))), (T(es, 'Outside', 'Afuera'), as_list(p.get('exteriorFeatures'))),
             (T(es, 'Subdivision', 'Vecindario'), p.get('subdivision')), (T(es, 'County', 'Condado'), (h.get('geo') or {}).get('county')),
             (T(es, 'Yearly taxes', 'Impuestos al año'), tx.get('taxAnnualAmount') and money(tx['taxAnnualAmount']) + (f" ({tx['taxYear']})" if tx.get('taxYear') else '')),
             ('HOA', ass.get('fee') and money(ass['fee']) + (f" / {str(ass.get('frequency')).lower()}" if ass.get('frequency') else '')),
             (T(es, 'Days on market', 'Días en el mercado'), dom), ('MLS #', mls_no)]
    facts_html = ''.join(f'<li>{k}: <b>{e(v)}</b></li>' for k, v in facts if yes(v))
    schools = [(T(es, 'School district', 'Distrito escolar'), s.get('district')), (T(es, 'Elementary', 'Primaria'), s.get('elementarySchool')),
               (T(es, 'Middle', 'Secundaria'), s.get('middleSchool')), (T(es, 'High', 'Preparatoria'), s.get('highSchool'))]
    schools_html = ''.join(f'<li>{k}: <b>{e(fix_typos(v))}</b></li>' for k, v in schools if v)
    pick = lambda k: (links[k][2] if es else links[k][1]) if links.get(k) else None
    tlink = pick('town') or T(es, '/homes-for-sale/', '/es/casas-en-venta/')
    more = sorted((x for x in same_town if x['mlsId'] != h['mlsId']), key=lambda x: abs((x.get('listPrice') or 0) - lp))
    more_html = ''.join(card(x, url_of(x, es), es) for x in more[:4])
    explore = [(T(es, f'All homes for sale in {town}', f'Todas las casas en venta en {town}'), pick('town'))]
    if links.get('sub'): explore.append((T(es, f"Homes in {links['sub'][0]}", f"Casas en {links['sub'][0]}"), pick('sub')))
    if links.get('district'): explore.append((T(es, f"Homes in the {links['district'][0]} School District", f"Casas en el distrito escolar {links['district'][0]}"), pick('district')))
    explore_html = ''.join(f'<a href="{u}">{e(l)}</a>' for l, u in explore if u)
    ld = {'@context': 'https://schema.org', '@type': 'RealEstateListing', 'name': full, 'url': SITE + url, 'description': desc, 'inLanguage': 'es' if es else 'en',
          'image': photos[:5], 'datePosted': (h.get('listDate') or '')[:10] or None,
          'offers': {'@type': 'Offer', 'price': lp, 'priceCurrency': 'USD', 'availability': 'https://schema.org/InStock'},
          'about': {'@type': 'Apartment' if condo else 'SingleFamilyResidence',
                    'address': {'@type': 'PostalAddress', 'streetAddress': st or None, 'addressLocality': town, 'addressRegion': a.get('state') or 'SD', 'postalCode': a.get('postalCode')},
                    'numberOfBedrooms': bd or None, 'numberOfBathroomsTotal': float(ba) if ba else None,
                    'floorSize': {'@type': 'QuantitativeValue', 'value': sq, 'unitCode': 'FTK'} if sq else None,
                    'yearBuilt': p.get('yearBuilt')},
          'broker': {'@type': 'RealEstateAgent', 'name': 'Marcos Diaz, Keller Williams Realty Sioux Falls', 'telephone': '+1-605-838-9140'}}
    if (h.get('geo') or {}).get('lat') and show_addr(h):
        ld['about']['geo'] = {'@type': 'GeoCoordinates', 'latitude': h['geo']['lat'], 'longitude': h['geo']['lng']}
    strip = lambda o: {k: strip(v) for k, v in o.items() if v not in (None, '', [])} if isinstance(o, dict) else o
    head = CSS + alts(en_url, es_url) + '<script type="application/ld+json">' + json.dumps(strip(ld)).replace('</', '<\\/') + '</script>\n'
    remarks = h.get('remarks') or ''
    mo = payment(h)
    pay_html = ''
    if mo:
        pay_html += (f'<div class="lp-box"><h3>{T(es, "Estimated payment", "Pago mensual aproximado")}</h3><div class="big">{money(mo)}{T(es, "/mo", "/mes")}*</div>'
                     f'<small>{T(es, "Principal, interest, taxes and insurance.", "Préstamo, interés, impuestos y seguro.")} <a href="{T(es, "/", "/es/")}?price={int(lp)}#calculator">{T(es, "Change the numbers →", "Cambie los números →")}</a></small></div>')
    if is_dpa(h):
        five = round(lp * 0.95 * 0.05 / 100) * 100
        pay_html += (f'<div class="lp-box lp-g5"><h3>{T(es, "First-time buyer?", "¿Su primera casa?")}</h3><p style="margin:0">'
                     + T(es, f'This price is under the {money(DPA_LIMIT)} limit for South Dakota’s <b>Give Me Five</b> program: up to 5% of your loan (about {money(five)}) toward your down payment, if you qualify.',
                            f'Este precio está bajo el límite de {money(DPA_LIMIT)} del programa <b>Give Me Five</b> de Dakota del Sur: hasta 5% de su préstamo (unos {money(five)}) para su pago inicial, si califica.')
                     + f'</p><small><a href="{T(es, "/blog/give-me-five-down-payment-assistance/", "/es/blog/give-me-five-ayuda-pago-inicial/")}">{T(es, "See who qualifies →", "Vea quién califica →")}</a></small></div>')
    pay_html = f'<div class="lp-pay">{pay_html}</div>' if pay_html else ''
    lead = T(es, f'New {e(town)} homes around {money(lp)}' + (f' with {bd}+ bedrooms' if bd else '') + ', sent to you as soon as they hit the market. Free, and you can stop anytime.',
                 f'Casas nuevas en {e(town)} cerca de {money(lp)}' + (f' con {bd} recámaras o más' if bd else '') + ', apenas salgan a la venta. Es gratis y puede parar cuando quiera.')
    alert_html = alert_box(es, town, int(round(lp * 0.8, -4)), int(round(lp * 1.2, -4)), bd or '', 'condominium' if condo else 'residential', h['mlsId'], lead)
    crumbs = (f'<a href="{T(es, "/", "/es/")}">{T(es, "Home", "Inicio")}</a> / <a href="{T(es, "/homes-for-sale/", "/es/casas-en-venta/")}">{T(es, "Homes for sale", "Casas en venta")}</a> / <a href="{tlink}">{e(town)}</a>')
    about_me = T(es, "I'm Marcos Diaz, a Broker Associate with Keller Williams Realty Sioux Falls. I can tell you what's around it, what similar homes sold for, and whether it's priced right. I'm bilingual, so we can talk in English or Spanish.",
                     'Soy Marcos Diaz, Broker Associate con Keller Williams Realty Sioux Falls. Le puedo decir qué hay cerca, en cuánto se vendieron casas parecidas y si el precio es justo. Hablo español e inglés.')
    body = f'''  <section class="lp-hero"><div class="lp-wrap">
    <p class="lp-crumbs">{crumbs}</p>
    <h1>{e(full)}</h1>
    <div class="lp-price">{price}</div>
    <div class="lp-stats"><span>{bd} {T(es, "bed" if str(bd) == "1" else "beds", "recámara" if str(bd) == "1" else "recámaras")}</span><span>{ba or 0} {T(es, "bath" if str(ba) == "1" else "baths", "baño" if str(ba) == "1" else "baños")}</span>{f"<span>{sq:,} {T(es, 'sq ft', 'pies²')}</span>" if sq else ""}<span>{e(kind)}</span>{f"<span>{T(es, 'Built', 'Construida en')} {p['yearBuilt']}</span>" if p.get('yearBuilt') else ""}</div>
  </div></section>
  <section class="lp-body-sec"><div class="lp-wrap">
    <p class="lp-attr">{T(es, "Listing courtesy of", "Cortesía de")} {e(attribution(h))}</p>
    {('<div class="lp-hls">' + ''.join(f'<span>{e(x)}</span>' for x in highlights(h, es)[:8]) + '</div>') if highlights(h, es) else ''}
    {pay_html}
    {f'<div class="lp-gal">{gal}</div>' if gal else ''}
    <p><a href="{live}">{T(es, f"See all {len(photos)} photos, the map and drive times →", f"Vea las {len(photos)} fotos, el mapa y el tiempo de manejo →")}</a></p>
    <div class="lp-btns">
      <a class="lp-btn gold" href="{e(book)}" target="_blank" rel="noopener">{T(es, "Request a showing", "Pedir una visita")}</a>
      <a class="lp-btn" href="tel:+16058389140">{T(es, "Call", "Llamar")} 605-838-9140</a>
      <a class="lp-btn" href="{e(sms)}">{T(es, "Text Marcos", "Mandar texto")}</a>
    </div>
    {f'<div class="lp-sec"><h2>{T(es, "About this home", "Sobre esta casa")}</h2>' + (f'<p><small>{T(es, "", "Descripción del agente de la casa, en inglés:")}</small></p>' if es else '') + f'<p>{e(remarks)}</p></div>' if remarks else ''}
    <div class="lp-sec"><h2>{T(es, "Facts &amp; features", "Detalles de la casa")}</h2><ul class="lp-facts">{facts_html}</ul></div>
    {f'<div class="lp-sec"><h2>{T(es, "Schools", "Escuelas")}</h2><ul class="lp-facts">{schools_html}</ul><p><small>{T(es, "Always confirm schools with the district for a specific address.", "Siempre confirme las escuelas con el distrito para cada dirección.")}</small></p></div>' if schools_html else ''}
    <div class="lp-sec"><h2>{T(es, "Thinking about this home?", "¿Le interesa esta casa?")}</h2><p>{about_me} {T(es, "Call or text", "Llame o mande un texto al")} <a href="tel:+16058389140">605-838-9140</a>.</p></div>
    {alert_html}
    {f'<div class="lp-sec"><h2>{T(es, f"More homes for sale in {e(town)}", f"Más casas en venta en {e(town)}")}</h2><div class="lp-grid">{more_html}</div></div>' if more_html else ''}
    {f'<div class="lp-towns">{explore_html}</div>' if explore_html else ''}
    <p class="lp-disc">{e(h.get("disclaimer") or "")} {disclaimer(es, updated)}</p>
    {f'<p class="lp-foot">*{e(pay_note(es))}</p>' if mo else ''}
  </div></section>
{ALERT_JS}
'''
    _page(path, title, desc, body, lang='es' if es else 'en', canonical=SITE + url, alt_es=es_url, alt_en=en_url, head_extra=head, news=False)
    if photos: set_og_image(path, px(photos[0], 1200), full)
    return url

# ---------- Collection pages (towns, prices, bedrooms, neighborhoods, districts...) ----------
class Coll:
    """One list page, in English and Spanish."""
    def __init__(self, en_url, es_url, h1, title, desc_kw, homes, crumbs=(), area=None, q='', alert=None, sub=()):
        self.en_url, self.es_url, self.h1, self.title, self.desc_kw = en_url, es_url, h1, title, desc_kw
        self.homes, self.crumbs, self.area, self.q, self.alert, self.sub = homes, list(crumbs), area, q, alert or {}, list(sub)

def coll_page(c, updated, es):
    homes = sorted(c.homes, key=lambda x: (x.get('listDate') or ''), reverse=True)
    n = len(homes)
    prices = sorted(x['listPrice'] for x in homes if x.get('listPrice'))
    med = prices[len(prices) // 2] if prices else 0
    new7 = sum(1 for x in homes if is_new_week(x))
    url = c.es_url if es else c.en_url
    h1, title, kw = (x[1] if es else x[0] for x in (c.h1, c.title, c.desc_kw))
    search = T(es, '/search/', '/es/buscar-casas/') + (('?q=' + urllib.parse.quote(c.q)) if c.q else '')
    if es:
        lead = f'{n} casas en venta ahora' + (f' · precio medio {money(med)}' if med else '') + (f' · {new7} nuevas esta semana' if new7 else '')
        desc = f'Vea {n} {kw} con fotos, precios y pago mensual aproximado. Se actualiza cada día. Agente que habla español: Marcos Diaz, Keller Williams Realty Sioux Falls.'
    else:
        lead = f'{n} homes for sale right now' + (f' · median price {money(med)}' if med else '') + (f' · {new7} new this week' if new7 else '')
        desc = f'See {n} {kw} with photos, prices and estimated monthly payments. Updated daily. Marcos Diaz, Keller Williams Realty Sioux Falls.'
    crumbs = [(T(es, 'Home', 'Inicio'), T(es, '/', '/es/')), (T(es, 'Homes for sale', 'Casas en venta'), T(es, '/homes-for-sale/', '/es/casas-en-venta/'))]
    crumbs += [(lab[1] if es else lab[0], u[1] if es else u[0]) for lab, u in c.crumbs]
    if c.en_url == '/homes-for-sale/': crumbs = crumbs[:1]
    crumbs_html = ' / '.join(f'<a href="{u}">{e(l)}</a>' for l, u in crumbs) + ' / ' + e(h1)
    cards = ''.join(card(x, url_of(x, es), es) for x in homes[:MAX_TOWN_CARDS])
    quick_html, groups_html = sub_groups(c.sub, es)
    a = c.alert
    alert = alert_box(es, a.get('q', ''), a.get('minprice', ''), a.get('maxprice', ''), a.get('minbeds', ''), a.get('type', ''), '',
                      T(es, 'New homes like these, sent to you as soon as they hit the market. Free, and you can stop anytime.',
                            'Casas nuevas como estas, apenas salgan a la venta. Es gratis y puede parar cuando quiera.')) if homes and a else ''
    area_btn = ''
    if c.area: area_btn = f'<a class="lp-btn" href="{T(es, "/areas/", "/es/areas/")}{c.area}.html">{T(es, "Living in ", "Conozca ")}{e(c.q)}</a>'
    empty = T(es, 'No homes like this are for sale right now. Call or text me and I’ll let you know as soon as one comes up.',
                  'Ahora no hay casas así en venta. Llámeme o mándeme un texto y le aviso cuando salga una.')
    body = f'''  <section class="lp-hero"><div class="lp-wrap">
    <p class="lp-crumbs">{crumbs_html}</p>
    <h1>{e(h1)}</h1><p>{lead}</p>
  </div></section>
  <section class="lp-body-sec"><div class="lp-wrap">
    <div class="lp-btns"><a class="lp-btn gold" href="{e(search)}">{T(es, "See them on the map", "Verlas en el mapa")}</a>{area_btn}<a class="lp-btn" href="tel:+16058389140">{T(es, "Call or text", "Llame o mande texto:")} 605-838-9140</a></div>
    {quick_html}
    {f'<div class="lp-grid">{cards}</div>' if cards else f'<p>{empty}</p>'}
    {f'<p><a href="{e(search)}">{T(es, f"See all {n} homes on the map →", f"Ver las {n} casas en el mapa →")}</a></p>' if n > MAX_TOWN_CARDS else ''}
    {groups_html}
    {alert}
    <p class="lp-disc">{disclaimer(es, updated)}</p>
    {f'<p class="lp-foot">*{e(pay_note(es))}</p>' if homes else ''}
  </div></section>
{ALERT_JS if alert else ''}
'''
    _page(url.strip('/') + '/index.html', title if len(title) > 46 else f'{title} | Marcos Diaz', desc, body, lang='es' if es else 'en', canonical=SITE + url,
          alt_es=c.es_url, alt_en=c.en_url, head_extra=CSS + alts(c.en_url, c.es_url))
    photo = next((x['photos'][0] for x in homes if x.get('photos')), None)
    if photo: set_og_image(url.strip('/') + '/index.html', px(photo, 1200), h1)
    return url


def sub_groups(subs, es):
    """Short quick links above the homes (new / price cuts), the rest grouped under headings below them."""
    def link(l, u, k, short=None):
        return f'<a href="{u[1] if es else u[0]}">{e(short or (l[1] if es else l[0]))} <b>({k})</b></a>'
    quick, price, beds, nb, other = [], [], [], [], []
    for l, u, k in subs:
        url = u[0]
        if url.endswith('new-this-week/'): quick.append(link(l, u, k, T(es, 'New this week', 'Nuevas esta semana')))
        elif url.endswith('price-cuts/'): quick.append(link(l, u, k, T(es, 'Price cuts', 'Bajaron de precio')))
        elif '/under-' in url:
            cap = url.rstrip('/').rsplit('under-', 1)[1].upper()
            price.append(link(l, u, k, T(es, f'Under ${cap}', f'Menos de ${cap}')))
        elif re.search(r'/(\d)-bedrooms/$', url):
            b = re.search(r'/(\d)-bedrooms/$', url).group(1)
            beds.append(link(l, u, k, T(es, f'{b}+ beds', f'{b}+ recámaras')))
        elif '/neighborhoods/' in url:
            name = re.sub(r'^(Homes for Sale in |Casas en venta en )', '', l[1] if es else l[0]).rsplit(',', 1)[0]
            nb.append(link(l, u, k, re.sub(r' neighborhood$', '', name)))
        else: other.append(link(l, u, k))
    quick_html = f'<div class="lp-towns lp-quick">{"".join(quick)}</div>' if quick else ''
    sec = lambda h, xs: f'<h2 class="lp-gh">{h}</h2><div class="lp-towns">{"".join(xs)}</div>' if xs else ''
    more = ''
    if len(nb) > 12:
        more = f'<details class="lp-more"><summary>{T(es, f"{len(nb) - 12} more neighborhoods", f"{len(nb) - 12} vecindarios más")}</summary><div class="lp-towns">{"".join(nb[12:])}</div></details>'
    groups = (sec(T(es, 'Shop by price', 'Por precio'), price) + sec(T(es, 'Shop by bedrooms', 'Por recámaras'), beds)
              + sec(T(es, 'Popular neighborhoods', 'Vecindarios populares'), nb[:12]) + more + sec(T(es, 'More searches', 'Más búsquedas'), other))
    return quick_html, (f'<div class="lp-groups">{groups}</div>' if groups else '')

# ---------- What goes in each set ----------
PRICE_CAPS = [200000, 250000, 300000, 350000, 400000, 500000]
def kfmt(n): return f'${n // 1000}K'
def acres(h):
    p = h.get('property') or {}
    if p.get('acres'): return float(p['acres'])
    if p.get('lotSizeArea'):
        u = str(p.get('lotSizeAreaUnits') or '').lower()
        return float(p['lotSizeArea']) if 'acre' in u or (not u and p['lotSizeArea'] < 200) else float(p['lotSizeArea']) / 43560
    return 0
THIS_YEAR = datetime.date.today().year
def is_new(h): return ((h.get('property') or {}).get('yearBuilt') or 0) >= THIS_YEAR - 1
def is_condo(h):
    p = h.get('property') or {}
    return p.get('type') == 'CND' or bool(re.search(r'condo|town', str(p.get('subTypeText') or ''), re.I))
def price_cut(h):
    o, l = h.get('originalListPrice') or 0, h.get('listPrice') or 0
    return o - l if o and l and o > l else 0
def is_new_week(h):
    # Use the real list date; the MLS days-on-market field is 0 for many older listings
    ld = str(h.get('listDate') or '')[:10]
    if ld:
        try: return (datetime.date.today() - datetime.date.fromisoformat(ld)).days <= 7
        except ValueError: pass
    d = (h.get('mls') or {}).get('daysOnMarket')
    return bool(d) and d <= 7

def fresh_subs(homes, base_en, base_es, where_en, where_es, q, crumbs, always=False):
    """'New this week' and 'Price cuts' pages. Area-wide ones are always built; town ones need 3+ homes."""
    out = []
    for en_s, es_s, test, h1, kw in (
        ('new-this-week', 'nuevas-esta-semana', is_new_week,
         (f'New Listings This Week {where_en}', f'Casas nuevas esta semana {where_es}'),
         (f'homes listed for sale this week {where_en}', f'casas que salieron a la venta esta semana {where_es}')),
        ('price-cuts', 'bajaron-de-precio', price_cut,
         (f'Price Cuts: Homes for Sale {where_en}', f'Casas que bajaron de precio {where_es}'),
         (f'homes with price reductions {where_en}', f'casas que bajaron de precio {where_es}'))):
        hs = [x for x in homes if test(x)]
        if always or len(hs) >= 3:
            if en_s == 'price-cuts': hs = sorted(hs, key=lambda x: -price_cut(x))
            out.append(Coll(f'{base_en}{en_s}/', f'{base_es}{es_s}/', h1, h1, kw, hs, crumbs, q=q, alert={'q': q} if q else {}))
    return out

def is_ranch(h): return bool(re.search(r'ranch', str((h.get('property') or {}).get('style') or ''), re.I))
ROMAN = re.compile(r'^(i{1,3}|iv|v|vi{1,3}|ix|x)$', re.I)
def nice_case(s):  # "KLEIN'S 2ND ADDN III" -> "Klein's 2nd Addn III"
    return ' '.join(w.upper() if ROMAN.match(w) else re.sub(r"^([a-z])", lambda m: m.group(1).upper(), w.lower()) for w in s.split())
SUB_JUNK = re.compile(r'temporary|check back|unknown|^none$|^n/?a$|metes|unplatted|^tbd$', re.I)
def nice_sub(s):
    s = str(s or '')
    if SUB_JUNK.search(s.strip()): return ''  # MLS placeholders, not real neighborhoods
    s = re.sub(r'\b(ADDN?|ADDITION|ADD\.?|SUBD?|SUBDIVISION|PLAT|PH(ASE)?\s*\w+)\b\.?', '', s, flags=re.I)
    # "Copper Creek Heights An To The City Of Sioux Falls" -> "Copper Creek Heights"
    s = re.sub(r'\b(an\s+|a\s+)?to\s+(the\s+)?(city\s+of\s+)?[A-Za-z .]+$', '', s, flags=re.I) if re.search(r'\bto\s+(the\s+)?(city|sioux|tea|harrisburg|brandon)', s, re.I) else s
    s = re.sub(r'(\d)(?!(?:st|nd|rd|th)\b)([A-Za-z]{2,})', r'\1 \2', s, flags=re.I)  # "41Ellis" -> "41 Ellis"
    s = re.sub(r'\s+(an|a)$', '', s.strip(), flags=re.I)
    s = re.sub(r'\s+', ' ', s).strip(' -,')
    if SUB_JUNK.search(s): return ''
    return nice_case(s) if s.isupper() or s.islower() else s
def fix_typos(s):  # spelling mistakes that come in from the MLS feed
    return re.sub(r'\bComminty\b', 'Community', str(s or ''))

def nice_district(s):
    s = fix_typos(s)
    s = re.sub(r'\bschool district\b|\bsd\b|\bdist(rict)?\b', '', str(s or ''), flags=re.I)
    s = re.sub(r'\s+', ' ', s).strip(' -,')
    return s.title() if s.isupper() or s.islower() else s

def price_beds_subs(homes, base_en, base_es, where_en, where_es, q, crumbs, alert_extra=None):
    """Price-cap and bedroom pages for one place. Returns list of Coll."""
    out, last = [], None
    for cap in PRICE_CAPS:
        hs = [x for x in homes if 0 < (x.get('listPrice') or 0) <= cap]
        if len(hs) >= 5 and len(hs) < len(homes) and len(hs) != last:
            last = len(hs); k = kfmt(cap).lower().replace('$', '')
            out.append(Coll(f'{base_en}under-{k}/', f'{base_es}menos-de-{k}/',
                            (f'Homes for Sale Under {kfmt(cap)} {where_en}', f'Casas en venta por menos de {kfmt(cap)} {where_es}'),
                            (f'Homes Under {kfmt(cap)} {where_en}', f'Casas por menos de {kfmt(cap)} {where_es}'),
                            (f'homes for sale under {kfmt(cap)} {where_en}', f'casas en venta por menos de {kfmt(cap)} {where_es}'),
                            hs, crumbs, q=q, alert=dict(alert_extra or {}, q=q, maxprice=cap)))
    for b in (3, 4, 5):
        hs = [x for x in homes if ((x.get('property') or {}).get('bedrooms') or 0) >= b]
        if len(hs) >= 5 and len(hs) < len(homes):
            out.append(Coll(f'{base_en}{b}-bedrooms/', f'{base_es}{b}-recamaras/',
                            (f'{b}+ Bedroom Homes for Sale {where_en}', f'Casas de {b} recámaras o más {where_es}'),
                            (f'{b} Bedroom Homes for Sale {where_en}', f'Casas de {b} recámaras {where_es}'),
                            (f'homes with {b}+ bedrooms for sale {where_en}', f'casas de {b} recámaras o más en venta {where_es}'),
                            hs, crumbs, q=q, alert=dict(alert_extra or {}, q=q, minbeds=b)))
    return out

def build_sets(homes, by_town):
    colls, town_coll, links = [], {}, defaultdict(dict)
    H, HE = '/homes-for-sale/', '/es/casas-en-venta/'
    # Towns + their price/bedroom pages + neighborhoods in town
    subs_by_town = defaultdict(lambda: defaultdict(list))
    for h in homes:
        sd = nice_sub((h.get('property') or {}).get('subdivision'))
        if sd and len(sd) > 2: subs_by_town[town_of(h)][sd].append(h)
    for t, hs in by_town.items():
        if not (t in TOWNS or len(hs) >= 3): continue
        slug, area = TOWNS.get(t, (slugify(t + ' sd'), None))
        en, es_ = f'{H}{slug}/', f'{HE}{slug}/'
        crumb = [((t, t), (en, es_))]
        kids = fresh_subs(hs, en, es_, f'in {t}, SD', f'en {t}, SD', t, crumb) + price_beds_subs(hs, en, es_, f'in {t}, SD', f'en {t}, SD', t, crumb)
        nbhd = []
        for sd, shs in sorted(subs_by_town[t].items(), key=lambda kv: -len(kv[1])):
            if len(shs) < 3: continue
            ss = slugify(sd)
            c = Coll(f'{H}neighborhoods/{ss}/', f'{HE}vecindarios/{ss}/',
                     (f'Homes for Sale in {sd}, {t}', f'Casas en venta en {sd}, {t}'),
                     (f'{sd} Homes for Sale, {t} SD', f'Casas en venta en {sd}, {t} SD'),
                     (f'homes for sale in the {sd} neighborhood of {t}, SD', f'casas en venta en el vecindario {sd} de {t}, SD'),
                     shs, crumb, q=t, alert={'q': t})
            nbhd.append(c)
            for x in shs: links[x['mlsId']]['sub'] = (sd, c.en_url, c.es_url)
        sub = [((c.h1[0].replace(f' in {t}, SD', ''), c.h1[1].replace(f' en {t}, SD', '')), (c.en_url, c.es_url), len(c.homes)) for c in kids]
        sub += [((f'{c.h1[0].split(" in ")[1].split(",")[0]} neighborhood', f'Vecindario {c.h1[1].split(" en ")[1].split(",")[0]}'), (c.en_url, c.es_url), len(c.homes)) for c in nbhd]
        tc = Coll(en, es_, (f'Homes for Sale in {t}, SD', f'Casas en venta en {t}, SD'),
                  (f'{t}, SD Homes for Sale | {len(hs)} Listings', f'Casas en venta en {t}, SD | {len(hs)} casas'),
                  (f'homes for sale in {t}, SD', f'casas en venta en {t}, SD'), hs, (), area, t, {'q': t}, sub)
        town_coll[t] = tc
        colls += [tc] + kids + nbhd
        for x in hs: links[x['mlsId']]['town'] = (t, en, es_)
    # School districts
    dist = defaultdict(list)
    for h in homes:
        d = nice_district((h.get('school') or {}).get('district'))
        if d and len(d) > 1: dist[d].append(h)
    district_colls = []
    for d, hs in sorted(dist.items(), key=lambda kv: -len(kv[1])):
        if len(hs) < 3: continue
        ds = slugify(d)
        c = Coll(f'{H}school-districts/{ds}/', f'{HE}distritos-escolares/{ds}/',
                 (f'Homes for Sale in the {d} School District', f'Casas en venta en el distrito escolar {d}'),
                 (f'{d} School District Homes for Sale', f'Casas en el distrito escolar {d}'),
                 (f'homes for sale in the {d} School District', f'casas en venta en el distrito escolar {d}'), hs, alert={})
        district_colls.append(c)
        for x in hs: links[x['mlsId']]['district'] = (d, c.en_url, c.es_url)
    # Area-wide searches
    wide = []
    def add(en_slug, es_slug, h1, title, kw, hs, alert=None):
        if len(hs) >= 3: wide.append(Coll(f'{H}{en_slug}/', f'{HE}{es_slug}/', h1, title, kw, hs, alert=alert or {}))
    near = ('near Sioux Falls, SD', 'cerca de Sioux Falls, SD')
    add('acreage', 'con-terreno', (f'Homes with Acreage for Sale {near[0]}', f'Casas con terreno (un acre o más) {near[1]}'),
        ('Acreage Homes for Sale Near Sioux Falls', 'Casas con terreno cerca de Sioux Falls'),
        (f'homes on 1+ acre for sale {near[0]}', f'casas con un acre o más en venta {near[1]}'), [x for x in homes if acres(x) >= 1])
    add('new-construction', 'construccion-nueva', (f'New Construction Homes for Sale {near[0]}', f'Casas nuevas en venta {near[1]}'),
        ('New Construction Homes Near Sioux Falls', 'Casas nuevas cerca de Sioux Falls'),
        (f'new construction homes for sale {near[0]}', f'casas nuevas en venta {near[1]}'), [x for x in homes if is_new(x)])
    add('condos-townhomes', 'condominios', (f'Condos & Townhomes for Sale {near[0]}', f'Condominios y casas adosadas en venta {near[1]}'),
        ('Condos & Townhomes for Sale in Sioux Falls', 'Condominios en venta en Sioux Falls'),
        (f'condos and townhomes for sale {near[0]}', f'condominios y casas adosadas en venta {near[1]}'), [x for x in homes if is_condo(x)], {'type': 'condominium'})
    add('ranch-homes', 'casas-de-un-piso', (f'Ranch Homes for Sale {near[0]}', f'Casas estilo rancho (un piso) en venta {near[1]}'),
        ('Ranch-Style Homes for Sale Near Sioux Falls', 'Casas de un piso cerca de Sioux Falls'),
        (f'ranch-style homes for sale {near[0]}', f'casas estilo rancho en venta {near[1]}'), [x for x in homes if is_ranch(x)])
    wide = fresh_subs(homes, H, HE, near[0], near[1], '', [], always=True) + wide + price_beds_subs(homes, H, HE, near[0], near[1], '', [])
    colls += district_colls + wide
    # Hub
    tlinks = [((t, t), (c.en_url, c.es_url), len(c.homes)) for t, c in sorted(town_coll.items(), key=lambda kv: (kv[0] != 'Sioux Falls', -len(kv[1].homes), kv[0])) if c.homes]
    wl = [((c.h1[0].replace(' for Sale near Sioux Falls, SD', '').replace(' near Sioux Falls, SD', ''), c.h1[1].replace(' en venta cerca de Sioux Falls, SD', '').replace(' cerca de Sioux Falls, SD', '')), (c.en_url, c.es_url), len(c.homes)) for c in wide]
    dl = [((c.h1[0].replace('Homes for Sale in the ', ''), c.h1[1].replace('Casas en venta en el distrito escolar ', 'Distrito ')), (c.en_url, c.es_url), len(c.homes)) for c in district_colls]
    hub = Coll(H, HE, ('Homes for Sale in Sioux Falls & Nearby Towns', 'Casas en venta en Sioux Falls y pueblos cercanos'),
               ('Homes for Sale in Sioux Falls & Nearby Towns', 'Casas en venta en Sioux Falls y pueblos cercanos'),
               ('homes for sale in Sioux Falls, Tea, Harrisburg, Brandon and nearby towns', 'casas en venta en Sioux Falls, Tea, Harrisburg, Brandon y pueblos cercanos'),
               [], sub=tlinks + wl + dl)
    hub.homes_count = len(homes)
    return [hub] + colls, links

def hub_fix(c, n):
    """The hub lists links, not homes: give it the total count without printing every card."""
    for es in (False, True):
        fp = os.path.join(ROOT, (c.es_url if es else c.en_url).strip('/') + '/index.html')
        s = open(fp).read()
        s = s.replace('<p>0 homes for sale right now</p>', f'<p>{n} homes for sale right now in Sioux Falls and nearby towns. Pick a town or a search below.</p>')
        s = s.replace('<p>0 casas en venta ahora</p>', f'<p>{n} casas en venta ahora en Sioux Falls y pueblos cercanos. Escoja un pueblo o una búsqueda.</p>')
        s = s.replace('See 0 homes for sale', f'See {n} homes for sale').replace('Vea 0 casas en venta', f'Vea {n} casas en venta')
        s = re.sub(r'<p>(No homes like this are for sale right now|Ahora no hay casas así en venta)[^<]*</p>', '', s)
        open(fp, 'w').write(s)

# ---------- Main ----------
def main():
    raw = fetch_listings()
    for h in raw: numbers(h)
    homes = [h for h in raw if h.get('mlsId') and h.get('internetEntireListingDisplay') is not False and town_of(h)
             and str((h.get('mls') or {}).get('status') or 'Active').replace(' ', '').lower() in ('active', 'activeundercontract', '')]
    if not homes: sys.exit('No listings could be shown – stopping so the site is not emptied.')
    updated = last_update()
    by_town = defaultdict(list)
    for h in homes: by_town[town_of(h)].append(h)
    for t in TOWNS: by_town.setdefault(t, [])  # every town with an area page gets a page, even with no homes today
    colls, links = build_sets(homes, by_town)
    urls = []
    for t, hs in by_town.items():
        for h in hs:
            d = (h.get('modified') or '')[:10]
            urls += [(home_page(h, hs, updated, False, links[h['mlsId']]), d), (home_page(h, hs, updated, True, links[h['mlsId']]), d)]
    for c in colls:
        urls += [(coll_page(c, updated, False), ''), (coll_page(c, updated, True), '')]
    hub_fix(colls[0], len(homes))

    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f'  <url><loc>{SITE}{u}</loc><lastmod>{d or today}</lastmod></url>' for u, d in urls]
    sm.append('</urlset>')
    open(os.path.join(ROOT, 'homes-sitemap.xml'), 'w').write('\n'.join(sm) + '\n')
    rb = os.path.join(ROOT, 'robots.txt'); r = open(rb).read()
    if 'homes-sitemap.xml' not in r: open(rb, 'a').write(f'Sitemap: {SITE}/homes-sitemap.xml\n')

    # Area pages: "See homes for sale" buttons go to the new town pages instead of the KW search
    for area, tslug in AREA_TO_TOWN.items():
        for f, base in ((f'areas/{area}.html', '/homes-for-sale/'), (f'es/areas/{area}.html', '/es/casas-en-venta/')):
            fp = os.path.join(ROOT, f)
            if not os.path.exists(fp): continue
            s = open(fp).read()
            s = re.sub(r'href="https://marcos\.kw\.com/search/sale\?viewport=[^"]*"( class="btn[^"]*") target="_blank" rel="noopener"', lambda m: f'href="{base}{tslug}/"{m.group(1)}', s)
            open(fp, 'w').write(s)
    print(f'Listing pages: {len(homes)} homes, {len(colls)} list pages (x2 languages), {len(urls)} URLs in homes-sitemap.xml')

if __name__ == '__main__':
    main()
