# Marcos Diaz – Real Estate Website

Personal website for Marcos Diaz, REALTOR® at Keller Williams Realty Sioux Falls.

Live at **https://605homesearch.com**

- `index.html`: the main page (English)
- `es/`: Spanish version (`es/index.html`) and Spanish privacy notice
- `areas/`: neighborhood pages (Sioux Falls, SW/SE Sioux Falls, Tea, Harrisburg, Brandon)
- `privacy.html`: privacy notice
- `site.js`: shared behavior (menu, lead form, reviews slideshow, mortgage calculator)
- `thank-you.html`: fallback thank-you page
- `sitemap.xml`, `robots.txt`: for search engines
- `styles.css`: colors, fonts, and layout (ivory, navy, and gold theme)
- `fonts/`: self-hosted Cormorant Garamond and Jost
- `images/`: photos, logo, and favicon

Hosted on GitHub Pages. Every change pushed to `main` is published automatically by `.github/workflows/deploy.yml`. The domain is managed in Cloudflare DNS (DNS only) and set under Settings → Pages → Custom domain.

## Lead automation
`automation/lead-automation.gs` is a Google Apps Script attached to the "605homesearch.com – Website Leads" Google Sheet. The website form posts each lead to it (URL in the form's `data-sheet` attribute); it saves the lead to the sheet, emails Marcos an instant alert, sends the lead an auto-reply (English/Spanish), and emails a weekly summary on Mondays.
