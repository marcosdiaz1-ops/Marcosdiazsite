"""Update /market/ and /es/mercado/ with a new monthly report.
Usage: python3 automation/market-update/update_market.py config.json
See README.md for the config keys. Edits the live HTML directly (tools/build_pages.py is out of date; do not run it)."""
import re, sys, json, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
cfg = json.loads(pathlib.Path(sys.argv[1]).read_text())
months = json.loads((HERE / 'months.json').read_text())
months = [m for m in months if m[0] != cfg['month_key']] + [[cfg['month_key'], cfg['median']]]
months.sort()
(HERE / 'months.json').write_text(json.dumps(months))
show = months[-12:]
EN_M = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
ES_M = 'ene feb mar abr may jun jul ago sep oct nov dic'.split()

def chart(es=False):
    vals = [v for _, v in show]
    lo = int(math.floor((min(vals) - 10000) / 20000) * 20000)
    hi = int(math.ceil((max(vals) + 5000) / 20000) * 20000)
    W, H, pad_l, pad_b, pad_t = 640, 280, 56, 34, 24
    bw = (W - pad_l - 20) / len(show)
    label = "Precio mediano mensual en Sioux Falls" if es else "Monthly median sale price in Sioux Falls"
    p = [f'<svg viewBox="0 0 {W} {H}" class="mchart" role="img" aria-label="{label}">']
    for v in range(lo, hi + 1, 20000):
        y = pad_t + (H - pad_t - pad_b) * (1 - (v - lo) / (hi - lo))
        p.append(f'<line x1="{pad_l}" x2="{W-10}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/><text x="{pad_l-8}" y="{y+4:.1f}" class="ylab" text-anchor="end">${v//1000}K</text>')
    for i, (k, v) in enumerate(show):
        x = pad_l + 10 + i * bw
        top = pad_t + (H - pad_t - pad_b) * (1 - (v - lo) / (hi - lo)); h = (H - pad_b) - top
        cls = "bar last" if i == len(show) - 1 else "bar"
        m = int(k[5:7]) - 1
        lab = (ES_M if es else EN_M)[m]
        if k[:4] != show[-1][0][:4]:
            lab += f" '{k[2:4]}"
        p.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw*0.62:.1f}" height="{h:.1f}" class="{cls}"/>')
        p.append(f'<text x="{x+bw*0.31:.1f}" y="{top-7:.1f}" class="vlab" text-anchor="middle">${v/1000:.0f}K</text>')
        p.append(f'<text x="{x+bw*0.31:.1f}" y="{H-12}" class="xlab" text-anchor="middle">{lab}</text>')
    p.append('</svg>')
    return ''.join(p)

def apply(path, L, es):
    t = path.read_text()
    def sub(pat, rep):
        nonlocal t
        t2, k = re.subn(pat, lambda m: rep, t, count=1, flags=re.S)
        assert k == 1, f'{path}: pattern not found: {pat[:60]}'
        t = t2
    sub(r'<title>.*?</title>', f'<title>{L["title"]}{L["suffix"]}</title>')
    sub(r'(?<=<meta name="description" content=")[^"]*', L['desc'])
    sub(r'(?<=<meta property="og:title" content=")[^"]*', L['title'] + L['suffix'])
    sub(r'(?<=<meta property="og:description" content=")[^"]*', L['desc'])
    for k, v in (('twitter:title', L['title'] + L['suffix']), ('twitter:description', L['desc'])):
        if f'name="{k}"' in t:
            sub(rf'(?<=<meta name="{k}" content=")[^"]*', v)
    sub(r'(?<="headline": ")[^"]*', L['headline'])
    sub(r'(?<="dateModified": ")[^"]*', cfg['updated_iso'])
    sub(r'<p class="lead">.*?</p>', f'<p class="lead">{L["lead"]}</p>')
    sub(r'      <dl class="mstats">.*?</dl>', '      <dl class="mstats">\n' + L['stats'].strip('\n') + '\n      </dl>')
    prose = L['prose'].replace('{CHART}', chart(es))
    sub(r'        <div class="prose">.*?        </div>(?=\s*<aside class="side-card">)', '        <div class="prose">\n' + prose.strip('\n') + '\n        </div>')
    path.write_text(t)

apply(ROOT / 'market/index.html', cfg['en'], False)
apply(ROOT / 'es/mercado/index.html', cfg['es'], True)
# Homepage "Market Update" band (EN + ES) — keeps the homepage in step with the full report
EN_FULL = 'January February March April May June July August September October November December'.split()
ES_FULL = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
B = cfg['band']  # {"median_chg": "-4.6%", "sold": "203", "sold_chg": "-26%", "supply": "4.0"}
yr, mo = cfg['month_key'][:4], int(cfg['month_key'][5:7]) - 1
med = f"${cfg['median']/1000:.1f}K".replace('.0K', 'K')
fix = lambda s: s.replace('-', '−')
for path, es in ((ROOT / 'index.html', False), (ROOT / 'es/index.html', True)):
    t = path.read_text()
    import datetime as _dt
    up = _dt.date.fromisoformat(cfg['updated_iso'][:10])
    EN_AB = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
    ES_AB = 'ene feb mar abr may jun jul ago sep oct nov dic'.split()
    eyebrow = (f'Reporte de {ES_FULL[mo]} · actualizado {up.day} {ES_AB[up.month-1]}' if es
               else f'{EN_FULL[mo]} report · Updated {EN_AB[up.month-1]} {up.day}')
    rows = (f'<div><dt>{med}</dt><dd>Precio mediano · {fix(B["median_chg"])}</dd></div>\n'
            f'        <div><dt>{B["sold"]}</dt><dd>Casas vendidas · {fix(B["sold_chg"])}</dd></div>\n'
            f'        <div><dt>{B["supply"]}</dt><dd>Meses de inventario</dd></div>') if es else (
            f'<div><dt>{med}</dt><dd>Median price · {fix(B["median_chg"])}</dd></div>\n'
            f'        <div><dt>{B["sold"]}</dt><dd>Homes sold · {fix(B["sold_chg"])}</dd></div>\n'
            f'        <div><dt>{B["supply"]}</dt><dd>Months of supply</dd></div>')
    t, k1 = re.subn(r'(<section class="market-band">.*?<p class="eyebrow light">)[^<]*', lambda m: m.group(1) + eyebrow, t, count=1, flags=re.S)
    t, k2 = re.subn(r'(<section class="market-band">.*?<dl class="mini">\s*).*?(\s*</dl>)', lambda m: m.group(1) + rows + m.group(2), t, count=1, flags=re.S)
    assert k1 == k2 == 1, f'{path}: market band not found'
    path.write_text(t)
sm = ROOT / 'sitemap.xml'; s = sm.read_text()
for u in ('https://605homesearch.com/market/', 'https://605homesearch.com/es/mercado/'):
    s, k = re.subn(r'(<loc>' + re.escape(u) + r'</loc>\s*<lastmod>)[^<]*', r'\g<1>' + cfg['updated_iso'], s)
    assert k == 1
sm.write_text(s)
print('ok: market pages updated for', cfg['month_key'])
