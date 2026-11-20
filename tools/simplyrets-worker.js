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
const ALLOWED_ORIGINS = ['https://605homesearch.com', 'https://www.605homesearch.com'];

function cors(origin) {
  const ok = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': ok,
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
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

    // Listing search (/properties) and single listing (/properties/<mlsId>) only
    if (!/^\/properties(\/[A-Za-z0-9_-]+)?$/.test(url.pathname)) return new Response('Not found', { status: 404, headers });

    const target = UPSTREAM + url.pathname + url.search;
    const cache = caches.default;
    const cacheKey = new Request(target, { method: 'GET' });
    let res = await cache.match(cacheKey);
    if (!res) {
      const r = await fetch(target, { headers: { Authorization: auth, Accept: 'application/json' } });
      res = new Response(r.body, { status: r.status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=300' } });
      if (r.ok) ctx.waitUntil(cache.put(cacheKey, res.clone()));
    }
    const out = new Response(res.body, res);
    Object.entries(headers).forEach(([k, v]) => out.headers.set(k, v));
    return out;
  },
};
