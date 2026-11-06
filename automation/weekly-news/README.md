# Weekly "This Week in Sioux Falls" blog post

A scheduled Claude task writes one original news roundup every week (English + Spanish) and pushes it here.

1. Write the article body HTML for each language (no copying news articles: summarize in our own words, add "what it means for homeowners/buyers", link to the source).
2. `python3 automation/weekly-news/make_post.py post-config.json` builds both post pages from an existing post template (see `example-post-config.json`).
3. `python3 automation/weekly-news/add_listing.py listing-config.json` adds the cards to `blog/index.html` and `es/blog/index.html` and the URLs to `sitemap.xml` (see `example-listing-config.json`).
4. Commit and push to `main`; GitHub Pages publishes automatically.
