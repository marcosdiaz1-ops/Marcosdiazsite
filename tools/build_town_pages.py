# Rebuilds the town pages (areas/*.html and es/areas/*.html) in the "neighborhood guide" layout:
# full-width photo hero, live homes for sale in that town, Census overview, living there, map,
# schools by level, common questions, explore other towns, then the newsletter + footer.
# Reads the text that is already on each page (living, what to know, schools, FAQ, side card),
# so edits to that text are kept. Safe to run again: a page already in the new layout is rebuilt
# from the copy of its text saved in data/town_text/.
import os, re, json, html, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE = os.path.join(ROOT, 'data', 'town_text')

# Town -> (MLS city name, Census key, school district, map box [south, west, north, east])
TOWNS = {
 'sioux-falls':           ('Sioux Falls', 'Sioux Falls', 'Sioux Falls',    (43.465, -96.860, 43.625, -96.610)),
 'southwest-sioux-falls': ('Sioux Falls', 'Sioux Falls', 'Sioux Falls',    (43.460, -96.870, 43.545, -96.730)),
 'southeast-sioux-falls': ('Sioux Falls', 'Sioux Falls', 'Sioux Falls',    (43.460, -96.750, 43.545, -96.610)),
 'tea':                   ('Tea',         'Tea',         'Tea Area',       (43.430, -96.865, 43.475, -96.800)),
 'harrisburg':            ('Harrisburg',  'Harrisburg',  'Harrisburg',     (43.410, -96.730, 43.455, -96.665)),
 'brandon':               ('Brandon',     'Brandon',     'Brandon Valley', (43.575, -96.610, 43.615, -96.540)),
 'garretson':             ('Garretson',   'Garretson',   'Garretson',      (43.705, -96.520, 43.730, -96.485)),
 'hartford':              ('Hartford',    'Hartford',    'West Central',   (43.610, -96.965, 43.637, -96.920)),
 'crooks':                ('Crooks',      'Crooks',      'Tri-Valley',     (43.652, -96.830, 43.677, -96.792)),
 'lennox':                ('Lennox',      'Lennox',      'Lennox',         (43.342, -96.910, 43.367, -96.873)),
 'canton':                ('Canton',      'Canton',      'Canton',         (43.287, -96.615, 43.315, -96.570)),
}
# Shown in the "Explore other towns" strip (SW/SE Sioux Falls pages still exist but aren't listed here)
STRIP = ['sioux-falls', 'tea', 'harrisburg', 'brandon', 'garretson', 'hartford', 'crooks', 'lennox', 'canton']
NAMES = {'sioux-falls': 'Sioux Falls', 'tea': 'Tea', 'harrisburg': 'Harrisburg', 'brandon': 'Brandon', 'garretson': 'Garretson',
         'hartford': 'Hartford', 'crooks': 'Crooks', 'lennox': 'Lennox', 'canton': 'Canton',
         'southwest-sioux-falls': 'Southwest Sioux Falls', 'southeast-sioux-falls': 'Southeast Sioux Falls'}
NAMES_ES = dict(NAMES, **{'southwest-sioux-falls': 'Suroeste de Sioux Falls', 'southeast-sioux-falls': 'Sureste de Sioux Falls'})

# U.S. Census Bureau, American Community Survey 2024 5-year estimates (via Census Reporter)
ACS = 'ACS 2024 5-year'
CENSUS = {
 'Sioux Falls': dict(pop=201469, age=35.5, inc=75970, val=292400, own=59.5, hh=85992, rent=1035, yr=1993, ba=38.1),
 'Tea':         dict(pop=6786, age=30.6, inc=120139, val=351100, own=79.7, hh=2171, rent=1220, yr=2004, ba=47.1),
 'Harrisburg':  dict(pop=8519, age=31.1, inc=108724, val=312200, own=78.4, hh=3008, rent=1362, yr=2008, ba=43.8),
 'Brandon':     dict(pop=10996, age=36.7, inc=110806, val=336600, own=80.1, hh=4072, rent=976, yr=2001, ba=41.9),
 'Garretson':   dict(pop=1176, age=48.5, inc=59741, val=203800, own=62.7, hh=568, rent=697, yr=1973, ba=28.2),
 'Hartford':    dict(pop=3478, age=39.5, inc=99893, val=257700, own=76.8, hh=1373, rent=938, yr=1997, ba=34.3),
 'Crooks':      dict(pop=1268, age=43.6, inc=98984, val=295400, own=83.2, hh=501, rent=1135, yr=1991, ba=36.5),
 'Lennox':      dict(pop=2468, age=38.0, inc=81761, val=235900, own=74.3, hh=983, rent=745, yr=1977, ba=24.1),
 'Canton':      dict(pop=3033, age=42.2, inc=60850, val=191400, own=68.1, hh=1409, rent=673, yr=1960, ba=16.9),
}

# Free photos from Wikimedia Commons: (file, author, license, license url)
PHOTOS = {
 'sioux-falls': ("Sioux_Falls_Skyline_and_Falls_Park_03-20-23_(cropped).jpg", "Maxpower2727", "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0"),
 'southwest-sioux-falls': ("Falls_Park,_Sioux_Falls,_SD_-_53746880624.jpg", "w_lemay", "CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0"),
 'southeast-sioux-falls': ("Downtown_Sioux_Falls_in_the_evening.jpg", "Maxpower2727", "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0"),
 'tea': ("Tea_Area_High_School.jpg", "WavingDolphin", "CC0", ""),
 'harrisburg': ("DAIR_3024,_Harrisburg_-_Flickr_-_chief_huddleston.jpg", "Jerry Huddleston", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0"),
 'brandon': ("Big_Sioux_River_at_Big_Sioux_Recreation_Area,_Brandon,_South_Dakota.jpg", "Votesmall", "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0"),
 'garretson': ("Palisades_Along_Split_Rock_Creek_-_Garretson,_South_Dakota_(8-30-26).jpg", "ToxicFlame427", "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0"),
 'hartford': ("Hartford,_South_Dakota_5.jpg", "Jon Platek", "CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0"),
 'crooks': None,
 'lennox': ("Lennox,_South_Dakota_5.jpg", "Jon Platek", "CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0"),
 'canton': ("Canton,_South_Dakota_5.jpg", "AlexiusHoratius", "CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0"),
}
def photo(slug, w):
    p = PHOTOS.get(slug)
    return 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(p[0]) + f'?width={w}' if p else ''

SCHOOLS = json.load(open(os.path.join(ROOT, 'data', 'schools.json')))
LEVEL = {'E': 0, 'M': 1, 'H': 2}

def T(es, en, sp): return sp if es else en
def money(n): return '${:,.0f}'.format(n)
def num(n): return '{:,}'.format(n)

def extract(doc):
    """Pull the text blocks out of an old-layout page."""
    g = lambda pat: (re.search(pat, doc, re.S) or [None, ''])[1]
    prose = g(r'<div class="prose">(.*?)\n        <h3 class="sub"')
    parts = re.split(r'\n        <h2>', '\n' + prose)
    sec = {}
    for p in parts:
        if not p.strip(): continue
        h, _, body = p.partition('</h2>')
        sec[h.strip()] = body.strip()
    keys = list(sec)
    return dict(
        crumbs=g(r'<p class="crumbs">(.*?)</p>'),
        h1=g(r'<h1>(.*?)</h1>'), lead=g(r'<p class="lead">(.*?)</p>'),
        living=(keys[0], sec[keys[0]]), know=(keys[1], sec[keys[1]]), schools=(keys[2], sec[keys[2]]),
        faq=(keys[3], sec[keys[3]]), cta=(keys[4], sec[keys[4]]),
        side=g(r'(<aside class="side-card">.*?</aside>)'),
    )

def stats(es, d):
    items = [
        (num(d['pop']), T(es, 'Population', 'Población')),
        (f"{d['age']:g}", T(es, 'Median age', 'Edad media')),
        (money(d['inc']), T(es, 'Median household income', 'Ingreso medio por hogar')),
        (money(d['val']), T(es, 'Median home value', 'Valor medio de las casas')),
        (f"{d['own']:g}%", T(es, 'Own their home', 'Son dueños de su casa')),
        (num(d['hh']), T(es, 'Households', 'Hogares')),
        (money(d['rent']) + T(es, '/mo', '/mes'), T(es, 'Median rent', 'Renta media')),
        (str(d['yr']), T(es, 'Typical year built', 'Año típico de construcción')),
    ]
    return ''.join(f'<div class="tp-stat"><b>{v}</b><span>{l}</span></div>' for v, l in items)

def schools_html(es, district):
    lists = [[], [], []]
    for name, lvl, grades, dist, la, lo in SCHOOLS['pub']:
        if dist == district and lvl in LEVEL:
            lists[LEVEL[lvl]].append((name, grades))
    heads = [T(es, 'Elementary', 'Primaria'), T(es, 'Middle', 'Secundaria'), T(es, 'High school', 'Preparatoria')]
    cols = []
    for h, items in zip(heads, lists):
        if not items: continue
        lis = ''.join(f'<li>{html.escape(n)} <small>{html.escape(gr)}</small></li>' for n, gr in sorted(items))
        cols.append(f'<div class="tp-school"><h3>{h} <span>({len(items)})</span></h3><ul>{lis}</ul></div>')
    return ''.join(cols)

def faq_html(body):
    qa = re.findall(r'<h3>(.*?)</h3>\s*<p>(.*?)</p>', body, re.S)
    return ''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in qa)

def build(slug, es):
    path = os.path.join(ROOT, 'es' if es else '', 'areas', f'{slug}.html')
    doc = open(path, encoding='utf-8').read()
    save = os.path.join(SAVE, ('es-' if es else '') + slug + '.json')
    if 'class="town-page"' in doc:
        t = json.load(open(save))
    else:
        t = extract(doc)
        os.makedirs(SAVE, exist_ok=True)
        json.dump(t, open(save, 'w'), ensure_ascii=False, indent=1)
    city, ckey, district, box = TOWNS[slug]
    name = (NAMES_ES if es else NAMES)[slug]
    d = CENSUS[ckey]
    up = '../../' if es else '../'
    tslug = city.lower().replace(' ', '-') + '-sd'
    allhomes = T(es, f'/homes-for-sale/{tslug}/', f'/es/casas-en-venta/{tslug}/')
    sub = slug in ('southwest-sioux-falls', 'southeast-sioux-falls')
    s_, w_, n_, e_ = box
    points = f'data-points="{n_:.4f},{w_:.4f}|{n_:.4f},{e_:.4f}|{s_:.4f},{e_:.4f}|{s_:.4f},{w_:.4f}"' if sub else f'data-cities="{city}"'
    ph = photo(slug, 1800)
    hero_bg = f' style="background-image:url(\'{ph}\')"' if ph else ''
    pc = PHOTOS.get(slug)
    credit = ''
    if pc:
        lic = f'<a href="{pc[3]}" rel="nofollow noopener" target="_blank">{pc[2]}</a>' if pc[3] else pc[2]
        credit = f'<p class="tp-credit">{T(es, "Photo", "Foto")}: <a href="https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(pc[0])}" rel="nofollow noopener" target="_blank">{html.escape(pc[1])}</a>, {lic}</p>'
    census_note = T(es, f'Source: U.S. Census Bureau, American Community Survey ({ACS} estimates), city of {city}.',
                    f'Fuente: Oficina del Censo de EE. UU., American Community Survey (estimados {ACS}), ciudad de {city}.')
    if sub:
        census_note += T(es, ' These numbers are for all of Sioux Falls.', ' Estos números son de todo Sioux Falls.')
    intro = T(es, f"{num(d['pop'])} people live in {city}, where the median age is {d['age']:g} and the median home value is {money(d['val'])}.",
              f"En {city} viven {num(d['pop'])} personas. La edad media es {d['age']:g} años y el valor medio de las casas es {money(d['val'])}.")
    mapsrc = f'https://www.openstreetmap.org/export/embed.html?bbox={w_}%2C{s_}%2C{e_}%2C{n_}&amp;layer=mapnik'
    maplink = f'https://www.openstreetmap.org/?#map=14/{(s_+n_)/2:.4f}/{(w_+e_)/2:.4f}'
    others = []
    for o in STRIP:
        if o == slug: continue
        img = f'<img src="{photo(o, 600)}" alt="" loading="lazy" width="600" height="450">' if PHOTOS.get(o) else f'<span class="tp-blank"><img src="{up}images/logo.svg" alt="" width="56" height="56"></span>'
        others.append(f'<a href="{o}.html" class="tp-other"><span class="tp-oimg">{img}</span><span class="tp-oname">{(NAMES_ES if es else NAMES)[o]}</span></a>')
    living_h, living = t['living']; know_h, know = t['know']; sch_h, sch = t['schools']; faq_h, faq = t['faq']; cta_h, cta = t['cta']
    main = f'''<main class="town-page">
  <section class="tp-hero{' tp-noimg' if not ph else ''}"{hero_bg}>
    <div class="wrap">
      <p class="crumbs">{t['crumbs']}</p>
      <p class="eyebrow">{T(es, 'Explore', 'Explore')}</p>
      <h1>{t['h1']}</h1>
      <p class="lead">{t['lead']}</p>
      <div class="tp-hero-btns"><a href="{allhomes}" class="btn btn-gold">{T(es, f'See Homes for Sale in {name}', f'Ver casas en venta en {name}')}</a><a href="#tp-listings" class="tp-down" aria-label="{T(es, 'Scroll down', 'Bajar')}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 9l7 7 7-7"/></svg></a></div>
    </div>
    {credit}
  </section>

  <section id="featured" class="featured tp-listings" {points} aria-label="{T(es, f'Homes for sale in {name}', f'Casas en venta en {name}')}">
    <div class="wrap" id="tp-listings">
      <div class="fh-head">
        <div>
          <p class="eyebrow">{T(es, 'Property listings', 'Casas en venta')}</p>
          <h2>{T(es, f'Homes for sale in {name}', f'Casas en venta en {name}')}</h2>
          <p class="fh-sub">{T(es, 'The newest homes on the market, updated from the MLS throughout the day. Tap any home for photos, details and to request a showing.', 'Las casas más nuevas en el mercado, actualizadas del MLS durante el día. Toque una casa para ver fotos, detalles y pedir una visita.')}</p>
          <p class="fh-fallback">{T(es, f'See every home for sale in {name}, then call or text me to see any home you like.', f'Vea todas las casas en venta en {name} y llámeme o envíeme un mensaje para ver la que le guste.')}</p>
        </div>
        <div class="fh-arrows">
          <button type="button" class="fh-nav p" aria-label="{T(es, 'Previous homes', 'Casas anteriores')}">‹</button>
          <button type="button" class="fh-nav n" aria-label="{T(es, 'More homes', 'Más casas')}">›</button>
        </div>
      </div>
      <div class="fh-track"></div>
      <div class="fh-foot"><a href="{allhomes}" class="btn btn-navy">{T(es, f'See All Homes in {name}', f'Ver todas las casas en {name}')}</a></div>
      <p class="fh-disc">{T(es, 'Listing information is deemed reliable but not guaranteed and should be independently verified. Listings shown are courtesy of the listing brokerage named on each listing. Listing data provided by the REALTOR® Association of the Sioux Empire MLS.', 'La información de las casas se considera confiable pero no está garantizada y debe verificarse. Las casas que se muestran son cortesía de la agencia nombrada en cada una. Información proporcionada por el MLS de la REALTOR® Association of the Sioux Empire.')}</p>
    </div>
  </section>

  <section class="tp-sec tp-overview">
    <div class="wrap">
      <div class="tp-head"><p class="eyebrow">{T(es, 'Overview', 'Resumen')}</p><h2>{T(es, f'{name} at a glance', f'{name} en números')}</h2><p>{intro}</p></div>
      <div class="tp-stats">{stats(es, d)}</div>
      <p class="tp-note">{census_note}</p>
    </div>
  </section>

  <section class="tp-sec tp-living">
    <div class="wrap page-grid">
      <div class="prose">
        <h2>{living_h}</h2>
        {living}
        <h2>{know_h}</h2>
        {know}
      </div>
      {t['side']}
    </div>
  </section>

  <section class="tp-sec tp-around">
    <div class="wrap">
      <div class="tp-head"><p class="eyebrow">{T(es, 'Around town', 'Alrededor')}</p><h2>{T(es, f'Around {name}', f'Alrededor de {name}')}</h2></div>
      <div class="tp-map"><iframe title="{T(es, f'Map of {name}', f'Mapa de {name}')}" src="{mapsrc}" loading="lazy"></iframe></div>
      <p class="tp-note"><a href="{maplink}" target="_blank" rel="noopener">{T(es, 'View larger map', 'Ver mapa más grande')}</a> · © OpenStreetMap contributors</p>
    </div>
  </section>

  <section class="tp-sec tp-schools">
    <div class="wrap">
      <div class="tp-head"><p class="eyebrow">{T(es, 'Schools', 'Escuelas')}</p><h2>{T(es, f'Schools in {name}', f'Escuelas en {name}')}</h2>{sch}</div>
      <div class="tp-school-cols">{schools_html(es, district)}</div>
      <p class="tp-note">{T(es, f'Public schools in the {district} School District. Source: U.S. Dept. of Education, NCES. Always confirm the school district for a specific address.', f'Escuelas públicas del distrito escolar {district}. Fuente: Departamento de Educación de EE. UU., NCES. Siempre confirme el distrito escolar de cada dirección.')}</p>
    </div>
  </section>

  <section class="tp-sec tp-faq">
    <div class="wrap tp-narrow">
      <div class="tp-head"><p class="eyebrow">{T(es, 'Common questions', 'Preguntas frecuentes')}</p><h2>{faq_h}</h2></div>
      <div class="faq-list">{faq_html(faq)}</div>
      <h2 class="tp-cta-h">{cta_h}</h2>
      {cta}
    </div>
  </section>

  <section class="tp-others">
    <div class="wrap">
      <div class="tp-head"><p class="eyebrow">{T(es, 'Areas I serve', 'Áreas donde trabajo')}</p><h2>{T(es, 'Explore other towns', 'Explore otros pueblos')}</h2></div>
      <div class="tp-other-row">{''.join(others)}</div>
      <p class="tp-other-all"><a href="{up}{T(es, '', 'es/')}#areas" class="btn btn-gold">{T(es, 'All areas I serve', 'Todas las áreas')}</a></p>
    </div>
  </section>
'''
    # keep everything from the newsletter band onward
    m_start = doc.index('<main')
    tail = doc[doc.index('<section class="news-band">'):] if '<section class="news-band">' in doc else doc[doc.index('</main>'):]
    out = doc[:m_start] + main + tail
    if 'featured.js' not in out:
        out = out.replace(f'<script src="{up}site.js?v=BUILD" defer></script>', f'<script src="{up}site.js?v=BUILD" defer></script>\n<script src="{up}featured.js?v=BUILD" defer></script>', 1)
    open(path, 'w', encoding='utf-8').write(out)

if __name__ == '__main__':
    for slug in TOWNS:
        for es in (False, True):
            build(slug, es)
    print('town pages rebuilt:', len(TOWNS) * 2)
