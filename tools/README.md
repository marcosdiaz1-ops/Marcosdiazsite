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
