# Generates subpages (privacy + neighborhood pages, EN and ES privacy) for 605homesearch.com
import os, html
import os
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
if HERE not in sys.path: sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
SEARCH = 'https://marcos.kw.com/search/sale?viewport=43.5123477544219%2C-96.73235438067628%2C43.46346435534284%2C-96.80573961932375'


def page(path, title, desc, body, lang='en', canonical='', alt_es='', alt_en='', head_extra='', news=True):
    from news import news_band
    depth = path.count('/')
    p = '../' * depth
    es = lang == 'es'
    home = (p + 'es/') if es else (p or './')
    nav = (f'''      <a href="{home}#about">Sobre mí</a>
      <a href="{home}#reviews">Reseñas</a>
      <a href="{home}#guide">Compradores</a>
      <a href="{home}#sellers">Vendedores</a>
      <a href="{home}#areas">Áreas</a>
      <a href="{p}es/mercado/">Mercado</a>
      <a href="{p}es/blog/">Blog</a>
      <a href="{SEARCH}">Buscar casas</a>
      <a href="{alt_en or p + '../'}" class="lang" lang="en" hreflang="en" aria-label="View in English">EN</a>
      <a href="{home}#contact" class="nav-cta">Contacto</a>''' if es else f'''      <a href="{home}#about">About</a>
      <a href="{home}#reviews">Reviews</a>
      <a href="{home}#guide">Buyers</a>
      <a href="{home}#sellers">Sellers</a>
      <a href="{home}#areas">Areas</a>
      <a href="{p}market/">Market</a>
      <a href="{p}blog/">Blog</a>
      <a href="{SEARCH}">Search Homes</a>
      <a href="{alt_es or p + 'es/'}" class="lang" lang="es" hreflang="es" aria-label="Ver en español">ES</a>
      <a href="{home}#contact" class="nav-cta">Contact</a>''')
    legal = ('Marcos Diaz, Broker Associate con licencia en Dakota del Sur, REALTOR®. Keller Williams Realty Sioux Falls, 6300 S Connie Ave, Sioux Falls, SD 57108 · Oficina <a href="tel:+16052750555">605-275-0555</a>. Cada oficina es de propiedad y operación independiente. Igualdad de oportunidades en la vivienda.'
             if es else 'Marcos Diaz, Broker Associate licensed in South Dakota, REALTOR®. Keller Williams Realty Sioux Falls, 6300 S Connie Ave, Sioux Falls, SD 57108 · Office <a href="tel:+16052750555">605-275-0555</a>. Each office is independently owned and operated. Equal Housing Opportunity.')
    priv = f'{p}es/privacidad.html' if es else f'{p}privacy.html'
    privlabel = 'Privacidad' if es else 'Privacy'
    doc = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{'es_US' if es else 'en_US'}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://605homesearch.com/images/og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
{head_extra}<link rel="icon" href="{p}images/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{p}fonts/fonts.css?v=BUILD">
<link rel="stylesheet" href="{p}styles.css?v=BUILD">
</head>
<body class="subpage">

<header class="site-header" id="header">
  <div class="nav">
    <a href="{home}" class="brand">
      <img src="{p}images/logo.svg" alt="" width="34" height="34">
      <span class="brand-text">Marcos Diaz<small>Keller Williams Realty</small></span>
    </a>
    <button class="menu-btn" aria-label="{'Abrir menú' if es else 'Open menu'}" aria-expanded="false"><span></span><span></span></button>
    <nav class="links">
{nav}
    </nav>
  </div>
</header>

<main>
{body}
{news_band(es) if news else ''}</main>

<footer class="site-footer">
  <div class="wrap footer-inner">
    <div class="footer-brand">
      <img src="{p}images/logo.svg" alt="" width="40" height="40">
      <span class="brand-text light">Marcos Diaz<small>REALTOR® · Keller Williams Realty Sioux Falls</small></span>
    </div>
    <div class="footer-links">
      <a href="tel:+16058389140">605-838-9140</a>
      <a href="mailto:marcosdiaz1@kw.com">marcosdiaz1@kw.com</a>
    </div>
    <div class="footer-social">
      <a href="https://www.facebook.com/marcos.diaz.782829" target="_blank" rel="noopener" aria-label="Facebook" title="Facebook"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/></svg></a>
      <a href="https://www.instagram.com/marcosdiaz_kw/" target="_blank" rel="noopener" aria-label="Instagram" title="Instagram"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"/></svg></a>
      <a href="https://www.linkedin.com/in/marcos-diaz-1b2bb63bb/" target="_blank" rel="noopener" aria-label="LinkedIn" title="LinkedIn"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>
      <a href="https://www.tiktok.com/@marcosdiazrealtor" target="_blank" rel="noopener" aria-label="TikTok" title="TikTok"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg></a>
    </div>
  </div>
  <div class="wrap legal">
    <img class="eho-logo" src="/images/equal-housing.svg" alt="Equal Housing Opportunity" width="56" height="56">
    <p>{legal}</p>
    <p>&copy; <span class="year">2026</span> Marcos Diaz · <a href="{priv}">{privlabel}</a></p>
  </div>
</footer>
<script src="{p}site.js?v=BUILD" defer></script>
</body>
</html>
'''
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or ROOT, exist_ok=True)
    open(full, 'w').write(doc)
    print('wrote', path)


# ---------------- PRIVACY (EN) ----------------
privacy_en = '''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="./">Home</a> &nbsp;/&nbsp; Privacy</p>
      <h1>Privacy Notice</h1>
      <p class="lead">How information you share on 605homesearch.com is used. Effective November 4, 2026.</p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap narrow prose">
      <h2>What I collect</h2>
      <p>When you fill out the contact form, I receive the answers you choose (for example, whether you're buying or selling and your timeline) along with your name, phone number, and email address. I don't collect anything else through this website.</p>
      <h2>How I use it</h2>
      <p>I use your information only to respond to you and help with your real estate needs, such as calling, texting, or emailing you about your search or sale. Your information is never sold.</p>
      <h2>Who processes it</h2>
      <ul>
        <li><strong>Form delivery:</strong> form submissions are delivered to my email by Web3Forms, a form-processing service.</li>
        <li><strong>Hosting:</strong> this website is hosted on GitHub Pages, which may log basic technical information (such as IP addresses) for security purposes.</li>
        <li><strong>My brokerage:</strong> as a licensee of Keller Williams Realty Sioux Falls, I may keep your contact details in my brokerage's client management tools so I can serve you.</li>
      </ul>
      <h2>Cookies and tracking</h2>
      <p>This website does not use advertising cookies or analytics tracking. Fonts are hosted on this site, not loaded from third parties.</p>
      <h2>Other websites</h2>
      <p>Links such as "Search Homes" (my Keller Williams home search) and Google reviews take you to other websites, which have their own privacy policies.</p>
      <h2>Your choices</h2>
      <p>You can ask me to update or delete the information you've shared at any time. Contact Marcos Diaz at <a href="mailto:marcosdiaz1@kw.com">marcosdiaz1@kw.com</a> or <a href="tel:+16058389140">605-838-9140</a>.</p>
    </div>
  </section>'''
page('privacy.html', 'Privacy Notice | Marcos Diaz, REALTOR® | 605homesearch.com',
     'How information shared on 605homesearch.com is collected and used.', privacy_en,
     canonical='https://605homesearch.com/privacy.html', alt_es='es/privacidad.html')

# ---------------- PRIVACY (ES) ----------------
privacy_es = '''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="./">Inicio</a> &nbsp;/&nbsp; Privacidad</p>
      <h1>Aviso de Privacidad</h1>
      <p class="lead">Cómo se usa la información que comparte en 605homesearch.com. Vigente desde el 4 de noviembre de 2026.</p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap narrow prose">
      <h2>Qué información recibo</h2>
      <p>Cuando llena el formulario de contacto, recibo las respuestas que elige (por ejemplo, si desea comprar o vender y cuándo planea mudarse), junto con su nombre, número de teléfono y correo electrónico. No recopilo ninguna otra información a través de este sitio web.</p>
      <h2>Cómo la uso</h2>
      <p>Uso su información únicamente para responderle y ayudarle con sus necesidades de bienes raíces, por ejemplo, llamarle, enviarle un mensaje de texto o un correo sobre su búsqueda o su venta. Su información nunca se vende.</p>
      <h2>Quién la procesa</h2>
      <ul>
        <li><strong>Envío del formulario:</strong> los mensajes del formulario llegan a mi correo a través de Web3Forms, un servicio de procesamiento de formularios.</li>
        <li><strong>Alojamiento:</strong> este sitio está alojado en GitHub Pages, que puede registrar información técnica básica (como direcciones IP) por motivos de seguridad.</li>
        <li><strong>Mi correduría:</strong> como agente de Keller Williams Realty Sioux Falls, puedo guardar sus datos de contacto en las herramientas de mi correduría para poder atenderle.</li>
      </ul>
      <h2>Cookies y rastreo</h2>
      <p>Este sitio no usa cookies de publicidad ni herramientas de análisis. Las fuentes tipográficas están alojadas en este mismo sitio, no se cargan desde terceros.</p>
      <h2>Otros sitios web</h2>
      <p>Enlaces como "Buscar casas" (mi buscador de Keller Williams) y las reseñas de Google le llevan a otros sitios web, que tienen sus propias políticas de privacidad.</p>
      <h2>Sus opciones</h2>
      <p>Puede pedirme en cualquier momento que actualice o elimine la información que compartió. Comuníquese con Marcos Diaz en <a href="mailto:marcosdiaz1@kw.com">marcosdiaz1@kw.com</a> o al <a href="tel:+16058389140">605-838-9140</a>.</p>
    </div>
  </section>'''
page('es/privacidad.html', 'Aviso de Privacidad | Marcos Diaz, REALTOR® | 605homesearch.com',
     'Cómo se recopila y usa la información compartida en 605homesearch.com.', privacy_es, lang='es',
     canonical='https://605homesearch.com/es/privacidad.html', alt_en='../privacy.html')

# ---------------- AREA PAGES ----------------
AREAS = [
    ('sioux-falls', 'Sioux Falls'),
    ('southwest-sioux-falls', 'Southwest Sioux Falls'),
    ('southeast-sioux-falls', 'Southeast Sioux Falls'),
    ('tea', 'Tea'),
    ('harrisburg', 'Harrisburg'),
    ('brandon', 'Brandon'),
    ('garretson', 'Garretson'),
    ('hartford', 'Hartford'),
    ('crooks', 'Crooks'),
    ('lennox', 'Lennox'),
    ('canton', 'Canton'),
]


# Map-framed KW search for each area (north,east,south,west)
CENTERS = {
 'sioux-falls': (43.5446, -96.7311, .09, .15), 'southwest-sioux-falls': (43.505, -96.800, .045, .07),
 'southeast-sioux-falls': (43.505, -96.680, .045, .07), 'tea': (43.4573, -96.8215, .037, .059),
 'harrisburg': (43.4316, -96.6973, .037, .059), 'brandon': (43.5947, -96.5720, .037, .059),
 'garretson': (43.7172, -96.5028, .03, .05), 'hartford': (43.6233, -96.9426, .03, .05),
 'crooks': (43.6647, -96.8106, .03, .05), 'lennox': (43.3547, -96.8920, .03, .05),
 'canton': (43.3008, -96.5928, .03, .05),
}
def town_search(slug, es=False):
    la, lo, dla, dlo = CENTERS[slug]
    vp = f'{la+dla:.4f}%2C{lo+dlo:.4f}%2C{la-dla:.4f}%2C{lo-dlo:.4f}'
    return f'https://marcos.kw.com/search/sale?viewport={vp}'

AREA_CONTENT = {
 'sioux-falls': dict(
   title='Sioux Falls, SD Homes for Sale & Real Estate',
   lead="South Dakota's largest city, with a wide range of neighborhoods, price points, and home styles.",
   about=["Sioux Falls is South Dakota's largest city and the economic hub of the region. From historic homes near downtown and Falls Park to newer subdivisions on the edges of town, there's a wide range of neighborhoods, price points, and home styles to choose from.",
          "Because the city is growing in every direction, the right neighborhood depends on what matters most to you: commute, schools, lot size, budget, or being close to shopping, parks, and trails."],
   why=["Neighborhoods ranging from established, tree-lined streets to brand-new construction",
        "Access to I-29 and I-229 for getting around the city",
        "Parks, trails, and Falls Park in the heart of downtown",
        "A broad mix of price points for first-time buyers, move-up buyers, and investors"],
   schools="Most of Sioux Falls is served by the Sioux Falls School District, but some edges of the city fall in neighboring districts such as Harrisburg, Tea Area, and Brandon Valley. Always confirm the school district for a specific address.",
 ),
 'southwest-sioux-falls': dict(
   title='Southwest Sioux Falls Homes for Sale',
   lead='A growing part of the city with many newer neighborhoods and quick access to I-29.',
   about=["Southwest Sioux Falls has seen a lot of growth, with many newer subdivisions alongside established neighborhoods. It's a popular choice for buyers who want a newer home with modern layouts while staying close to the conveniences of the city.",
          "I've helped clients buy and sell homes in Southwest Sioux Falls and can walk you through the differences between subdivisions, from lot sizes to HOA rules."],
   why=["Many newer homes and subdivisions",
        "Quick access to I-29",
        "Close to shopping, dining, and everyday conveniences",
        "Options for first-time buyers and move-up buyers alike"],
   schools="Depending on the exact address, homes in Southwest Sioux Falls may be in the Sioux Falls, Tea Area, or Harrisburg school districts. Always confirm the school district for a specific address.",
 ),
 'southeast-sioux-falls': dict(
   title='Southeast Sioux Falls Homes for Sale',
   lead='A mix of established neighborhoods and newer development on the southeast side of the city.',
   about=["Southeast Sioux Falls offers a mix of established neighborhoods with mature trees and newer development further out. Buyers often like the balance of space, access, and amenities on this side of town.",
          "I've helped clients buy and sell in Southeast Sioux Falls, and I can help you compare neighborhoods based on your budget, commute, and the type of home you want."],
   why=["Established neighborhoods and newer construction",
        "Access to I-229 for getting across the city",
        "Parks, trails, and shopping nearby",
        "A range of home styles and price points"],
   schools="Depending on the exact address, homes in Southeast Sioux Falls may be in the Sioux Falls, Brandon Valley, or Harrisburg school districts. Always confirm the school district for a specific address.",
 ),
 'tea': dict(
   title='Tea, SD Homes for Sale & Real Estate',
   lead='A growing community just southwest of Sioux Falls with a small-town feel.',
   about=["Tea is a growing community in Lincoln County, just southwest of Sioux Falls. Many buyers choose Tea for its small-town feel while staying only minutes from Sioux Falls shopping, dining, and jobs.",
          "With plenty of newer homes and ongoing development, Tea can be a great fit for first-time buyers, growing families, and anyone looking for a little more space."],
   why=["Small-town community feel close to Sioux Falls",
        "Many newer homes and neighborhoods",
        "Easy access to I-29",
        "Room to grow, with ongoing new development"],
   schools="Tea is served by the Tea Area School District. Always confirm the school district for a specific address.",
 ),
 'harrisburg': dict(
   title='Harrisburg, SD Homes for Sale & Real Estate',
   lead='One of the fastest-growing communities in the Sioux Falls area, just to the south.',
   about=["Harrisburg sits just south of Sioux Falls in Lincoln County and has been one of the fastest-growing communities in the area. Buyers are drawn to its newer neighborhoods and community feel, with Sioux Falls just a short drive away.",
          "Whether you're buying your first home or moving up, I can help you understand the Harrisburg market and find the right neighborhood."],
   why=["Fast-growing community with many newer homes",
        "A short drive to Sioux Falls",
        "Community feel with room to grow",
        "Options across a range of price points"],
   schools="Harrisburg is served by the Harrisburg School District, which also covers parts of southern Sioux Falls. Always confirm the school district for a specific address.",
 ),
 'brandon': dict(
   title='Brandon, SD Homes for Sale & Real Estate',
   lead='A welcoming community just east of Sioux Falls.',
   about=["Brandon is a community in Minnehaha County just east of Sioux Falls. Buyers often choose Brandon for its hometown feel and easy access to Sioux Falls, along with nearby outdoor spaces like the Big Sioux Recreation Area.",
          "I can help you explore homes in Brandon and compare them with nearby options so you find the right fit for your budget and lifestyle."],
   why=["Hometown feel close to Sioux Falls",
        "Near the Big Sioux Recreation Area",
        "Mix of established and newer neighborhoods",
        "Easy access to I-90 and the east side of Sioux Falls"],
   schools="Brandon is served by the Brandon Valley School District. Always confirm the school district for a specific address.",
 ),
}


AREA_CONTENT.update({
 'garretson': dict(
   title='Garretson, SD Homes for Sale & Real Estate',
   lead='The "City of Parks," northeast of Sioux Falls near the Minnesota border.',
   about=["Garretson is a small city in Minnehaha County, northeast of Sioux Falls near the Minnesota border. It's known as the \"City of Parks\" for its beautiful red quartzite scenery along Split Rock Creek.",
          "Buyers who want a quieter small-town lifestyle, more space, and nature right out the door often look at Garretson, while still being within driving distance of Sioux Falls jobs and shopping. I've helped buyers purchase in Garretson and know the area well."],
   why=["Small-town living with a close-knit community",
        "Devil's Gulch and Split Rock Park right in town",
        "Palisades State Park just south of town, with hiking, climbing, and camping",
        "More space and a slower pace, within reach of Sioux Falls"],
   schools="Garretson is served by the Garretson School District, which covers Garretson and Sherman. Always confirm the school district for a specific address.",
 ),
 'hartford': dict(
   title='Hartford, SD Homes for Sale & Real Estate',
   lead='A suburban community a few miles northwest of Sioux Falls.',
   about=["Hartford is a suburban city in Minnehaha County, just a few miles northwest of Sioux Falls. It offers a small-town community feel with an easy drive into the city for work, shopping, and entertainment.",
          "It's a popular choice for buyers who want a smaller community and good value while staying close to Sioux Falls. I can help you compare Hartford with other communities around the city."],
   why=["Small-town community close to Sioux Falls",
        "A quick drive into the city",
        "A mix of established homes and newer construction",
        "Room to spread out compared to the city"],
   schools="Hartford is home to the West Central School District, which also serves Humboldt and surrounding areas. Always confirm the school district for a specific address.",
 ),
 'crooks': dict(
   title='Crooks, SD Homes for Sale & Real Estate',
   lead='A small community just north of Sioux Falls.',
   about=["Crooks is a small city in Minnehaha County just north of Sioux Falls. Many buyers like its quiet, small-town setting while being only minutes from the city.",
          "If you want a little more space and a peaceful neighborhood without a long commute, Crooks is worth a look. I'll help you see what's available and how it compares to nearby areas."],
   why=["Quiet small-town setting",
        "Minutes from Sioux Falls",
        "Homes with more room and bigger lots",
        "A tight-knit community"],
   schools="Crooks is in the Tri-Valley School District, which also serves Colton and parts of the surrounding area. Always confirm the school district for a specific address.",
 ),
 'lennox': dict(
   title='Lennox, SD Homes for Sale & Real Estate',
   lead='A Lincoln County community southwest of Sioux Falls, just off I-29.',
   about=["Lennox is a city in Lincoln County, about 20 miles southwest of Sioux Falls and a few miles off I-29. It offers a strong small-town community with parks, a community pool, and local events.",
          "Buyers often choose Lennox for its community feel and value, with an easy drive to Sioux Falls, Tea, and Harrisburg. I can help you understand the Lennox market and find the right home."],
   why=["Strong small-town community",
        "Easy access to I-29",
        "Parks, a community pool, and local events",
        "Good value compared to homes closer to the city"],
   schools="Lennox is served by the Lennox School District, which also includes Worthing and Chancellor. Always confirm the school district for a specific address.",
 ),
 'canton': dict(
   title='Canton, SD Homes for Sale & Real Estate',
   lead='The Lincoln County seat, south of Sioux Falls in the rolling hills of the Sioux Valley.',
   about=["Canton is the county seat of Lincoln County, south of Sioux Falls. It sits in the rolling hills of the Sioux Valley, with the Big Sioux River on its east side, Lake Alvin to the north, and Newton Hills State Park to the south.",
          "Buyers who love the outdoors and a historic small-town downtown often look at Canton, with Sioux Falls about a 20-minute drive away."],
   why=["Historic small-town downtown",
        "Newton Hills State Park just south of town",
        "Lake Alvin and the Big Sioux River nearby",
        "Community pool, golf course, and parks"],
   schools="Canton is served by the Canton School District. Always confirm the school district for a specific address.",
 ),
})

import json

ES_NAMES = {
 'sioux-falls': 'Sioux Falls',
 'southwest-sioux-falls': 'el Suroeste de Sioux Falls',
 'southeast-sioux-falls': 'el Sureste de Sioux Falls',
 'tea': 'Tea', 'harrisburg': 'Harrisburg', 'brandon': 'Brandon',
}
ES_SHORT = {
 'sioux-falls': 'Sioux Falls', 'southwest-sioux-falls': 'Suroeste de Sioux Falls',
 'southeast-sioux-falls': 'Sureste de Sioux Falls', 'tea': 'Tea', 'harrisburg': 'Harrisburg', 'brandon': 'Brandon',
}
ES_CONTENT = {
 'sioux-falls': dict(
   title='Casas en venta en Sioux Falls, SD',
   lead='La ciudad más grande de Dakota del Sur, con una gran variedad de vecindarios, precios y estilos de casas.',
   about=["Sioux Falls es la ciudad más grande de Dakota del Sur y el centro económico de la región. Desde casas históricas cerca del centro y de Falls Park hasta fraccionamientos nuevos en las afueras, hay una gran variedad de vecindarios, precios y estilos para elegir.",
          "Como la ciudad crece en todas direcciones, el vecindario ideal depende de lo que más le importe: el trayecto al trabajo, las escuelas, el tamaño del terreno, el presupuesto o estar cerca de tiendas, parques y senderos."],
   why=["Vecindarios que van desde calles establecidas y arboladas hasta construcción nueva",
        "Acceso a la I-29 y la I-229 para moverse por la ciudad",
        "Parques, senderos y Falls Park en el corazón del centro",
        "Una amplia variedad de precios para compradores de primera vivienda, familias que buscan más espacio e inversionistas"],
   schools="La mayor parte de Sioux Falls pertenece al Distrito Escolar de Sioux Falls, pero algunas orillas de la ciudad están en distritos vecinos como Harrisburg, Tea Area y Brandon Valley. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'southwest-sioux-falls': dict(
   title='Casas en venta en el Suroeste de Sioux Falls',
   lead='Una zona en crecimiento con muchos vecindarios nuevos y acceso rápido a la I-29.',
   about=["El suroeste de Sioux Falls ha crecido mucho, con varios fraccionamientos nuevos junto a vecindarios establecidos. Es una opción popular para quienes buscan una casa más nueva con distribución moderna, sin alejarse de las comodidades de la ciudad.",
          "He ayudado a clientes a comprar y vender casas en el suroeste de Sioux Falls y puedo explicarle las diferencias entre fraccionamientos, desde el tamaño de los terrenos hasta las reglas de la asociación de vecinos (HOA)."],
   why=["Muchas casas y fraccionamientos nuevos",
        "Acceso rápido a la I-29",
        "Cerca de tiendas, restaurantes y servicios",
        "Opciones tanto para compradores de primera vivienda como para quienes buscan más espacio"],
   schools="Según la dirección exacta, las casas del suroeste de Sioux Falls pueden pertenecer a los distritos escolares de Sioux Falls, Tea Area o Harrisburg. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'southeast-sioux-falls': dict(
   title='Casas en venta en el Sureste de Sioux Falls',
   lead='Una mezcla de vecindarios establecidos y desarrollo nuevo en el lado sureste de la ciudad.',
   about=["El sureste de Sioux Falls ofrece una mezcla de vecindarios establecidos con árboles maduros y desarrollo nuevo más hacia las afueras. A muchos compradores les gusta el equilibrio entre espacio, acceso y servicios de este lado de la ciudad.",
          "He ayudado a clientes a comprar y vender en el sureste de Sioux Falls, y puedo ayudarle a comparar vecindarios según su presupuesto, su trayecto y el tipo de casa que busca."],
   why=["Vecindarios establecidos y construcción nueva",
        "Acceso a la I-229 para cruzar la ciudad",
        "Parques, senderos y tiendas cerca",
        "Variedad de estilos de casas y precios"],
   schools="Según la dirección exacta, las casas del sureste de Sioux Falls pueden pertenecer a los distritos escolares de Sioux Falls, Brandon Valley o Harrisburg. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'tea': dict(
   title='Casas en venta en Tea, SD',
   lead='Una comunidad en crecimiento al suroeste de Sioux Falls, con ambiente de pueblo.',
   about=["Tea es una comunidad en crecimiento del condado de Lincoln, justo al suroeste de Sioux Falls. Muchos compradores eligen Tea por su ambiente de pueblo, a solo minutos de las tiendas, restaurantes y empleos de Sioux Falls.",
          "Con muchas casas nuevas y desarrollo constante, Tea puede ser una gran opción para compradores de primera vivienda, familias en crecimiento y cualquiera que busque un poco más de espacio."],
   why=["Ambiente de pueblo cerca de Sioux Falls",
        "Muchas casas y vecindarios nuevos",
        "Fácil acceso a la I-29",
        "Espacio para crecer, con desarrollo nuevo constante"],
   schools="Tea pertenece al Distrito Escolar de Tea Area. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'harrisburg': dict(
   title='Casas en venta en Harrisburg, SD',
   lead='Una de las comunidades de más rápido crecimiento en el área de Sioux Falls, justo al sur.',
   about=["Harrisburg está justo al sur de Sioux Falls, en el condado de Lincoln, y ha sido una de las comunidades de más rápido crecimiento de la zona. A los compradores les atraen sus vecindarios nuevos y su ambiente de comunidad, con Sioux Falls a poca distancia en carro.",
          "Ya sea que compre su primera casa o busque algo más grande, puedo ayudarle a entender el mercado de Harrisburg y encontrar el vecindario indicado."],
   why=["Comunidad en rápido crecimiento con muchas casas nuevas",
        "A poca distancia en carro de Sioux Falls",
        "Ambiente de comunidad con espacio para crecer",
        "Opciones en distintos rangos de precio"],
   schools="Harrisburg pertenece al Distrito Escolar de Harrisburg, que también cubre partes del sur de Sioux Falls. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'brandon': dict(
   title='Casas en venta en Brandon, SD',
   lead='Una comunidad acogedora justo al este de Sioux Falls.',
   about=["Brandon es una comunidad del condado de Minnehaha, justo al este de Sioux Falls. Muchos compradores eligen Brandon por su ambiente de pueblo y su fácil acceso a Sioux Falls, además de espacios al aire libre cercanos como el Big Sioux Recreation Area.",
          "Puedo ayudarle a explorar casas en Brandon y compararlas con opciones cercanas para que encuentre la que mejor se ajuste a su presupuesto y estilo de vida."],
   why=["Ambiente de pueblo cerca de Sioux Falls",
        "Cerca del Big Sioux Recreation Area",
        "Mezcla de vecindarios establecidos y nuevos",
        "Fácil acceso a la I-90 y al lado este de Sioux Falls"],
   schools="Brandon pertenece al Distrito Escolar de Brandon Valley. Siempre confirme el distrito escolar de una dirección específica.",
 ),
}


ES_NAMES.update({'garretson': 'Garretson', 'hartford': 'Hartford', 'crooks': 'Crooks', 'lennox': 'Lennox', 'canton': 'Canton'})
ES_SHORT.update({'garretson': 'Garretson', 'hartford': 'Hartford', 'crooks': 'Crooks', 'lennox': 'Lennox', 'canton': 'Canton'})
ES_CONTENT.update({
 'garretson': dict(
   title='Casas en venta en Garretson, SD',
   lead='La "Ciudad de los Parques", al noreste de Sioux Falls cerca de la frontera con Minnesota.',
   about=["Garretson es una pequeña ciudad del condado de Minnehaha, al noreste de Sioux Falls y cerca de la frontera con Minnesota. Se le conoce como la \"Ciudad de los Parques\" por sus hermosos paisajes de cuarcita roja a lo largo de Split Rock Creek.",
          "Los compradores que buscan una vida tranquila de pueblo, más espacio y naturaleza cerca suelen considerar Garretson, sin dejar de estar a una distancia razonable de los empleos y tiendas de Sioux Falls. He ayudado a compradores a adquirir casa en Garretson y conozco bien el área."],
   why=["Vida de pueblo con una comunidad unida",
        "Devil's Gulch y Split Rock Park en el mismo pueblo",
        "Palisades State Park justo al sur, con senderismo, escalada y campamento",
        "Más espacio y un ritmo más tranquilo, cerca de Sioux Falls"],
   schools="Garretson pertenece al Distrito Escolar de Garretson, que cubre Garretson y Sherman. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'hartford': dict(
   title='Casas en venta en Hartford, SD',
   lead='Una comunidad suburbana a pocas millas al noroeste de Sioux Falls.',
   about=["Hartford es una ciudad suburbana del condado de Minnehaha, a pocas millas al noroeste de Sioux Falls. Ofrece ambiente de pueblo con un trayecto corto a la ciudad para trabajar, comprar y divertirse.",
          "Es una opción popular para quienes buscan una comunidad más pequeña y buen valor sin alejarse de Sioux Falls. Le ayudo a comparar Hartford con otras comunidades alrededor de la ciudad."],
   why=["Ambiente de pueblo cerca de Sioux Falls",
        "Trayecto corto a la ciudad",
        "Casas establecidas y construcción nueva",
        "Más espacio que en la ciudad"],
   schools="En Hartford está el Distrito Escolar West Central, que también sirve a Humboldt y sus alrededores. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'crooks': dict(
   title='Casas en venta en Crooks, SD',
   lead='Una pequeña comunidad justo al norte de Sioux Falls.',
   about=["Crooks es una pequeña ciudad del condado de Minnehaha, justo al norte de Sioux Falls. A muchos compradores les gusta su ambiente tranquilo de pueblo, a solo minutos de la ciudad.",
          "Si quiere un poco más de espacio y un vecindario tranquilo sin un trayecto largo, vale la pena considerar Crooks. Le muestro lo que hay disponible y cómo se compara con áreas cercanas."],
   why=["Ambiente tranquilo de pueblo",
        "A minutos de Sioux Falls",
        "Casas con más espacio y terrenos más grandes",
        "Una comunidad unida"],
   schools="Crooks pertenece al Distrito Escolar Tri-Valley, que también sirve a Colton y partes de los alrededores. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'lennox': dict(
   title='Casas en venta en Lennox, SD',
   lead='Una comunidad del condado de Lincoln al suroeste de Sioux Falls, cerca de la I-29.',
   about=["Lennox es una ciudad del condado de Lincoln, a unas 20 millas al suroeste de Sioux Falls y a pocas millas de la I-29. Tiene una comunidad de pueblo muy unida, con parques, piscina comunitaria y eventos locales.",
          "Muchos compradores eligen Lennox por su ambiente de comunidad y buen valor, con un trayecto fácil a Sioux Falls, Tea y Harrisburg. Le ayudo a entender el mercado de Lennox y encontrar la casa indicada."],
   why=["Comunidad de pueblo muy unida",
        "Fácil acceso a la I-29",
        "Parques, piscina comunitaria y eventos locales",
        "Buen valor comparado con casas más cerca de la ciudad"],
   schools="Lennox pertenece al Distrito Escolar de Lennox, que también incluye Worthing y Chancellor. Siempre confirme el distrito escolar de una dirección específica.",
 ),
 'canton': dict(
   title='Casas en venta en Canton, SD',
   lead='La sede del condado de Lincoln, al sur de Sioux Falls, entre las colinas del valle del Sioux.',
   about=["Canton es la sede del condado de Lincoln, al sur de Sioux Falls. Está entre las colinas del valle del Sioux, con el río Big Sioux al este, el lago Alvin al norte y Newton Hills State Park al sur.",
          "A los compradores que disfrutan la naturaleza y un centro histórico de pueblo les gusta Canton, a unos 20 minutos de Sioux Falls."],
   why=["Centro histórico de pueblo",
        "Newton Hills State Park justo al sur",
        "El lago Alvin y el río Big Sioux cerca",
        "Piscina comunitaria, campo de golf y parques"],
   schools="Canton pertenece al Distrito Escolar de Canton. Siempre confirme el distrito escolar de una dirección específica.",
 ),
})

def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>\n'

for slug, name in AREAS:
    en_url = f'https://605homesearch.com/areas/{slug}.html'
    es_url = f'https://605homesearch.com/es/areas/{slug}.html'
    alts = (f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
            f'<link rel="alternate" hreflang="es" href="{es_url}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{en_url}">\n')
    # ---------- English ----------
    d = AREA_CONTENT[slug]
    about = '\n'.join(f'      <p>{t}</p>' for t in d['about'])
    why = '\n'.join(f'        <li>{t}</li>' for t in d['why'])
    others = '\n'.join(f'          <a href="{s2}.html">{n2}</a>' for s2, n2 in AREAS if s2 != slug)
    body = f"""  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="../">Home</a> &nbsp;/&nbsp; <a href="../#areas">Areas</a> &nbsp;/&nbsp; {name}</p>
      <h1>Homes for Sale in {name}</h1>
      <p class="lead">{d['lead']}</p>
      <p class="hero-search"><a href="{town_search(slug)}" class="btn btn-gold" target="_blank" rel="noopener">See Homes for Sale in {name}</a></p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap page-grid">
      <div class="prose">
        <h2>Living in {name}</h2>
{about}
        <h2>Why buyers like {name}</h2>
        <ul>
{why}
        </ul>
        <h2>Schools</h2>
        <p>{d['schools']}</p>
        <h2>Thinking about buying or selling in {name}?</h2>
        <p>I'll help you understand current prices, what's selling, and which neighborhoods fit your goals. If the right home isn't on the market, I can also search off-market for you. Se habla español: <a href="../es/areas/{slug}.html">ver esta página en español</a>.</p>
        <h3 class="sub" style="margin-top:40px">Explore other areas</h3>
        <div class="other-areas">
{others}
        </div>
      </div>
      <aside class="side-card">
        <p class="eyebrow">Work with Marcos</p>
        <h3>Search {name} homes</h3>
        <a href="{town_search(slug)}" class="btn btn-navy" target="_blank" rel="noopener">See Homes for Sale in {name}</a>
        <a href="../#contact" class="btn btn-gold">Talk to Marcos</a>
        <p class="muted">Call or text <a href="tel:+16058389140">605-838-9140</a><br>REALTOR® · Keller Williams Realty Sioux Falls<br>English &amp; Español</p>
      </aside>
    </div>
  </section>"""
    extra = alts + ld(crumbs_ld([('Home', 'https://605homesearch.com/'), ('Areas', 'https://605homesearch.com/#areas'), (name, en_url)]))
    page(f'areas/{slug}.html', f"{d['title']} | Marcos Diaz, REALTOR®",
         f"{d['lead']} Buy or sell in {name} with Marcos Diaz, Keller Williams Realty Sioux Falls. Se habla español.",
         body, canonical=en_url, alt_es=f'../es/areas/{slug}.html', head_extra=extra)
    # ---------- Spanish ----------
    e = ES_CONTENT[slug]; en_name = ES_NAMES[slug]; short = ES_SHORT[slug]
    about = '\n'.join(f'      <p>{t}</p>' for t in e['about'])
    why = '\n'.join(f'        <li>{t}</li>' for t in e['why'])
    others = '\n'.join(f'          <a href="{s2}.html">{ES_SHORT[s2]}</a>' for s2, _ in AREAS if s2 != slug)
    cap = en_name[0].upper() + en_name[1:]
    body = f"""  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="../">Inicio</a> &nbsp;/&nbsp; <a href="../#areas">Áreas</a> &nbsp;/&nbsp; {short}</p>
      <h1>{e['title'].replace(', SD','')}</h1>
      <p class="lead">{e['lead']}</p>
      <p class="hero-search"><a href="{town_search(slug, True)}" class="btn btn-gold" target="_blank" rel="noopener">Ver casas en venta en {short}</a></p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap page-grid">
      <div class="prose">
        <h2>Vivir en {en_name}</h2>
{about}
        <h2>Por qué a los compradores les gusta {en_name}</h2>
        <ul>
{why}
        </ul>
        <h2>Escuelas</h2>
        <p>{e['schools']}</p>
        <h2>¿Piensa comprar o vender en {en_name}?</h2>
        <p>Le ayudo a entender los precios actuales, qué se está vendiendo y qué vecindarios se ajustan a sus metas. Si la casa ideal no está a la venta, también puedo buscar fuera del mercado. Le atiendo en español de principio a fin.</p>
        <h3 class="sub" style="margin-top:40px">Explore otras áreas</h3>
        <div class="other-areas">
{others}
        </div>
      </div>
      <aside class="side-card">
        <p class="eyebrow">Trabaje con Marcos</p>
        <h3>Casas en {short}</h3>
        <a href="{town_search(slug, True)}" class="btn btn-navy" target="_blank" rel="noopener">Ver casas en venta en {short}</a>
        <a href="../#contact" class="btn btn-gold">Hablar con Marcos</a>
        <p class="muted">Llame o envíe texto al <a href="tel:+16058389140">605-838-9140</a><br>REALTOR® · Keller Williams Realty Sioux Falls<br>Se habla español</p>
      </aside>
    </div>
  </section>"""
    extra = alts + ld(crumbs_ld([('Inicio', 'https://605homesearch.com/es/'), ('Áreas', 'https://605homesearch.com/es/#areas'), (short, es_url)]))
    page(f'es/areas/{slug}.html', f"{e['title']} | Marcos Diaz, agente de bienes raíces",
         f"{e['lead']} Compre o venda en {en_name} con Marcos Diaz, Keller Williams Realty Sioux Falls. Se habla español.",
         body, lang='es', canonical=es_url, alt_en=f'../../areas/{slug}.html', head_extra=extra)

# privacy pages: hreflang pair

# ---------------- MARKET UPDATE ----------------
MONTHS = [('Jan', 331650), ('Mar', 313950), ('May', 356800), ('Jun', 335000), ('Jul', 340450), ('Aug', 330000), ('Sep', 344600)]
MONTHS_ES = {'Jan': 'ene', 'Mar': 'mar', 'May': 'may', 'Jun': 'jun', 'Jul': 'jul', 'Aug': 'ago', 'Sep': 'sep'}

def chart(es=False):
    lo, hi = 300000, 360000
    W, H, pad_l, pad_b, pad_t = 640, 280, 56, 34, 24
    bw = (W - pad_l - 20) / len(MONTHS)
    parts = [f'<svg viewBox="0 0 {W} {H}" class="mchart" role="img" aria-label="{"Precio mediano mensual en Sioux Falls en 2026" if es else "Monthly median sale price in Sioux Falls, 2026"}">']
    for v in (300000, 320000, 340000, 360000):
        y = pad_t + (H - pad_t - pad_b) * (1 - (v - lo) / (hi - lo))
        parts.append(f'<line x1="{pad_l}" x2="{W-10}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/><text x="{pad_l-8}" y="{y+4:.1f}" class="ylab" text-anchor="end">${v//1000}K</text>')
    for i, (m, v) in enumerate(MONTHS):
        x = pad_l + 10 + i * bw
        top = pad_t + (H - pad_t - pad_b) * (1 - (v - lo) / (hi - lo))
        h = (H - pad_b) - top
        last = i == len(MONTHS) - 1
        parts.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw*0.62:.1f}" height="{h:.1f}" class="{"bar last" if last else "bar"}"/>')
        parts.append(f'<text x="{x+bw*0.31:.1f}" y="{top-7:.1f}" class="vlab" text-anchor="middle">${v/1000:.0f}K</text>')
        lab = MONTHS_ES[m] if es else m
        parts.append(f'<text x="{x+bw*0.31:.1f}" y="{H-12}" class="xlab" text-anchor="middle">{lab}</text>')
    parts.append('</svg>')
    return ''.join(parts)

SRC = 'https://siouxfalls.business/september-brings-jump-in-home-sales-record-average-price-in-sioux-falls/'

market_en = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="../">Home</a> &nbsp;/&nbsp; Market Update</p>
      <h1>Sioux Falls Housing Market Update</h1>
      <p class="lead">September 2026 numbers for the city of Sioux Falls, from the latest official report by the Realtor Association of the Sioux Empire. Updated November 4, 2026.</p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap">
      <dl class="mstats">
        <div><dt>$344,600</dt><dd>Median sale price</dd><span class="chg up">+1.8% vs. Sept 2025</span></div>
        <div><dt>219</dt><dd>Homes sold</dd><span class="chg up">+15.9% (189 last year)</span></div>
        <div><dt>81</dt><dd>Average days on market</dd><span class="chg">90 days a year ago</span></div>
        <div><dt>97.3%</dt><dd>Of original list price</dd><span class="chg">96.9% a year ago</span></div>
        <div><dt>1,011</dt><dd>Homes for sale</dd><span class="chg down">−25.7% year over year</span></div>
        <div><dt>3.8</dt><dd>Months of supply</dd><span class="chg down">−34.5% year over year</span></div>
        <div><dt>450</dt><dd>New listings</dd><span class="chg down">−2.2% (460 last year)</span></div>
        <div><dt>$456,855</dt><dd>Average sale price</dd><span class="chg up">+19.4%, a monthly record</span></div>
      </dl>
      <div class="page-grid market-grid">
        <div class="prose">
          <h2>What the numbers say</h2>
          <p>More homes sold in Sioux Falls this September than last, and the typical home sold for <strong>$344,600</strong>, up 1.8% from a year ago. The record <strong>$456,855</strong> average price was pulled up by a handful of high-dollar sales, including a $6 million estate on South Minnesota Avenue, so the median is the better guide to what a typical home is selling for.</p>
          <p>The biggest story is still <strong>low inventory</strong>. There were about a quarter fewer homes for sale than a year ago, and the city ended September with a 3.8-month supply. Homes are selling faster than last year (81 days on average, down from about 90) and sellers received 97.3% of their original asking price on average.</p>
          <h2>Median price in 2026</h2>
          <figure class="chart-fig">
            {chart()}
            <figcaption>Monthly median sale price, city of Sioux Falls. Months with a published report shown; the scale starts at $300K to make changes visible.</figcaption>
          </figure>
          <h2>What it means if you're buying</h2>
          <ul>
            <li>With fewer homes on the market, good homes in popular price ranges can move quickly. Get pre-approved before you start touring.</li>
            <li>Homes still average 81 days on market and sell for about 97% of list price, so there's often room to negotiate, especially on homes that have been listed a while.</li>
            <li>Homes priced between $150,000 and $200,000 sold fastest in September (82 days on average).</li>
          </ul>
          <h2>What it means if you're selling</h2>
          <ul>
            <li>Low inventory works in your favor: buyers have fewer choices than a year ago.</li>
            <li>Pricing still matters. Buyers are paying close to asking price, not far over it, so pricing right from day one is the best way to sell faster.</li>
            <li>Higher-end homes take longer: the $900,000 to $1 million range was the slowest-selling in September, at 124 days.</li>
          </ul>
          <p class="source">Source: <a href="{SRC}" target="_blank" rel="noopener">Realtor Association of the Sioux Empire, as reported by SiouxFalls.Business</a> (September 2026, city of Sioux Falls). Monthly medians from the association's 2026 reports. October 2026 figures will be added when the next report is released. Information is deemed reliable but not guaranteed.</p>
        </div>
        <aside class="side-card">
          <p class="eyebrow">Your Home, Your Numbers</p>
          <h3>Want numbers for your neighborhood?</h3>
          <p class="muted" style="font-size:.95rem">Citywide averages only tell part of the story. I'll pull recent sales near you and show what they mean for your plans.</p>
          <a href="../home-value/" class="btn btn-gold">What's My Home Worth?</a>
          <a href="{town_search(slug)}" class="btn btn-navy" target="_blank" rel="noopener">See Homes for Sale in {name}</a>
          <p class="muted">Call or text <a href="tel:+16058389140">605-838-9140</a><br>English &amp; Español · <a href="../es/mercado/">Ver en español</a></p>
        </aside>
      </div>
    </div>
  </section>'''

market_es = f'''  <section class="page-hero">
    <div class="wrap">
      <p class="crumbs"><a href="../">Inicio</a> &nbsp;/&nbsp; Mercado</p>
      <h1>Reporte del mercado de vivienda en Sioux Falls</h1>
      <p class="lead">Cifras de septiembre de 2026 para la ciudad de Sioux Falls, del reporte oficial más reciente de la Asociación de Realtors del Sioux Empire. Actualizado el 4 de noviembre de 2026.</p>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap">
      <dl class="mstats">
        <div><dt>$344,600</dt><dd>Precio mediano de venta</dd><span class="chg up">+1.8% vs. sept. 2025</span></div>
        <div><dt>219</dt><dd>Casas vendidas</dd><span class="chg up">+15.9% (189 el año pasado)</span></div>
        <div><dt>81</dt><dd>Días promedio en el mercado</dd><span class="chg">90 días hace un año</span></div>
        <div><dt>97.3%</dt><dd>Del precio original</dd><span class="chg">96.9% hace un año</span></div>
        <div><dt>1,011</dt><dd>Casas en venta</dd><span class="chg down">−25.7% vs. el año pasado</span></div>
        <div><dt>3.8</dt><dd>Meses de inventario</dd><span class="chg down">−34.5% vs. el año pasado</span></div>
        <div><dt>450</dt><dd>Casas nuevas en venta</dd><span class="chg down">−2.2% (460 el año pasado)</span></div>
        <div><dt>$456,855</dt><dd>Precio promedio de venta</dd><span class="chg up">+19.4%, récord mensual</span></div>
      </dl>
      <div class="page-grid market-grid">
        <div class="prose">
          <h2>Lo que dicen los números</h2>
          <p>Este septiembre se vendieron más casas en Sioux Falls que el año pasado, y la casa típica se vendió en <strong>$344,600</strong>, 1.8% más que hace un año. El precio promedio récord de <strong>$456,855</strong> subió por unas cuantas ventas de alto valor, incluyendo una propiedad de $6 millones en la South Minnesota Avenue, así que la mediana es la mejor guía de lo que cuesta una casa típica.</p>
          <p>Lo más importante sigue siendo el <strong>poco inventario</strong>. Había alrededor de una cuarta parte menos casas en venta que hace un año, y la ciudad terminó septiembre con 3.8 meses de inventario. Las casas se venden más rápido que el año pasado (81 días en promedio, frente a unos 90) y los vendedores recibieron en promedio el 97.3% de su precio original.</p>
          <h2>Precio mediano en 2026</h2>
          <figure class="chart-fig">
            {chart(es=True)}
            <figcaption>Precio mediano mensual de venta, ciudad de Sioux Falls. Se muestran los meses con reporte publicado; la escala empieza en $300K para que se noten los cambios.</figcaption>
          </figure>
          <h2>Si va a comprar</h2>
          <ul>
            <li>Con menos casas a la venta, las buenas casas en los rangos de precio más buscados se venden rápido. Obtenga su preaprobación antes de empezar a ver casas.</li>
            <li>Las casas todavía tardan 81 días en promedio y se venden por alrededor del 97% del precio de lista, así que muchas veces hay espacio para negociar, sobre todo con casas que llevan tiempo en venta.</li>
            <li>Las casas de $150,000 a $200,000 fueron las que se vendieron más rápido en septiembre (82 días en promedio).</li>
          </ul>
          <h2>Si va a vender</h2>
          <ul>
            <li>El poco inventario le favorece: los compradores tienen menos opciones que hace un año.</li>
            <li>El precio sigue siendo clave. Los compradores pagan cerca del precio de lista, no mucho más, así que ponerle el precio correcto desde el primer día es la mejor forma de vender más rápido.</li>
            <li>Las casas de mayor precio tardan más: el rango de $900,000 a $1 millón fue el más lento en septiembre, con 124 días.</li>
          </ul>
          <p class="source">Fuente: <a href="{SRC}" target="_blank" rel="noopener">Asociación de Realtors del Sioux Empire, según SiouxFalls.Business</a> (septiembre de 2026, ciudad de Sioux Falls; en inglés). Medianas mensuales de los reportes de 2026 de la asociación. Las cifras de octubre de 2026 se agregarán cuando salga el próximo reporte. La información se considera confiable pero no está garantizada.</p>
        </div>
        <aside class="side-card">
          <p class="eyebrow">Su casa, sus números</p>
          <h3>¿Quiere los números de su vecindario?</h3>
          <p class="muted" style="font-size:.95rem">Los promedios de la ciudad solo cuentan una parte. Le preparo las ventas recientes cerca de usted y le explico qué significan para sus planes.</p>
          <a href="../valor-de-casa/" class="btn btn-gold">¿Cuánto vale mi casa?</a>
          <a href="{town_search(slug, True)}" class="btn btn-navy" target="_blank" rel="noopener">Ver casas en venta en {short}</a>
          <p class="muted">Llame o envíe texto al <a href="tel:+16058389140">605-838-9140</a><br>Se habla español · <a href="../../market/">View in English</a></p>
        </aside>
      </div>
    </div>
  </section>'''

alts = ('<link rel="alternate" hreflang="en" href="https://605homesearch.com/market/">\n'
        '<link rel="alternate" hreflang="es" href="https://605homesearch.com/es/mercado/">\n'
        '<link rel="alternate" hreflang="x-default" href="https://605homesearch.com/market/">\n')
art = lambda headline, lang, url: ld({"@context": "https://schema.org", "@type": "Article", "headline": headline, "inLanguage": lang,
    "datePublished": "2026-11-04", "dateModified": "2026-11-04", "mainEntityOfPage": url,
    "author": {"@type": "Person", "name": "Marcos Diaz", "url": "https://605homesearch.com/"},
    "publisher": {"@type": "Organization", "name": "Marcos Diaz, Keller Williams Realty Sioux Falls", "logo": {"@type": "ImageObject", "url": "https://605homesearch.com/images/og-image.jpg"}},
    "image": "https://605homesearch.com/images/og-image.jpg"})
page('market/index.html', 'Sioux Falls Housing Market Update: September 2026 | Marcos Diaz, REALTOR®',
     'Sioux Falls housing market, September 2026: median price $344,600 (+1.8%), 219 homes sold, 81 days on market, 3.8 months of supply. What it means for buyers and sellers.',
     market_en, canonical='https://605homesearch.com/market/', alt_es='../es/mercado/',
     head_extra=alts + art('Sioux Falls Housing Market Update: September 2026', 'en', 'https://605homesearch.com/market/'))
page('es/mercado/index.html', 'Mercado de vivienda en Sioux Falls: septiembre 2026 | Marcos Diaz',
     'Mercado de vivienda en Sioux Falls, septiembre 2026: precio mediano $344,600 (+1.8%), 219 casas vendidas, 81 días en el mercado, 3.8 meses de inventario. Qué significa para compradores y vendedores.',
     market_es, lang='es', canonical='https://605homesearch.com/es/mercado/', alt_en='../../market/',
     head_extra=alts + art('Reporte del mercado de vivienda en Sioux Falls: septiembre 2026', 'es', 'https://605homesearch.com/es/mercado/'))


# ---------- Home value pages ----------
SHEET = 'https://script.google.com/macros/s/AKfycbw5PdoEEaGDAquTmKqO_1SkhtTaJG3G0584Xy4VIqG74FsaaH-tnxYpeIdrqTcCjZ0w/exec'

def hv_body(es):
    t = (lambda e, s: s if es else e)
    home = '../' if not es else '../../es/'
    priv = '../privacy.html' if not es else '../privacidad.html'
    other = '../es/valor-de-casa/' if not es else '../../home-value/'
    def ch(name, val, strong, small):
        return f'            <label class="choice"><input type="radio" name="{name}" value="{val}"><span><strong>{strong}</strong><small>{small}</small></span></label>\n'
    opts = [('Ready to sell now', t('Ready to sell now', 'Listo para vender'), t('Let\'s get it on the market', 'Quiero empezar ya')),
            ('1-3 months', t('1–3 months', '1–3 meses'), t('Planning the move now', 'Planeando la mudanza')),
            ('3-6 months', t('3–6 months', '3–6 meses'), t('Getting prepared', 'Preparándome')),
            ('Just curious', t('Just curious', 'Solo por curiosidad'), t('Want to know my equity', 'Quiero saber cuánto vale'))]
    return f'''  <section class="contact hv-hero">
    <div class="wrap contact-grid">
      <div class="contact-text">
        <p class="crumbs light"><a href="{home}">{t('Home', 'Inicio')}</a> &nbsp;/&nbsp; {t('Home Value', 'Valor de su casa')}</p>
        <p class="eyebrow light">{t('Free Home Value Report', 'Reporte gratis del valor de su casa')}</p>
        <h1>{t('What&rsquo;s your home worth?', '¿Cuánto vale su casa?')}</h1>
        <p>{t('Online estimates can be off by tens of thousands of dollars. I&rsquo;ll prepare a free, no-obligation home value report based on real recent sales near you, from a local Sioux Falls agent, not an algorithm.',
              'Los cálculos en línea pueden fallar por miles de dólares. Le preparo un reporte gratis y sin compromiso con el valor de su casa, basado en ventas reales y recientes cerca de usted, hecho por un agente local de Sioux Falls, no por una computadora.')}</p>
        <ul class="hv-points">
          <li>{t('Recent sales and active listings near you', 'Ventas recientes y casas en venta cerca de usted')}</li>
          <li>{t('A realistic price range for today&rsquo;s market', 'Un rango de precio realista para el mercado de hoy')}</li>
          <li>{t('Simple tips to get the most when you sell', 'Consejos sencillos para obtener más al vender')}</li>
        </ul>
        <p class="contact-big"><a href="tel:+16058389140">605-838-9140</a></p>
        <p class="book-call"><a href="https://calendar.app.google/rymyVUbd555Y3xSDA" target="_blank" rel="noopener" class="btn btn-ghost"><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M7 2h2v2h6V2h2v2h3a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h3zm12 8H5v9h14zM5 6v2h14V6z"/></svg> {t('Book a 15-Min Call', 'Agendar una llamada')}</a></p>
        <p class="hv-lang"><a href="{other}">{t('Ver en español', 'View in English')}</a></p>
      </div>
      <form action="https://api.web3forms.com/submit" method="POST" class="form wizard" id="leadForm" data-kind="home-value" data-sheet="{SHEET}" novalidate>
        <input type="hidden" name="access_key" value="d0023d26-ed18-4970-8a35-c3de9e5f7e6c">
        <input type="hidden" name="subject" value="{t('Home value request from website', 'Home value request from website (ESPAÑOL)')}">
        <input type="hidden" name="from_name" value="Marcos Diaz Website">
        <input type="hidden" name="Looking to" value="Home value">
        <input type="checkbox" name="botcheck" class="hidden" tabindex="-1" autocomplete="off">

        <div class="progress" aria-hidden="true"><span></span></div>
        <p class="step-count">{t('Step <b>1</b> of 3', 'Paso <b>1</b> de 3')}</p>

        <fieldset class="step active" data-step="1">
          <legend>{t('What&rsquo;s the property address?', '¿Cuál es la dirección de la casa?')}</legend>
          <label class="full">{t('Street address, city', 'Dirección y ciudad')}<input type="text" name="Address" autocomplete="street-address" placeholder="{t('123 Main St, Sioux Falls', '123 Main St, Sioux Falls')}" required></label>
          <div class="nav-btns"><span></span><button type="button" class="btn btn-gold next" disabled>{t('Continue', 'Continuar')}</button></div>
        </fieldset>

        <fieldset class="step" data-step="2">
          <legend>{t('When are you thinking of selling?', '¿Cuándo piensa vender?')}</legend>
          <div class="choices">
{''.join(ch('Timeline', v, s, m) for v, s, m in opts)}          </div>
          <div class="nav-btns"><button type="button" class="btn-back back">{t('← Back', '← Atrás')}</button><button type="button" class="btn btn-gold next" disabled>{t('Continue', 'Continuar')}</button></div>
        </fieldset>

        <fieldset class="step" data-step="3">
          <legend>{t('Where should I send your report?', '¿A dónde le envío su reporte?')}</legend>
          <label class="full">{t('First &amp; last name', 'Nombre y apellido')}<input type="text" name="Name" autocomplete="name" required></label>
          <div class="two">
            <label>{t('Phone', 'Teléfono')}<input type="tel" name="Phone" autocomplete="tel" required></label>
            <label>{t('Email', 'Correo electrónico')}<input type="email" name="email" autocomplete="email" required></label>
          </div>
          <p class="error" role="alert"></p>
          <div class="nav-btns"><button type="button" class="btn-back back">{t('← Back', '← Atrás')}</button><button type="submit" class="btn btn-gold">{t('Get My Home Value', 'Recibir mi reporte')}</button></div>
          <p class="fine">{t('Free and no obligation. Your information goes only to me and is never sold.', 'Gratis y sin compromiso. Su información es solo para mí y nunca se vende.')} <a href="{priv}">{t('Privacy notice', 'Aviso de privacidad')}</a></p>
        </fieldset>

        <div class="step sent" data-step="4" aria-live="polite">
          <div class="check" aria-hidden="true"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24"/><path d="M15 27l7 7 15-16"/></svg></div>
          <h3>{t('Thank you', 'Gracias')}<span class="sent-name"></span>!</h3>
          <p>{t('I&rsquo;m on it. I&rsquo;ll review recent sales near your home and reach out personally, usually within one business day.', 'Ya estoy trabajando en ello. Voy a revisar las ventas recientes cerca de su casa y me comunicaré con usted personalmente, por lo general en un día hábil.')}</p>
          <p class="fine">{t('Need me sooner? Call or text', '¿Me necesita antes? Llame o envíe texto al')} <a href="tel:+16058389140">605-838-9140</a>.</p>
        </div>
      </form>
    </div>
  </section>
  <section class="page-body">
    <div class="wrap">
      <div class="hv-steps">
        <div><span class="step-n">1</span><h3>{t('Tell me about your home', 'Cuénteme de su casa')}</h3><p>{t('Share the address and your timeline. It takes about 30 seconds.', 'Comparta la dirección y cuándo piensa vender. Toma unos 30 segundos.')}</p></div>
        <div><span class="step-n">2</span><h3>{t('I run the numbers', 'Yo hago el análisis')}</h3><p>{t('I compare your home to recent sales, active listings, and current buyer demand in your neighborhood.', 'Comparo su casa con ventas recientes, casas en venta y la demanda actual en su vecindario.')}</p></div>
        <div><span class="step-n">3</span><h3>{t('You get your report', 'Usted recibe su reporte')}</h3><p>{t('I&rsquo;ll walk you through your value and options, with no pressure to list.', 'Le explico el valor y sus opciones, sin ninguna presión para vender.')}</p></div>
      </div>
    </div>
  </section>'''

hv_alts = ('<link rel="alternate" hreflang="en" href="https://605homesearch.com/home-value/">\n'
           '<link rel="alternate" hreflang="es" href="https://605homesearch.com/es/valor-de-casa/">\n'
           '<link rel="alternate" hreflang="x-default" href="https://605homesearch.com/home-value/">\n')
page('home-value/index.html', 'What\'s My Home Worth? Free Sioux Falls Home Value Report | Marcos Diaz',
     'Get a free, no-obligation home value report for your Sioux Falls, Tea, Harrisburg or Brandon home, based on real recent sales near you. From Marcos Diaz, Keller Williams.',
     hv_body(False), canonical='https://605homesearch.com/home-value/', alt_es='../es/valor-de-casa/', head_extra=hv_alts)
page('es/valor-de-casa/index.html', '¿Cuánto vale mi casa? Reporte gratis en Sioux Falls | Marcos Diaz',
     'Reciba un reporte gratis y sin compromiso del valor de su casa en Sioux Falls, Tea, Harrisburg o Brandon, basado en ventas reales cerca de usted. Se habla español.',
     hv_body(True), lang='es', canonical='https://605homesearch.com/es/valor-de-casa/', alt_en='../../home-value/', head_extra=hv_alts)


# ---------- Review page (bilingual, not indexed) ----------
REVIEW = 'https://search.google.com/local/writereview?placeid=ChIJ2UyxjuTJjocRDyUNVRImzBw'
rv_body = f'''  <section class="page-hero review-page">
    <div class="wrap narrow">
      <p class="eyebrow">Thank You · Gracias</p>
      <h1>Thank you for trusting me with your move.</h1>
      <p class="lead">If you have a minute, a quick Google review helps other families find an agent they can trust. It means a lot to me.</p>
      <a href="{REVIEW}" class="btn btn-gold btn-lg">★ Leave a Google Review</a>
      <hr class="rv-rule">
      <h2 lang="es">Gracias por confiar en mí.</h2>
      <p class="lead" lang="es">Si tiene un minuto, una reseña rápida en Google ayuda a otras familias a encontrar un agente de confianza. Significa mucho para mí.</p>
      <a href="{REVIEW}" class="btn btn-gold btn-lg" lang="es">★ Dejar una reseña en Google</a>
      <p class="muted rv-sign">— Marcos Diaz, REALTOR® · <a href="tel:+16058389140">605-838-9140</a></p>
    </div>
  </section>'''
page('review/index.html', 'Leave a Review | Marcos Diaz, REALTOR®',
     'Thank you for working with Marcos Diaz. Leave a quick Google review.',
     rv_body, canonical='https://605homesearch.com/review/', head_extra='<meta name="robots" content="noindex">\n', news=False)
