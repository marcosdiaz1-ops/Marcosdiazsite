"""Build the Spanish home search page from the English one.

  python3 tools/build_es_search.py preview   # search-preview/ -> es/buscar-casas-preview/ (noindex)
  python3 tools/build_es_search.py live      # search/         -> es/buscar-casas/

The Spanish page keeps its own <head> (title, description, canonical), menu and footer from the
current es/buscar-casas/index.html, and translates the search's own text. The search script
switches its words to Spanish by itself when the page says lang="es".
"""
import re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mode = (sys.argv[1:] or ['preview'])[0]
src = os.path.join(ROOT, 'search-preview/index.html' if mode == 'preview' else 'search/index.html')
dst = os.path.join(ROOT, 'es/buscar-casas-preview/index.html' if mode == 'preview' else 'es/buscar-casas/index.html')
shell = open(os.path.join(ROOT, 'es/buscar-casas/index.html')).read()
en = open(src).read()

def grab(pat, text):
    m = re.search(pat, text, re.S); assert m, pat; return m.group(0)

es = en.replace('<html lang="en">', '<html lang="es">', 1)
# head: keep the English page's styles/scripts, use the Spanish title/description/links
es_meta = grab(r'<title>.*?<link rel="alternate" hreflang="x-default"[^\n]*\n', shell)
if mode == 'preview':
    es = re.sub(r'<title>.*?<meta name="robots" content="noindex, nofollow">\n', lambda m: es_meta.split('<meta name="description"')[0] + '<meta name="robots" content="noindex, nofollow">\n', es, count=1, flags=re.S)
else:
    es = re.sub(r'<title>.*?<link rel="alternate" hreflang="x-default"[^\n]*\n', lambda m: es_meta, es, count=1, flags=re.S)
es = re.sub(r'<header.*?</header>', lambda m: grab(r'<header.*?</header>', shell), es, count=1, flags=re.S)
es = re.sub(r'<footer.*?</footer>', lambda m: grab(r'<footer.*?</footer>', shell), es, count=1, flags=re.S)

T = [
 ('placeholder="City, ZIP, address, or MLS #" aria-label="City, ZIP, address, or MLS #"', 'placeholder="Ciudad, código postal, dirección o MLS #" aria-label="Ciudad, código postal, dirección o MLS #"'),
 ('class="sp-qgo" aria-label="Search"', 'class="sp-qgo" aria-label="Buscar"'),
 ('<span id="pl-price">Price</span>', '<span id="pl-price">Precio</span>'),
 ('aria-label="Price">\n              <div class="pop-h">Price range</div>', 'aria-label="Precio">\n              <div class="pop-h">Rango de precio</div>'),
 ('<label>Min<input type="text" inputmode="numeric" id="pp-min" placeholder="No min"></label>', '<label>Mínimo<input type="text" inputmode="numeric" id="pp-min" placeholder="Sin mínimo"></label>'),
 ('<label>Max<input type="text" inputmode="numeric" id="pp-max" placeholder="No max"></label>', '<label>Máximo<input type="text" inputmode="numeric" id="pp-max" placeholder="Sin máximo"></label>'),
 ('<span id="pl-beds">Beds &amp; baths</span>', '<span id="pl-beds">Recámaras y baños</span>'),
 ('aria-label="Beds and baths">\n              <div class="pop-h">Bedrooms</div>', 'aria-label="Recámaras y baños">\n              <div class="pop-h">Recámaras</div>'),
 ('<div class="pop-h">Bathrooms</div>', '<div class="pop-h">Baños</div>'),
 ('data-v="">Any</button><button type="button" data-v="1">1+</button><button type="button" data-v="2">2+</button><button type="button" data-v="3">3+</button><button type="button" data-v="4">4+</button><button type="button" data-v="5">5+</button>', 'data-v="">Todas</button><button type="button" data-v="1">1+</button><button type="button" data-v="2">2+</button><button type="button" data-v="3">3+</button><button type="button" data-v="4">4+</button><button type="button" data-v="5">5+</button>'),
 ('data-v="">Any</button><button type="button" data-v="1">1+</button><button type="button" data-v="2">2+</button><button type="button" data-v="3">3+</button><button type="button" data-v="4">4+</button></div>', 'data-v="">Todos</button><button type="button" data-v="1">1+</button><button type="button" data-v="2">2+</button><button type="button" data-v="3">3+</button><button type="button" data-v="4">4+</button></div>'),
 ('<span id="pl-type">Home type</span>', '<span id="pl-type">Tipo de casa</span>'),
 ('aria-label="Home type">\n              <div class="pop-h">Home type</div>', 'aria-label="Tipo de casa">\n              <div class="pop-h">Tipo de casa</div>'),
 ('value="" checked><span>Any type</span>', 'value="" checked><span>Cualquier tipo</span>'),
 ('value="residential"><span>House</span>', 'value="residential"><span>Casa</span>'),
 ('value="condominium"><span>Condo / townhome</span>', 'value="condominium"><span>Condominio / townhome</span>'),
 ('value="multifamily"><span>Multi-family</span>', 'value="multifamily"><span>Multifamiliar</span>'),
 ('value="land"><span>Land</span>', 'value="land"><span>Terreno</span>'),
 ('<span id="pl-more">More</span>', '<span id="pl-more">Más</span>'),
 ('aria-label="More filters">\n              <div class="pop-h">Square feet</div>', 'aria-label="Más filtros">\n              <div class="pop-h">Pies cuadrados</div>'),
 ('<option value="">Any size</option><option value="1000">1,000+ sq ft</option><option value="1500">1,500+ sq ft</option><option value="2000">2,000+ sq ft</option><option value="2500">2,500+ sq ft</option><option value="3000">3,000+ sq ft</option><option value="4000">4,000+ sq ft</option>', '<option value="">Cualquier tamaño</option><option value="1000">1,000+ pies²</option><option value="1500">1,500+ pies²</option><option value="2000">2,000+ pies²</option><option value="2500">2,500+ pies²</option><option value="3000">3,000+ pies²</option><option value="4000">4,000+ pies²</option>'),
 ('<div class="pop-h">Year built</div>', '<div class="pop-h">Año de construcción</div>'),
 ('<div class="pop-h">Lot size</div>', '<div class="pop-h">Tamaño del terreno</div>'),
 ('<input type="checkbox" id="pm-pend"> Show pending homes too</label>', '<input type="checkbox" id="pm-pend"> Mostrar también casas pendientes</label>'),
 ('<option value="">Any lot</option><option value="0.5">½ acre or more</option><option value="1">1+ acre</option><option value="2">2+ acres</option><option value="5">5+ acres</option><option value="10">10+ acres</option>', '<option value="">Cualquier terreno</option><option value="0.5">½ acre o más</option><option value="1">1 acre o más</option><option value="2">2 acres o más</option><option value="5">5 acres o más</option><option value="10">10 acres o más</option>'),
 ('<option value="">Any year</option><option value="1980">1980 or newer</option><option value="2000">2000 or newer</option><option value="2010">2010 or newer</option><option value="2020">2020 or newer</option>', '<option value="">Cualquier año</option><option value="1980">1980 o más nueva</option><option value="2000">2000 o más nueva</option><option value="2010">2010 o más nueva</option><option value="2020">2020 o más nueva</option>'),
 ('<div class="pop-h">Days on market</div>', '<div class="pop-h">Días en el mercado</div>'),
 ('<option value="">Any</option><option value="1">New in last 1 day</option><option value="7">New in last 7 days</option><option value="14">New in last 14 days</option><option value="30">New in last 30 days</option>', '<option value="">Cualquiera</option><option value="1">Nuevas en el último día</option><option value="7">Nuevas en los últimos 7 días</option><option value="14">Nuevas en los últimos 14 días</option><option value="30">Nuevas en los últimos 30 días</option>'),
 ('class="pop-reset" data-reset="price">Reset</button><button type="button" class="pop-apply" data-apply="price">Apply</button>', 'class="pop-reset" data-reset="price">Borrar</button><button type="button" class="pop-apply" data-apply="price">Aplicar</button>'),
 ('class="pop-reset" data-reset="beds">Reset</button><button type="button" class="pop-apply" data-apply="beds">Apply</button>', 'class="pop-reset" data-reset="beds">Borrar</button><button type="button" class="pop-apply" data-apply="beds">Aplicar</button>'),
 ('class="pop-reset" data-reset="type">Reset</button><button type="button" class="pop-apply" data-apply="type">Apply</button>', 'class="pop-reset" data-reset="type">Borrar</button><button type="button" class="pop-apply" data-apply="type">Aplicar</button>'),
 ('class="pop-reset" data-reset="more">Reset</button><button type="button" class="pop-apply" data-apply="more">Apply</button>', 'class="pop-reset" data-reset="more">Borrar</button><button type="button" class="pop-apply" data-apply="more">Aplicar</button>'),
 ('class="sp-savebtn" data-alert hidden>Save search</button>', 'class="sp-savebtn" data-alert hidden>Guardar búsqueda</button>'),
 ('DEMO DATA — these are sample listings, not real homes for sale. Private preview page.', 'DATOS DE PRUEBA — página privada de vista previa.'),
 ('<h1>Search Homes for Sale</h1>', '<h1>Buscar casas en venta</h1>'),
 ('<p>Live MLS listings for Sioux Falls and the surrounding area. See one you like? Call or text me at <a href="tel:+16058389140">605-838-9140</a>.</p>',
  '<p>Casas del MLS en vivo en Sioux Falls y sus alrededores. ¿Le gusta una? Llámeme o envíeme un texto al <a href="tel:+16058389140">605-838-9140</a>.</p>'),
 ('placeholder="City, ZIP, address, or MLS #"', 'placeholder="Ciudad, código postal, dirección o MLS #"'),
 ('aria-label="Min price"><option value="">Min price</option>', 'aria-label="Precio mínimo"><option value="">Precio mín.</option>'),
 ('aria-label="Max price"><option value="">Max price</option>', 'aria-label="Precio máximo"><option value="">Precio máx.</option>'),
 ('aria-label="Beds"><option value="">Beds</option>', 'aria-label="Recámaras"><option value="">Recámaras</option>'),
 ('aria-label="Baths"><option value="">Baths</option>', 'aria-label="Baños"><option value="">Baños</option>'),
 ('aria-label="Home type"><option value="">Any type</option><option value="residential">House</option><option value="condominium">Condo</option><option value="multifamily">Multi-family</option><option value="land">Land</option>',
  'aria-label="Tipo de casa"><option value="">Cualquier tipo</option><option value="residential">Casa</option><option value="condominium">Condominio</option><option value="multifamily">Multifamiliar</option><option value="land">Terreno</option>'),
 ('aria-expanded="false">Filters</button>', 'aria-expanded="false">Filtros</button>'),
 ('<button type="submit">Search</button>', '<button type="submit">Buscar</button>'),
 ('data-v="map" class="on">Map</button><button type="button" data-v="list">List</button>', 'data-v="map" class="on">Mapa</button><button type="button" data-v="list">Lista</button>'),
 ('id="sp-count">Loading homes…</div>', 'id="sp-count">Cargando casas…</div>'),
 ('<span id="sp-savedn">Saved (0)</span>', '<span id="sp-savedn">Guardadas (0)</span>'),
 ('Get new listing alerts</button>', 'Recibir alertas de casas nuevas</button>'),
 ('<span id="sp-cmptxt">Pick 2 or 3 homes to compare</span><button type="button" id="sp-cmpgo" disabled>Compare</button>', '<span id="sp-cmptxt">Marque 2 o 3 casas para comparar</span><button type="button" id="sp-cmpgo" disabled>Comparar</button>'),
 ('id="sp-more" hidden>Show more homes</button>', 'id="sp-more" hidden>Ver más casas</button>'),
 ('<p class="sp-disc">Listing information is deemed reliable but not guaranteed and should be independently verified. <span id="sp-updated"></span> Listings shown are courtesy of the listing brokerage named on each listing. Listing data provided by the REALTOR® Association of the Sioux Empire MLS.</p>',
  '<p class="sp-disc">La información de las casas se considera confiable pero no está garantizada y debe verificarse. <span id="sp-updated"></span> Las casas son cortesía de la correduría indicada en cada una. Información proporcionada por el MLS de la REALTOR® Association of the Sioux Empire.</p>'),
 ('aria-label="Home details"', 'aria-label="Detalles de la casa"'),
 ('aria-label="Photos"', 'aria-label="Fotos"'),
 ('aria-label="Close photos"', 'aria-label="Cerrar fotos"'),
 ('aria-label="Previous photo"', 'aria-label="Foto anterior"'),
 ('aria-label="Next photo"', 'aria-label="Foto siguiente"'),
 ('<h2 id="cmp-h">Compare homes</h2>', '<h2 id="cmp-h">Comparar casas</h2>'),
 ('<p class="sp-disc">Listing information is deemed reliable but not guaranteed and should be independently verified. Listing data provided by the REALTOR® Association of the Sioux Empire MLS.</p>',
  '<p class="sp-disc">La información se considera confiable pero no está garantizada y debe verificarse. Información proporcionada por el MLS de la REALTOR® Association of the Sioux Empire.</p>'),
 ('<h2 id="al-h">Get new listings first</h2>', '<h2 id="al-h">Vea las casas nuevas primero</h2>'),
 ('I’ll email you new homes that match your search as soon as they hit the market.', 'Le enviaré por correo las casas nuevas que coincidan con su búsqueda apenas salgan al mercado.'),
 ('<label for="al-name">Name</label>', '<label for="al-name">Nombre</label>'),
 ('<label for="al-email">Email</label>', '<label for="al-email">Correo electrónico</label>'),
 ('<label for="al-phone">Phone <span style="font-weight:300">(optional)</span></label>', '<label for="al-phone">Teléfono <span style="font-weight:300">(opcional)</span></label>'),
 ('<label>How often?</label>', '<label>¿Cada cuánto?</label>'),
 ('value="Daily" checked>Daily</label><label><input type="radio" name="freq" value="Weekly">Weekly</label>', 'value="Daily" checked>Diario</label><label><input type="radio" name="freq" value="Weekly">Semanal</label>'),
 ('Yes, email me new listings from Marcos Diaz, and use the homes I open on this site to fine-tune my alerts. If I add my phone, Marcos may call or text me about homes. I can unsubscribe anytime. <a href="/privacy.html" target="_blank">Privacy</a>',
  'Sí, envíenme casas nuevas de Marcos Diaz y usen las casas que abro en este sitio para ajustar mis alertas. Si agrego mi teléfono, Marcos me puede llamar o enviar textos sobre casas. Puedo cancelar cuando quiera. <a href="/es/privacidad.html" target="_blank">Privacidad</a>'),
 ('class="al-send">Start my alerts</button>', 'class="al-send">Empezar mis alertas</button>'),
 ('<b>You’re all set!</b>Check your email. I sent you the homes that match right now. New ones will come as soon as they’re listed.',
  '<b>¡Listo!</b>Revise su correo. Le envié las casas que coinciden ahora mismo. Las nuevas le llegarán apenas salgan al mercado.'),
 ('aria-label="Close"', 'aria-label="Cerrar"'),
]
for a, b in T:
    if a in es: es = es.replace(a, b)
    elif 'DEMO DATA' not in a and ('pop' in a or 'pl-' in a or 'Save search' in a):
        print('note: not found:', a[:60])
# extra "more ways to search" cards on the live page come from the Spanish shell
if mode == 'live':
    m = re.search(r'<p class="map-cta-or".*?</div>\n', es, re.S)
    sm = re.search(r'<p class="map-cta-or".*?</div>\n', shell, re.S)
    if m and sm: es = es.replace(m.group(0), sm.group(0))
left = [w for w in ['Search Homes for Sale', 'Get new listings first', 'Start my alerts', 'Compare homes', '>Save search<', '>Apply<', 'Price range', 'Beds &amp; baths'] if w in es]
assert not left, left
os.makedirs(os.path.dirname(dst), exist_ok=True)
open(dst, 'w').write(es)
print('wrote', os.path.relpath(dst, ROOT))
