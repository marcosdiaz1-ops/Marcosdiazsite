"""Google-friendly listing pages, built from the live RASE feed every time the site publishes.

Runs inside .github/workflows/deploy.yml (never committed), only after the new search is live
(the file data/listing-pages-on exists; tools/go_live_search.py creates it).

Makes, from every active listing the feed allows on the internet:
  /homes/<address>-<mlsId>/          one page per home (English)
  /homes-for-sale/ and /homes-for-sale/<town>/            town pages (English)
  /es/casas-en-venta/ and /es/casas-en-venta/<town>/      town pages (Spanish)
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
def baths(p):
    b = (p.get('bathsFull') or 0) + (p.get('bathsThreeQuarter') or 0) + 0.5 * (p.get('bathsHalf') or 0)
    b = b or p.get('bathrooms') or 0
    return ('%g' % b) if b else ''

def show_addr(h): return h.get('internetAddressDisplay') is not False

def street(h): return clean_addr((h.get('address') or {}).get('full')) if show_addr(h) else ''

def town_of(h): return ((h.get('address') or {}).get('city') or '').strip().title()

def url_of(h):
    a = h.get('address') or {}
    base = (street(h) + ' ' if street(h) else 'home ') + f"{town_of(h)} {a.get('state') or 'SD'} {a.get('postalCode') or ''}"
    return f"/homes/{slugify(base)}-{h['mlsId']}/"

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

def card(h, href, es=False):
    p, ph = h.get('property') or {}, (h.get('photos') or [None])[0]
    dom = (h.get('mls') or {}).get('daysOnMarket')
    tag = ('<span class="lp-new">' + ('Nueva' if es else 'New') + '</span>') if dom is not None and dom <= 7 else ''
    bd = f"{p.get('bedrooms') or 0} {'rec' if es else 'bd'} · {baths(p) or 0} {'baños' if es else 'ba'}" + (f" · {p['area']:,} {'pies²' if es else 'sq ft'}" if p.get('area') else '')
    where = (street(h) + ', ' if street(h) else '') + town_of(h)
    alt = ('Casa en venta: ' if es else 'Home for sale: ') + where
    return (f'<a class="lp-card" href="{href}">'
            + (f'<span class="lp-img"><img src="{e(ph)}" alt="{e(alt)}" loading="lazy" width="400" height="267">{tag}</span>' if ph else f'<span class="lp-img lp-noimg">{tag}</span>')
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
.lp-btn.gold{background:var(--gold);border-color:var(--gold);color:#fff}
.lp-sec{margin:30px 0}.lp-sec h2{font-size:1.5rem;margin-bottom:10px}
.lp-facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:6px 24px;list-style:none;padding:0}
.lp-facts li{border-bottom:1px solid var(--line);padding:7px 0}
.lp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px;margin:22px 0}
.lp-card{display:block;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;color:var(--ink);text-decoration:none}
.lp-card:hover{box-shadow:0 8px 24px rgba(19,32,59,.12)}
.lp-img{display:block;position:relative;aspect-ratio:3/2;background:#e9e3d8}
.lp-img{overflow:hidden}.lp-img img{width:100%;height:100%;object-fit:cover;display:block}
.lp-new{position:absolute;left:10px;top:10px;background:var(--gold);color:#fff;font-size:12px;padding:3px 8px;border-radius:6px}
.lp-body{display:flex;flex-direction:column;gap:2px;padding:12px 14px}
.lp-body b{font-size:1.25rem;color:var(--navy)}.lp-body small{color:#555;margin-top:6px;line-height:1.4}
.lp-towns{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}
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
.lp-alert button{grid-column:1/-1;font:inherit;font-weight:500;background:var(--gold);color:#fff;border:0;border-radius:10px;padding:13px;cursor:pointer}
.lp-alert .msg{grid-column:1/-1;margin:0;min-height:1em}
.lp-foot{font-size:.8rem;color:#666}
</style>
'''

ALERT_JS = """<script>
(function () {
  var URL_ = '""" + ALERTS_URL + """', RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  function getAid() { try { var v = localStorage.getItem('mdAlertId'); return RE.test(v || '') ? v : ''; } catch (e) { return ''; } }
  function newId() { return (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) { var r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); }); }
  var f = document.getElementById('lp-al'); if (!f) return;
  var aid = getAid();
  if (aid) { var v = new URLSearchParams(); v.set('action', 'view'); v.set('id', aid); v.set('mlsId', f.dataset.mls); fetch(URL_, { method: 'POST', mode: 'no-cors', body: v, keepalive: true }).catch(function () {}); }
  var msg = f.querySelector('.msg');
  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var name = f.name.value.trim(), email = f.email.value.trim();
    if (!name || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(email)) { msg.textContent = 'Please add your name and a good email.'; return; }
    if (!f.consent.checked) { msg.textContent = 'Please check the box so I can email you.'; return; }
    var d = new URLSearchParams(), id = getAid() || newId();
    d.set('name', name); d.set('email', email); d.set('phone', f.phone.value.trim()); d.set('freq', 'Daily'); d.set('consent', 'yes');
    d.set('botcheck', f.botcheck.value); d.set('id', id); d.set('lang', 'en'); d.set('source', location.href.slice(0, 200));
    d.set('q', f.dataset.q); d.set('minprice', f.dataset.min); d.set('maxprice', f.dataset.max); d.set('minbeds', f.dataset.beds); d.set('type', f.dataset.type);
    f.querySelector('button').disabled = true;
    fetch(URL_, { method: 'POST', mode: 'no-cors', body: d }).then(function () {
      try { localStorage.setItem('mdAlertId', id); } catch (e) {}
      f.innerHTML = '<p style="grid-column:1/-1;margin:0;color:#fff"><b>You’re all set!</b> Check your email. I sent you the homes that match right now.</p>';
    }).catch(function () { msg.textContent = 'That didn’t go through. Please try again, or text me at 605-838-9140.'; f.querySelector('button').disabled = false; });
  });
})();
</script>"""

def disclaimer(es, updated):
    if es:
        return ('La información se considera confiable pero no está garantizada y debe verificarse. '
                + (f'Información actualizada el {e(updated)}. ' if updated else '')
                + 'Las casas son cortesía de la oficina indicada en cada una. Información de las casas proporcionada por el MLS de la REALTOR® Association of the Sioux Empire.')
    return ('Listing information is deemed reliable but not guaranteed and should be independently verified. '
            + (f'Listing data last updated {e(updated)}. ' if updated else '')
            + 'Listings shown are courtesy of the listing brokerage named on each listing. Listing data provided by the REALTOR® Association of the Sioux Empire MLS.')

# ---------- One page per home ----------
def home_page(h, same_town, updated):
    p, a, s, tx, ass, m = (h.get(k) or {} for k in ('property', 'address', 'school', 'tax', 'association', 'mls'))
    st, town = street(h), town_of(h)
    full = (st + ', ' if st else '') + f"{town}, {a.get('state') or 'SD'} {a.get('postalCode') or ''}".strip()
    url = url_of(h); path = url.strip('/') + '/index.html'
    price = money(h.get('listPrice'))
    bd, ba, sq = p.get('bedrooms') or 0, baths(p), p.get('area')
    kind = p.get('subTypeText') or {'RES': 'Home', 'CND': 'Condo/townhome'}.get(p.get('type'), 'Home')
    title = f"{st or kind + ' for sale'}, {town}, SD {a.get('postalCode') or ''} | {price} | {bd} bd".strip()
    desc = (f"{price} · {bd} bed, {ba} bath" + (f", {sq:,} sq ft" if sq else '') + f" {kind.lower()} for sale in {town}, SD"
            + (f" (MLS #{h.get('listingId')})" if h.get('listingId') else '') + '. See photos, details and schedule a showing with Marcos Diaz, Keller Williams Realty Sioux Falls.')
    photos = h.get('photos') or []
    gal = ''.join(f'<img src="{e(u)}" alt="{e(("Photo %d of " % (i + 1)) + full)}" width="1200" height="800"' + (' loading="lazy"' if i else ' fetchpriority="high"') + '>'
                  for i, u in enumerate(photos[:7]))
    live = f"/search/#home={h['mlsId']}"
    book = BOOK + '?' + urllib.parse.urlencode({'a1': 'Home: ' + (st or 'MLS #' + str(h.get('listingId'))) + ', ' + town + (f" (MLS #{h.get('listingId')})" if h.get('listingId') else '')})
    sms = 'sms:+16058389140?&body=' + urllib.parse.quote(f"Hi Marcos, I'd like to see {st or 'MLS #' + str(h.get('listingId'))}" + (f" (MLS #{h.get('listingId')})" if h.get('listingId') else ''))
    dom = m.get('daysOnMarket')
    facts = [('Bedrooms', bd), ('Full baths', p.get('bathsFull')), ('3/4 baths', p.get('bathsThreeQuarter')), ('Half baths', p.get('bathsHalf')),
             ('Finished sq ft', sq and f'{sq:,}'), ('Price per sq ft', sq and h.get('listPrice') and money(h['listPrice'] / sq)), ('Type', kind), ('Style', p.get('style')),
             ('Year built', p.get('yearBuilt')), ('Stories', p.get('stories')), ('Garage', p.get('garageSpaces') and '%d-car' % round(p['garageSpaces'])),
             ('Lot', lot(p)), ('Heating', p.get('heating')), ('Cooling', p.get('cooling')), ('Foundation', p.get('foundation')),
             ('Flooring', as_list(p.get('flooring'))), ('Interior', as_list(p.get('interiorFeatures'))), ('Outside', as_list(p.get('exteriorFeatures'))),
             ('Subdivision', p.get('subdivision')), ('County', (h.get('geo') or {}).get('county')),
             ('Yearly taxes', tx.get('taxAnnualAmount') and money(tx['taxAnnualAmount']) + (f" ({tx['taxYear']})" if tx.get('taxYear') else '')),
             ('HOA', ass.get('fee') and money(ass['fee']) + (f" / {str(ass.get('frequency')).lower()}" if ass.get('frequency') else '')),
             ('Days on market', dom), ('MLS #', h.get('listingId'))]
    facts_html = ''.join(f'<li>{k}: <b>{e(v)}</b></li>' for k, v in facts if v not in (None, '', 0))
    schools = [('School district', s.get('district')), ('Elementary', s.get('elementarySchool')), ('Middle', s.get('middleSchool')), ('High', s.get('highSchool'))]
    schools_html = ''.join(f'<li>{k}: <b>{e(v)}</b></li>' for k, v in schools if v)
    tslug = TOWNS.get(town, (slugify(town + ' sd'), None))[0]
    tlink = f'/homes-for-sale/{tslug}/' if (town in TOWNS or len(same_town) >= 3) else '/homes-for-sale/'
    more = [x for x in same_town if x['mlsId'] != h['mlsId']]
    lp = h.get('listPrice') or 0
    more.sort(key=lambda x: abs((x.get('listPrice') or 0) - lp))
    more_html = ''.join(card(x, url_of(x)) for x in more[:4])
    ld = {'@context': 'https://schema.org', '@type': 'RealEstateListing', 'name': full, 'url': SITE + url, 'description': desc,
          'image': photos[:5], 'datePosted': (h.get('listDate') or '')[:10] or None,
          'offers': {'@type': 'Offer', 'price': lp, 'priceCurrency': 'USD', 'availability': 'https://schema.org/InStock'},
          'about': {'@type': 'SingleFamilyResidence' if p.get('type') != 'CND' else 'Apartment',
                    'address': {'@type': 'PostalAddress', 'streetAddress': st or None, 'addressLocality': town, 'addressRegion': a.get('state') or 'SD', 'postalCode': a.get('postalCode')},
                    'numberOfBedrooms': bd or None, 'numberOfBathroomsTotal': float(ba) if ba else None,
                    'floorSize': {'@type': 'QuantitativeValue', 'value': sq, 'unitCode': 'FTK'} if sq else None,
                    'yearBuilt': p.get('yearBuilt')},
          'broker': {'@type': 'RealEstateAgent', 'name': 'Marcos Diaz, Keller Williams Realty Sioux Falls', 'telephone': '+1-605-838-9140'}}
    if (h.get('geo') or {}).get('lat') and show_addr(h):
        ld['about']['geo'] = {'@type': 'GeoCoordinates', 'latitude': h['geo']['lat'], 'longitude': h['geo']['lng']}
    strip = lambda o: {k: strip(v) for k, v in o.items() if v not in (None, '', [])} if isinstance(o, dict) else o
    head = CSS + '<script type="application/ld+json">' + json.dumps(strip(ld)).replace('</', '<\\/') + '</script>\n'
    remarks = h.get('remarks') or ''
    mo = payment(h)
    pay_html = ''
    if mo:
        pay_html += (f'<div class="lp-box"><h3>Estimated payment</h3><div class="big">{money(mo)}/mo*</div>'
                     f'<small>Principal, interest, taxes and insurance. <a href="/?price={int(lp)}#calculator">Change the numbers →</a></small></div>')
    if is_dpa(h):
        five = round(lp * 0.95 * 0.05 / 100) * 100
        pay_html += (f'<div class="lp-box lp-g5"><h3>First-time buyer?</h3><p style="margin:0">This price is under the {money(DPA_LIMIT)} limit for South Dakota’s '
                     f'<b>Give Me Five</b> program: up to 5% of your loan (about {money(five)}) toward your down payment, if you qualify.</p>'
                     f'<small><a href="/blog/give-me-five-down-payment-assistance/">See who qualifies →</a></small></div>')
    pay_html = f'<div class="lp-pay">{pay_html}</div>' if pay_html else ''
    ptype = 'condominium' if p.get('type') == 'CND' else 'residential'
    alert_html = f'''<div class="lp-alert" id="alerts"><h2>Get new homes like this by email</h2>
      <p style="margin:0">New {e(town)} homes around {money(lp)}{f" with {bd}+ bedrooms" if bd else ""}, sent to you as soon as they hit the market. Free, and you can stop anytime.</p>
      <form id="lp-al" novalidate data-q="{e(town)}" data-min="{int(round(lp * 0.8, -4))}" data-max="{int(round(lp * 1.2, -4))}" data-beds="{bd or ''}" data-type="{ptype}" data-mls="{h['mlsId']}">
        <input type="text" name="name" placeholder="Name" aria-label="Name" autocomplete="name" maxlength="100">
        <input type="email" name="email" placeholder="Email" aria-label="Email" autocomplete="email" maxlength="120">
        <input type="tel" name="phone" placeholder="Phone (optional)" aria-label="Phone (optional)" autocomplete="tel" maxlength="40">
        <input type="text" name="botcheck" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
        <label class="ok"><input type="checkbox" name="consent" value="yes"><span>Yes, email me new listings from Marcos Diaz, and use the homes I open on this site to fine-tune my alerts. If I add my phone, Marcos may call or text me about homes. I can unsubscribe anytime. <a href="/privacy.html" target="_blank">Privacy</a></span></label>
        <button type="submit">Start my alerts</button><p class="msg" role="alert"></p>
      </form></div>'''
    body = f'''  <section class="lp-hero"><div class="lp-wrap">
    <p class="lp-crumbs"><a href="/">Home</a> / <a href="/homes-for-sale/">Homes for sale</a> / <a href="{tlink}">{e(town)}</a></p>
    <h1>{e(full)}</h1>
    <div class="lp-price">{price}</div>
    <div class="lp-stats"><span>{bd} beds</span><span>{ba or 0} baths</span>{f"<span>{sq:,} sq ft</span>" if sq else ""}<span>{e(kind)}</span>{f"<span>Built {p['yearBuilt']}</span>" if p.get('yearBuilt') else ""}</div>
  </div></section>
  <section class="lp-body-sec"><div class="lp-wrap">
    <p class="lp-attr">Listing courtesy of {e(attribution(h))}</p>
    {pay_html}
    {f'<div class="lp-gal">{gal}</div>' if gal else ''}
    <p><a href="{live}">See all {len(photos)} photos, the map and drive times →</a></p>
    <div class="lp-btns">
      <a class="lp-btn gold" href="{e(book)}" target="_blank" rel="noopener">Request a showing</a>
      <a class="lp-btn" href="tel:+16058389140">Call 605-838-9140</a>
      <a class="lp-btn" href="{e(sms)}">Text Marcos</a>
      <a class="lp-btn" href="/?price={int(lp)}#calculator">What would my payment be?</a>
    </div>
    {f'<div class="lp-sec"><h2>About this home</h2><p>{e(remarks)}</p></div>' if remarks else ''}
    <div class="lp-sec"><h2>Facts &amp; features</h2><ul class="lp-facts">{facts_html}</ul></div>
    {f'<div class="lp-sec"><h2>Schools</h2><ul class="lp-facts">{schools_html}</ul><p><small>Always confirm schools with the district for a specific address.</small></p></div>' if schools_html else ''}
    <div class="lp-sec"><h2>Thinking about this home?</h2><p>I'm Marcos Diaz, a Broker Associate with Keller Williams Realty Sioux Falls. I can tell you what's around it, what similar homes sold for, and whether it's priced right. I'm bilingual, so we can talk in English or Spanish. Call or text <a href="tel:+16058389140">605-838-9140</a>.</p></div>
    {alert_html}
    {f'<div class="lp-sec"><h2>More homes for sale in {e(town)}</h2><div class="lp-grid">{more_html}</div><p><a href="{tlink}">See more homes for sale →</a></p></div>' if more_html else ''}
    <p class="lp-disc">{e(h.get("disclaimer") or "")} {disclaimer(False, updated)}</p>
    {f'<p class="lp-foot">*{e(pay_note())}</p>' if mo else ''}
  </div></section>
{ALERT_JS}
'''
    _page(path, title, desc, body, canonical=SITE + url, head_extra=head, news=False)
    if photos:
        fp = os.path.join(ROOT, path); doc = open(fp).read()
        doc = re.sub(r'<meta property="og:image" content="[^"]*">', lambda m: f'<meta property="og:image" content="{e(photos[0])}">\n<meta property="og:image:alt" content="{e(full)}">', doc, count=1)
        open(fp, 'w').write(doc)
    return url

# ---------- Town pages (EN + ES) ----------
def town_page(town, slug, homes, updated, es):
    homes = sorted(homes, key=lambda x: (x.get('listDate') or ''), reverse=True)
    prices = sorted(x['listPrice'] for x in homes if x.get('listPrice'))
    med = prices[len(prices) // 2] if prices else 0
    new7 = sum(1 for x in homes if ((x.get('mls') or {}).get('daysOnMarket') or 99) <= 7)
    area = next((v[1] for k, v in TOWNS.items() if v[0] == slug), None)
    en_url, es_url = f'/homes-for-sale/{slug}/', f'/es/casas-en-venta/{slug}/'
    url = es_url if es else en_url
    search = ('/es/buscar-casas/' if es else '/search/') + '?q=' + urllib.parse.quote(town)
    if es:
        title = f'Casas en venta en {town}, SD | {len(homes)} casas | Marcos Diaz'
        desc = f'Vea {len(homes)} casas en venta en {town}, SD, con fotos y precios del MLS. Agente que habla español: Marcos Diaz, Keller Williams Realty Sioux Falls.'
        cards = ''.join(card(x, f"/es/buscar-casas/#home={x['mlsId']}", True) for x in homes[:MAX_TOWN_CARDS])
        lead = f'{len(homes)} casas en venta ahora' + (f' · precio medio {money(med)}' if med else '') + (f' · {new7} nuevas esta semana' if new7 else '')
        body = f'''  <section class="lp-hero"><div class="lp-wrap">
    <p class="lp-crumbs"><a href="/es/">Inicio</a> / <a href="/es/casas-en-venta/">Casas en venta</a> / {e(town)}</p>
    <h1>Casas en venta en {e(town)}, SD</h1><p>{lead}</p>
  </div></section>
  <section class="lp-body-sec"><div class="lp-wrap">
    <div class="lp-btns"><a class="lp-btn gold" href="{e(search)}">Ver todas en el mapa</a>{f'<a class="lp-btn" href="/es/areas/{area}.html">Conozca {e(town)}</a>' if area else ''}<a class="lp-btn" href="tel:+16058389140">Llame o envíe un texto: 605-838-9140</a></div>
    {f'<div class="lp-grid">{cards}</div>' if cards else f'<p>No hay casas en venta en {e(town)} en este momento. Llámeme o envíeme un texto y le aviso cuando salga una.</p>'}
    {f'<p><a href="{e(search)}">Ver las {len(homes)} casas en el mapa →</a></p>' if len(homes) > MAX_TOWN_CARDS else ''}
    <p class="lp-disc">{disclaimer(True, updated)}</p>
    {f'<p class="lp-foot">*{e(pay_note(True))}</p>' if homes else ''}
  </div></section>
'''
    else:
        title = f'{town}, SD Homes for Sale | {len(homes)} Listings | Marcos Diaz'
        desc = f'See {len(homes)} homes for sale in {town}, SD with photos, prices and details from the MLS. Updated daily. Marcos Diaz, Keller Williams Realty Sioux Falls.'
        cards = ''.join(card(x, url_of(x)) for x in homes[:MAX_TOWN_CARDS])
        lead = f'{len(homes)} homes for sale right now' + (f' · median price {money(med)}' if med else '') + (f' · {new7} new this week' if new7 else '')
        body = f'''  <section class="lp-hero"><div class="lp-wrap">
    <p class="lp-crumbs"><a href="/">Home</a> / <a href="/homes-for-sale/">Homes for sale</a> / {e(town)}</p>
    <h1>Homes for Sale in {e(town)}, SD</h1><p>{lead}</p>
  </div></section>
  <section class="lp-body-sec"><div class="lp-wrap">
    <div class="lp-btns"><a class="lp-btn gold" href="{e(search)}">See them all on the map</a>{f'<a class="lp-btn" href="/areas/{area}.html">Living in {e(town)}</a>' if area else ''}<a class="lp-btn" href="tel:+16058389140">Call or text 605-838-9140</a></div>
    {f'<div class="lp-grid">{cards}</div>' if cards else f'<p>No homes are for sale in {e(town)} right now. Call or text me and I’ll let you know as soon as one comes up.</p>'}
    {f'<p><a href="{e(search)}">See all {len(homes)} homes on the map →</a></p>' if len(homes) > MAX_TOWN_CARDS else ''}
    <p class="lp-disc">{disclaimer(False, updated)}</p>
    {f'<p class="lp-foot">*{e(pay_note())}</p>' if homes else ''}
  </div></section>
'''
    alts = (f'<link rel="alternate" hreflang="en" href="{SITE}{en_url}">\n<link rel="alternate" hreflang="es" href="{SITE}{es_url}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}{en_url}">\n')
    _page(url.strip('/') + '/index.html', title, desc, body, lang='es' if es else 'en', canonical=SITE + url,
          alt_es=es_url, alt_en=en_url, head_extra=CSS + alts)
    return url

def hub_page(by_town, es):
    order = sorted(by_town, key=lambda t: (t != 'Sioux Falls', -len(by_town[t]), t))
    base = '/es/casas-en-venta/' if es else '/homes-for-sale/'
    links = ''.join(f'<a href="{base}{TOWNS.get(t, (slugify(t + " sd"),))[0]}/">{e(t)} <b>({len(by_town[t])})</b></a>' for t in order if by_town[t])
    total = sum(len(v) for v in by_town.values())
    if es:
        title, desc = 'Casas en venta en Sioux Falls y pueblos cercanos | Marcos Diaz', f'{total} casas en venta en Sioux Falls, Tea, Harrisburg, Brandon y más. Escoja un pueblo para ver fotos y precios.'
        body = f'<section class="lp-hero"><div class="lp-wrap"><h1>Casas en venta por pueblo</h1><p>{total} casas en venta ahora en Sioux Falls y pueblos cercanos.</p></div></section><section class="lp-body-sec"><div class="lp-wrap"><div class="lp-towns">{links}</div><div class="lp-btns"><a class="lp-btn gold" href="/es/buscar-casas/">Buscar en el mapa</a></div></div></section>\n'
    else:
        title, desc = 'Homes for Sale in Sioux Falls & Nearby Towns | Marcos Diaz', f'{total} homes for sale in Sioux Falls, Tea, Harrisburg, Brandon and nearby towns. Pick a town to see photos and prices.'
        body = f'<section class="lp-hero"><div class="lp-wrap"><h1>Homes for Sale by Town</h1><p>{total} homes for sale right now in Sioux Falls and nearby towns.</p></div></section><section class="lp-body-sec"><div class="lp-wrap"><div class="lp-towns">{links}</div><div class="lp-btns"><a class="lp-btn gold" href="/search/">Search on the map</a></div></div></section>\n'
    alts = (f'<link rel="alternate" hreflang="en" href="{SITE}/homes-for-sale/">\n<link rel="alternate" hreflang="es" href="{SITE}/es/casas-en-venta/">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/homes-for-sale/">\n')
    _page(base.strip('/') + '/index.html', title, desc, body, lang='es' if es else 'en', canonical=SITE + base,
          alt_es='/es/casas-en-venta/', alt_en='/homes-for-sale/', head_extra=CSS + alts)
    return base

# ---------- Main ----------
def main():
    raw = fetch_listings()
    homes = [h for h in raw if h.get('mlsId') and h.get('internetEntireListingDisplay') is not False and town_of(h)
             and str((h.get('mls') or {}).get('status') or 'Active').replace(' ', '').lower() in ('active', 'activeundercontract', '')]
    if not homes: sys.exit('No listings could be shown – stopping so the site is not emptied.')
    updated = last_update()
    by_town = defaultdict(list)
    for h in homes: by_town[town_of(h)].append(h)
    urls = []
    for t, hs in by_town.items():
        for h in hs: urls.append((home_page(h, hs, updated), (h.get('modified') or '')[:10]))
    # town pages: every town with an area page (even with no homes today), plus any other town with 3+ homes
    for t in TOWNS: by_town.setdefault(t, [])
    for t, hs in by_town.items():
        if t in TOWNS or len(hs) >= 3:
            slug = TOWNS.get(t, (slugify(t + ' sd'),))[0]
            urls.append((town_page(t, slug, hs, updated, False), ''))
            urls.append((town_page(t, slug, hs, updated, True), ''))
    shown = {t: hs for t, hs in by_town.items() if t in TOWNS or len(hs) >= 3}
    urls += [(hub_page(shown, False), ''), (hub_page(shown, True), '')]

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
    print(f'Listing pages: {len(homes)} homes, {len(shown)} towns, {len(urls)} URLs in homes-sitemap.xml')

if __name__ == '__main__':
    main()
