# Build the 6 guide PDFs into guides/files/. Needs a local server on :8766 serving the repo root
# (python3 -m http.server 8766) and Playwright + Chrome.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from guides_content import GUIDES

BASE = 'http://localhost:8766'
OUT = os.path.join(ROOT, 'guides', 'files')
os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(ROOT, 'guides', '_tmp')
os.makedirs(TMP, exist_ok=True)

CSS = f'''
@import url("{BASE}/fonts/fonts.css");
@page {{ size: Letter; margin: .8in .85in .85in; }}
@page full {{ margin: 0; }}
.cover, .back {{ page: full; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font-family: "Jost", Arial, sans-serif; font-weight: 300; color: #3d4356; font-size: 11pt; line-height: 1.55; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.cover {{ width: 8.5in; height: 11in; background: #13203b; color: #fff; position: relative; padding: 1in .9in; page-break-after: always; overflow: hidden; }}
.cover::before {{ content: ""; position: absolute; inset: .35in; border: 1px solid rgba(215,180,140,.45); }}
.cover .logo {{ display: flex; align-items: center; gap: 14px; position: relative; }}
.cover .logo img {{ width: 46px; height: 46px; filter: brightness(0) invert(1); opacity: .9; }}
.cover .logo span {{ letter-spacing: .32em; text-transform: uppercase; font-size: 11pt; font-weight: 400; }}
.cover .logo small {{ display: block; letter-spacing: .26em; color: #d7b48c; font-size: 7.5pt; }}
.cover .mid {{ position: absolute; left: .9in; right: .9in; top: 3.3in; }}
.cover .eyebrow {{ color: #d7b48c; letter-spacing: .32em; text-transform: uppercase; font-size: 8.5pt; font-weight: 400; }}
.cover h1 {{ font-family: "Cormorant Garamond", Georgia, serif; font-weight: 400; font-size: 46pt; line-height: 1.04; margin: 18px 0 22px; }}
.cover .sub {{ font-size: 13pt; color: #e6e0d4; max-width: 5.4in; }}
.cover .rule {{ width: 70px; height: 1px; background: #d7b48c; margin: 30px 0; }}
.cover .foot {{ position: absolute; left: .9in; right: .9in; bottom: .9in; font-size: 9.5pt; color: #cfc8bb; display: flex; justify-content: space-between; align-items: flex-end; }}
.cover .foot b {{ color: #fff; font-weight: 400; font-size: 11pt; display: block; }}
.content {{ padding: 0; }}
.content h2 {{ font-family: "Cormorant Garamond", Georgia, serif; font-weight: 500; color: #13203b; font-size: 20pt; margin: 26px 0 8px; line-height: 1.15; page-break-after: avoid; break-after: avoid; break-inside: avoid; }}
.content h2 + p, .content h2 + ul {{ break-before: avoid; }}
.content h2:first-child {{ margin-top: 0; }}
.content h2::before {{ content: ""; display: block; width: 38px; height: 1px; background: #b98b5c; margin-bottom: 10px; }}
.content p {{ margin: 0 0 10px; }}
.content ul {{ margin: 4px 0 12px; padding-left: 18px; }}
.content li {{ margin-bottom: 5px; }}
.content li::marker {{ color: #b98b5c; }}
.content b {{ font-weight: 500; color: #1a2237; }}
.content ul.check {{ list-style: none; padding-left: 0; columns: 2; column-gap: 28px; }}
.content ul.check li {{ padding-left: 24px; position: relative; break-inside: avoid; }}
.content ul.check li::before {{ content: ""; position: absolute; left: 0; top: 4px; width: 12px; height: 12px; border: 1px solid #b98b5c; }}
.tip {{ background: #f8f5f0; border-left: 2px solid #b98b5c; padding: 10px 14px; font-size: 10pt; }}
.sources {{ margin-top: 22px; font-size: 8pt; color: #8a8579; border-top: 1px solid #e2d8ca; padding-top: 10px; }}
.back {{ width: 8.5in; height: 11in; background: #f8f5f0; page-break-before: always; padding: 1in .9in; position: relative; }}
.back .card {{ display: grid; grid-template-columns: 2.3in 1fr; gap: .45in; align-items: center; margin-top: 1.4in; }}
.back img.photo {{ width: 2.3in; height: 3in; object-fit: cover; object-position: top; }}
.back h2 {{ font-family: "Cormorant Garamond", Georgia, serif; font-weight: 400; color: #13203b; font-size: 32pt; margin: 6px 0 12px; line-height: 1.05; }}
.back .eyebrow {{ color: #8a6236; letter-spacing: .3em; text-transform: uppercase; font-size: 8pt; }}
.back p {{ margin: 0 0 8px; }}
.back .contact {{ margin-top: 18px; font-size: 11.5pt; color: #13203b; line-height: 1.9; }}
.back .contact b {{ font-weight: 500; }}
.back .legal {{ position: absolute; left: .9in; right: .9in; bottom: .7in; font-size: 7.5pt; color: #8a8579; line-height: 1.5; }}
'''

def build(key, lang):
    g = GUIDES[key]; es = lang == 'es'
    title = g['title_es' if es else 'title_en']
    eyebrow = 'Guía gratis' if es else 'Free Guide'
    back = f'''<div class="back">
  <div class="card">
    <img class="photo" src="{BASE}/images/marcos-about.jpg" alt="">
    <div>
      <p class="eyebrow">{'¿Listo para el siguiente paso?' if es else 'Ready for the next step?'}</p>
      <h2>{'Hablemos.' if es else "Let's talk."}</h2>
      <p>{'Soy Marcos Diaz, agente de bienes raíces bilingüe con Keller Williams Realty Sioux Falls. Le ayudo a comprar o vender con confianza, en inglés o en español.' if es else "I'm Marcos Diaz, a bilingual REALTOR® with Keller Williams Realty Sioux Falls. I help buyers and sellers move with confidence, in English or Spanish."}</p>
      <div class="contact">
        <b>{'Llame o envíe texto' if es else 'Call or text'}:</b> 605-838-9140<br>
        <b>Email:</b> marcosdiaz1@kw.com<br>
        <b>Web:</b> 605homesearch.com{'/es/' if es else ''}<br>
        <b>{'Agende una llamada' if es else 'Book a call'}:</b> 605homesearch.com/#contact
      </div>
    </div>
  </div>
  <p class="legal">Marcos Diaz, REALTOR®, Broker Associate, Keller Williams Realty Sioux Falls, 6300 S Connie Ave, Sioux Falls, SD 57108. {'Cada oficina es de propiedad y operación independiente. Igualdad de oportunidades de vivienda. Esta guía es informativa y no es asesoría legal, fiscal ni de préstamos; confirme los detalles con los profesionales adecuados.' if es else 'Each office is independently owned and operated. Equal Housing Opportunity. This guide is for general information and is not legal, tax or lending advice; confirm details with the right professionals.'}</p>
</div>'''
    html = f'''<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>
<div class="cover">
  <div class="logo"><img src="{BASE}/images/logo.svg" alt=""><div><span>Marcos Diaz</span><small>{'Bienes Raíces' if es else 'Real Estate'}</small></div></div>
  <div class="mid">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{title}</h1>
    <div class="rule"></div>
    <p class="sub">{g['sub_es' if es else 'sub_en']}</p>
  </div>
  <div class="foot"><div><b>Marcos Diaz, REALTOR®</b>Keller Williams Realty Sioux Falls</div><div style="text-align:right">605-838-9140<br>605homesearch.com</div></div>
</div>
<div class="content">
{g['es' if es else 'en']}
<p class="sources">{g['sources_es' if es else 'sources']}</p>
</div>
{back}
</body></html>'''
    name = g['file_es' if es else 'file_en']
    tmp = os.path.join(TMP, name.replace('.pdf', '.html'))
    open(tmp, 'w').write(html)
    return name, tmp

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg = b.new_page()
        for key in GUIDES:
            for lang in ('en', 'es'):
                name, tmp = build(key, lang)
                rel = os.path.relpath(tmp, ROOT)
                pg.goto(f'{BASE}/{rel}'); pg.wait_for_timeout(700)
                pg.pdf(path=os.path.join(OUT, name), format='Letter', print_background=True, prefer_css_page_size=True)
                print('built', name)
        b.close()
    import shutil; shutil.rmtree(TMP)
