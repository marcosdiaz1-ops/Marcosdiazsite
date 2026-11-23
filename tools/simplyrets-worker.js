// Cloudflare Worker: keeps the real SimplyRETS API key/secret private for 605homesearch.com/search-preview/.
// The browser calls this Worker; the Worker adds the secret login and asks SimplyRETS for the listings.
//
// Setup (Cloudflare dashboard → Workers & Pages → Create → Worker):
//   1. Paste this whole file as the Worker code and Deploy.
//   2. Settings → Variables and Secrets → add two *Secrets*:
//        SRETS_KEY    = your SimplyRETS API key
//        SRETS_SECRET = your SimplyRETS API secret
//   3. Settings → Domains & Routes → add Custom Domain: listings.605homesearch.com
//   4. In search-preview/index.html set  var LIVE_API = 'https://listings.605homesearch.com';
//
// Only read-only listing requests are allowed, and only from 605homesearch.com.

const UPSTREAM = 'https://api.simplyrets.com';
// MLS fields meant only for agents (showing instructions, private remarks): removed before anything reaches the browser
const PRIVATE = ['privateRemarks', 'showingInstructions', 'showingContactName', 'showingContactPhone'];
const ALLOWED_ORIGINS = ['https://605homesearch.com', 'https://www.605homesearch.com'];

function cors(origin) {
  const ok = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': ok,
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Expose-Headers': 'X-Total-Count',
    'Vary': 'Origin',
  };
}

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin') || '';
    const headers = cors(origin);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });
    if (request.method !== 'GET') return new Response('Method not allowed', { status: 405, headers });
    if (origin && !ALLOWED_ORIGINS.includes(origin)) return new Response('Forbidden', { status: 403, headers });

    const url = new URL(request.url);
    const auth = 'Basic ' + btoa(env.SRETS_KEY + ':' + env.SRETS_SECRET);

    // Last time the MLS data was refreshed (for the disclaimer)
    if (url.pathname === '/last-update') {
      const r = await fetch(UPSTREAM + '/', { method: 'OPTIONS', headers: { Authorization: auth } });
      return new Response(await r.text(), { status: r.status, headers: { ...headers, 'Content-Type': 'application/json' } });
    }

    // Upcoming public open houses, as a small list: [{ mlsId, start, end }]. Broker-only and private ones are left out.
    if (url.pathname === '/openhouses') {
      const cache = caches.default;
      const key = new Request(url.origin + '/openhouses', { method: 'GET' });
      let res = await cache.match(key);
      if (!res) {
        const r = await fetch(UPSTREAM + '/openhouses?limit=500', { headers: { Authorization: auth, Accept: 'application/json' } });
        let body = '[]';
        if (r.ok) {
          try {
            const list = await r.json();
            body = JSON.stringify((Array.isArray(list) ? list : [])
              .filter(o => o && o.listing && o.listing.mlsId && o.startTime && !/broker|private|office|caravan|agent|realtor/i.test(o.type || '') && o.listing.internetEntireListingDisplay !== false)
              .map(o => ({ mlsId: o.listing.mlsId, start: o.startTime, end: o.endTime || null })));
          } catch (e) { body = '[]'; }
        }
        // if the feed doesn't include open houses yet, answer "none" and check again in an hour instead of on every visit
        res = new Response(body, { status: 200, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=' + (r.ok ? 900 : 3600) } });
        ctx.waitUntil(cache.put(key, res.clone()));
      }
      const out = new Response(res.body, res);
      Object.entries(headers).forEach(([k, v]) => out.headers.set(k, v));
      return out;
    }

    // Listing search (/properties) and single listing (/properties/<mlsId>) only
    if (!/^\/properties(\/[A-Za-z0-9_-]+)?$/.test(url.pathname)) return new Response('Not found', { status: 404, headers });

    // ?pins=1 returns a small list (location, price, status) for every map pin, up to 500 homes
    const pins = url.searchParams.get('pins') === '1';
    // keep the query exactly as sent (commas in "points" stay as they are), minus pins=1
    let qs = url.search.replace(/^\?/, '').split('&').filter(p => p && p !== 'pins=1' && !(pins && /^limit=/.test(p)));
    if (pins) qs.push('limit=500');
    const target = UPSTREAM + url.pathname + (qs.length ? '?' + qs.join('&') : '');
    const cache = caches.default;
    const cacheKey = new Request(url.origin + url.pathname + url.search, { method: 'GET' });
    let res = await cache.match(cacheKey);
    if (!res) {
      const r = await fetch(target, { headers: { Authorization: auth, Accept: 'application/json' } });
      let body = await r.text();
      if (r.ok) {
        try {
          const data = JSON.parse(body);
          const list = Array.isArray(data) ? data : [data];
          // Never send agent-only MLS fields to the public website
          list.forEach(h => { if (h && typeof h === 'object') PRIVATE.forEach(k => delete h[k]); });
          body = JSON.stringify(pins
            ? list.filter(h => h && h.internetEntireListingDisplay !== false && h.geo && h.geo.lat).map(h => ({
                mlsId: h.mlsId, lat: h.geo.lat, lng: h.geo.lng, listPrice: h.listPrice, originalListPrice: h.originalListPrice || null,
                dom: h.mls ? h.mls.daysOnMarket : null, status: h.mls ? (h.mls.statusText || h.mls.status) : null }))
            : data);
        } catch (e) { /* not JSON: pass through */ }
      }
      const rh = { 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=300' };
      const total = r.headers.get('X-Total-Count'); if (total) rh['X-Total-Count'] = total;  // how many homes match (asked for with count=true)
      res = new Response(body, { status: r.status, headers: rh });
      if (r.ok) ctx.waitUntil(cache.put(cacheKey, res.clone()));
    }
    const out = new Response(res.body, res);
    Object.entries(headers).forEach(([k, v]) => out.headers.set(k, v));
    return out;
  },
};
