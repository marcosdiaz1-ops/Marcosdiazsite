# Adds basic schema.org data (WebPage + breadcrumb, tied to Marcos as the agent) to any public page
# that doesn't have structured data yet. Search engines and AI assistants use this to understand
# what each page is and who it belongs to. Safe to run again and again: pages that already have
# schema, or are hidden (noindex), are skipped. Runs automatically on every deploy.
import os, re, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://605homesearch.com'
AGENT = {'@type': 'RealEstateAgent', '@id': SITE + '/#marcos-diaz', 'name': 'Marcos Diaz, Broker Associate',
         'url': SITE + '/', 'telephone': '+1-605-838-9140',
         'parentOrganization': {'@type': 'Organization', 'name': 'Keller Williams Realty Sioux Falls'}}
# Pages that are tools get a little more detail
APPS = ('calculators/', 'calculadoras/')
SKIP = ('tools/', '.git/', 'automation/')


def main():
    added = 0
    for dp, dn, fn in os.walk(ROOT):
        rel_dir = os.path.relpath(dp, ROOT)
        if any((rel_dir + '/').startswith(s) for s in SKIP):
            continue
        for f in fn:
            if not f.endswith('.html'):
                continue
            fp = os.path.join(dp, f); doc = open(fp, encoding='utf-8').read()
            if 'application/ld+json' in doc or 'noindex' in doc or '</head>' not in doc:
                continue
            canon = re.search(r'<link rel="canonical" href="([^"]+)"', doc)
            title = re.search(r'<title>(.*?)</title>', doc, re.S)
            if not canon or not title:
                continue
            url = canon.group(1); name = html.unescape(title.group(1)).strip()
            desc = re.search(r'<meta name="description" content="([^"]*)"', doc)
            es = '<html lang="es"' in doc
            short = re.split(r'\s+[|–-]\s+', name)[0]
            page = {'@type': 'WebPage', '@id': url + '#webpage', 'url': url, 'name': name, 'inLanguage': 'es' if es else 'en',
                    'isPartOf': {'@type': 'WebSite', 'url': SITE + '/', 'name': 'Marcos Diaz, Keller Williams Realty Sioux Falls'},
                    'about': AGENT, 'publisher': {'@id': AGENT['@id']}}
            if desc:
                page['description'] = html.unescape(desc.group(1))
            graph = [page, {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Inicio' if es else 'Home', 'item': SITE + ('/es/' if es else '/')},
                {'@type': 'ListItem', 'position': 2, 'name': short, 'item': url}]}]
            if any(a in url for a in APPS):
                graph.append({'@type': 'WebApplication', 'name': short, 'url': url, 'applicationCategory': 'FinanceApplication',
                              'operatingSystem': 'Any', 'isAccessibleForFree': True, 'inLanguage': 'es' if es else 'en',
                              'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}, 'provider': {'@id': AGENT['@id']}})
            ld = '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False).replace('</', '<\\/') + '</script>\n'
            doc = doc.replace('</head>', ld + '</head>', 1)
            open(fp, 'w', encoding='utf-8').write(doc); added += 1
            print('schema added:', os.path.relpath(fp, ROOT))
    print(added, 'pages updated')


if __name__ == '__main__':
    main()
