# Monthly market update (/market/ and /es/mercado/)

A scheduled Claude task checks for the Realtor Association of the Sioux Empire (RASE) monthly report and updates both pages as soon as it's out.

1. Write `config.json` (see `example-config.json`): month_key (YYYY-MM), median (number), updated_iso, and for `en` and `es`: title, suffix, desc, headline, lead, stats (the `<div>` rows inside `<dl class="mstats">`, 6 or 8 rows), prose (the article HTML; put `{CHART}` where the chart SVG goes).
2. `python3 automation/market-update/update_market.py config.json`, which updates both pages, the median chart (last 12 months, stored in `months.json`) and the sitemap dates.
3. Check, commit, and push to `main`.

Only use numbers from the published report. Never estimate.
