"""Make the new map/photo search the real Search Homes page (run once RASE gives final approval).

  python3 tools/go_live_search.py           # search-preview/ -> search/, then Spanish search
  python3 tools/go_live_search.py --undo    # put the old KW/Paragon search page back

What it does:
  - Copies search-preview/index.html to search/index.html, but keeps the live page's
    title, description, canonical and language links (so Google can index it).
  - Removes the "noindex" tag and the demo banner.
  - Saves the old Search Homes page to tools/search-old-kw-page.html so --undo can restore it.
  - Rebuilds the Spanish search (es/buscar-casas/) with tools/build_es_search.py live.
Listing alert emails and the affordability calculator already link to /search/, so they
start opening the new search as soon as this is pushed.
"""
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'search/index.html')
PREVIEW = os.path.join(ROOT, 'search-preview/index.html')
BACKUP = os.path.join(ROOT, 'tools/search-old-kw-page.html')
ES_LIVE = os.path.join(ROOT, 'es/buscar-casas/index.html')
ES_BACKUP = os.path.join(ROOT, 'tools/buscar-casas-old-kw-page.html')

if '--undo' in sys.argv:
    shutil.copy(BACKUP, LIVE); shutil.copy(ES_BACKUP, ES_LIVE)
    print('Old search pages restored.'); sys.exit(0)

live = open(LIVE).read()
if 'id="sp-' in live or 'sp-filters' in live:
    sys.exit('search/ is already the new search. Nothing to do.')

shutil.copy(LIVE, BACKUP); shutil.copy(ES_LIVE, ES_BACKUP)

head = re.search(r'<title>.*?<link rel="alternate" hreflang="x-default"[^\n]*\n', live, re.S).group(0)
new = open(PREVIEW).read()
new, n = re.subn(r'<title>.*?<meta name="robots" content="noindex, nofollow">\n', lambda m: head, new, count=1, flags=re.S)
assert n == 1, 'could not swap the page head'
new = re.sub(r'<div class="demo-banner">.*?</div>\n?', '', new, count=1)
assert 'noindex' not in new
open(LIVE, 'w').write(new)

subprocess.run([sys.executable, os.path.join(ROOT, 'tools/build_es_search.py'), 'live'], check=True)
es = open(ES_LIVE).read()
assert 'noindex' not in es and 'hreflang="es"' in es
print('New search is now at /search/ and /es/buscar-casas/. Commit and push to publish.')
