# Site build tools (not published)

- `build_pages.py` – privacy, area, market, home value and review pages (EN + ES)
- `build_es.py` – builds `es/index.html` from `index.html`
- `build_blog.py` – blog index + posts from `blog_posts.py`, updates `sitemap.xml`
- `lender.py` – preferred lender card

## Add a blog post
1. Append a new dict to `POSTS` in `blog_posts.py` (newest date shows first).
2. `python3 tools/build_blog.py`
3. Commit and push to `main`; GitHub Actions publishes to 605homesearch.com.

- `build_guides.py` + `guides_content.py`: build the 6 free-guide PDFs into guides/files/ (needs `python3 -m http.server 8766` running).
- `build_guide_pages.py`: builds /guides/ and /es/guias/ download pages (lead form) and adds them to the sitemap.
- `news.py`: monthly market-update signup band, added to every generated page by `page()` (pass news=False to skip) and to the homepage.
- `build_dpa.py`: down payment assistance pages (/down-payment-assistance/, /es/ayuda-pago-inicial/).
- Area pages: "See homes for sale" buttons use `town_search()` in build_pages.py (KW map search framed on each town).
- `build_resources.py`: ITIN mortgage and low-credit pages (EN + ES, Spanish-first SEO), with FAQPage schema.

- `go_live_search.py`: when RASE approves, makes the new map/photo search the real Search Homes page (EN + ES). `--undo` puts the old page back.
- `build_listing_pages.py`: Google-friendly pages for every home (/homes/...) and town (/homes-for-sale/, /es/casas-en-venta/), built from the MLS feed during each publish and every 4 hours. Off until go-live (data/listing-pages-on).
