/**
 * 605homesearch.com – New listing alerts (Google Apps Script)
 *
 * Lives in the "605homesearch.com – Listing Alert Leads" Google Sheet (separate from Website Leads).
 *
 * What it does:
 *   1. When someone taps "Get new listing alerts" on the website search, it saves them as a row
 *      (name, email, phone, their search) and emails Marcos a NEW ALERT LEAD notice.
 *   2. It emails the person a welcome with homes that match right now.
 *   3. Every morning it checks the MLS for NEW homes matching each person's search and emails
 *      them (daily or weekly, their choice). Each email has an unsubscribe link.
 *   4. Learns from them: when a signed-up person opens homes on the website (or from an alert
 *      email), each view is saved on the "Activity" tab. After 3+ views it updates their search
 *      (city, price range, beds) to match what they actually look at. Set "Auto-adjust" to No on
 *      a row to stop that for one person.
 *   5. Hot lead notice: if someone opens the same home 3 times, Marcos gets a 🔥 email.
 *      "Call now" notice (email + phone alert): someone opens 6+ different homes in 24 hours,
 *      comes back after 14+ days without looking, or saves (♥) a home.
 *   6. Besides new listings, alert emails include PRICE DROPS on homes that match and homes
 *      BACK ON THE MARKET. A hidden "Snapshots" tab remembers each person's matching homes and
 *      prices so it can spot the changes.
 *   7. Monday 7 AM "who to call this week" email to Marcos: new sign-ups, the most active
 *      people (ranked), homes they keep opening, and everyone gone quiet for 2+ weeks.
 *   8. Saved homes: when a signed-up person taps ♥ on a home, it's kept on the "Saved homes" tab. Their
 *      emails then also tell them about price cuts, back on market, pending, sold, and open houses on those homes.
 *   9. Emails are laid out like Zillow's (one home: "New listing for sale at $X"; several: a roundup),
 *      with "Our recommendations for you" at the bottom.
 *
 * Setup (one time, about 5 minutes):
 *   - Open the Listing Alert Leads sheet → Extensions → Apps Script → delete what's there,
 *     paste this whole file → Save.
 *   - Pick "setup" in the function menu → Run → approve the permissions.
 *     (This formats the sheet and turns on the daily 8 AM check.)
 *   - Deploy → New deployment → type "Web app" → Execute as: Me → Who has access: Anyone → Deploy.
 *   - Copy the Web app URL and send it to Claude to connect it to the website.
 *
 * Status column: Active (gets emails), Unsubscribed (clicked unsubscribe), Paused (you stopped it).
 * You can change Status, How often, or the search columns by hand at any time.
 */

// ---------- Settings ----------
const OWNER_EMAIL = 'marcosdiaz1@kw.com';
const OWNER_NAME = 'Marcos Diaz';
const PHONE = '605-838-9140';
const SITE = 'https://605homesearch.com';
const SEARCH_PAGE = SITE + '/search/';           // where "See this home" links go
const SEARCH_PAGE_ES = SITE + '/es/buscar-casas/';  // same, for Spanish-speaking subscribers
const LISTINGS_API = 'https://listings.605homesearch.com/properties';
// Public web app link (used for the unsubscribe link in every email)
const WEBAPP_URL = 'https://script.google.com/macros/s/AKfycbxklqP-b5JNN1e2hsuwLXQvC0P6_4ZmJBORJLDojLWMwqWiUx5JFn0oiKDVXvu4c-6-/exec';
const MAX_HOMES_PER_EMAIL = 12;
const MAX_EMAILS_PER_RUN = 80;                    // stay well under Gmail's daily sending limit
// Instant phone alerts through the free ntfy app (same private topic as the website leads script)
const NTFY_TOPIC = 'md605-leads-1edb47408730';
const MAX_SIGNUPS_PER_DAY = 40;                   // safety limit against spam abuse
const OFFICE = 'Keller Williams Realty Sioux Falls, 6300 S Connie Ave, Sioux Falls, SD 57108 · 605-275-0555';

const HEADERS = ['Signed up', 'Name', 'Email', 'Phone', 'Search', 'Min price', 'Max price', 'Beds', 'Baths', 'Type',
                 'Map area', 'How often', 'Language', 'Status', 'Last sent', 'Homes sent', 'Source', 'Notes', 'ID',
                 'Auto-adjust', 'Views', 'Learned'];
const ACT_HEADERS = ['Date', 'Name', 'Email', 'MLS #', 'Price', 'Beds', 'Baths', 'City', 'Address', 'ID'];
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const C = {}; HEADERS.forEach(function (h, i) { C[h] = i; });
const TYPES = { residential: 'House', condominium: 'Condo', multifamily: 'Multi-family', land: 'Land' };

// ---------- Website sign-up ----------
function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.botcheck) return json_({ ok: true });          // spam trap
  if (p.action === 'save') { try { saveHomes_(p.id, String(p.mlsId || '').split(','), p.on !== '0'); } catch (err) { console.error('save failed', err); } return json_({ ok: true }); }
  if (p.action === 'view') { try { handleView_(p); } catch (err) { console.error('view failed', err); } return json_({ ok: true }); }
  const a = {
    name: clean_(p.name, 100),
    email: clean_(p.email, 120).toLowerCase(),
    phone: clean_(p.phone, 40),
    q: clean_(p.q, 80),
    minprice: digits_(p.minprice), maxprice: digits_(p.maxprice),
    minbeds: digits_(p.minbeds), minbaths: digits_(p.minbaths),
    type: TYPES[p.type] ? p.type : '',
    points: cleanPoints_(p.points),
    freq: /week/i.test(p.freq) ? 'Weekly' : 'Daily',
    lang: /^es/i.test(p.lang || '') ? 'Español' : 'English',
    source: clean_(p.source, 200),
    consent: p.consent === 'yes',
  };
  if (!a.name || !validEmail_(a.email) || !a.consent) return json_({ ok: false, error: 'missing fields' });
  if (!underDailyLimit_()) return json_({ ok: false, error: 'busy' });

  const lock = LockService.getScriptLock();
  lock.tryLock(10000);
  let id;
  try {
    const sh = sheet_();
    ensureHeaders_(sh);
    id = UUID_RE.test(p.id || '') && !findRow_(sh, p.id) ? String(p.id).toLowerCase() : Utilities.getUuid();
    sh.appendRow([new Date(), a.name, a.email, a.phone ? "'" + a.phone : '', a.q, a.minprice, a.maxprice, a.minbeds, a.minbaths,
                  a.type ? TYPES[a.type] : '', a.points, a.freq, a.lang, 'Active', new Date(), 0, a.source, '', id, 'Yes', 0, '']);
  } finally {
    lock.releaseLock();
  }
  let homes = [];
  try { homes = search_(a, null).slice(0, 6); } catch (err) { console.error('search failed', err); }
  try { changes_(a, id, new Date()); } catch (err) { console.error('snapshot failed', err); }
  if (p.saved) { try { saveHomes_(id, String(p.saved).split(','), true); } catch (err) { console.error('saved homes failed', err); } }
  try { pushOwner_(a); } catch (err) { console.error('phone alert failed', err); }
  try { notifyOwner_(a); } catch (err) { console.error('owner alert failed', err); }
  try { sendEmail_(a, id, homes, true); } catch (err) { console.error('welcome failed', err); }
  return json_({ ok: true });
}

// Unsubscribe link: ...exec?unsub=<ID>
function doGet(e) {
  const id = e && e.parameter && e.parameter.unsub;
  if (!id) return json_({ ok: true, service: '605homesearch listing alerts' });
  const sh = sheet_(), rows = sh.getDataRange().getValues();
  let es = false, found = false;
  for (let i = 1; i < rows.length; i++) {
    if (String(rows[i][C.ID]) === String(id)) {
      sh.getRange(i + 1, C.Status + 1).setValue('Unsubscribed');
      es = rows[i][C.Language] === 'Español'; found = true;
    }
  }
  const msg = !found ? 'This link is no longer active.' :
    es ? 'Listo. Ya no recibirá alertas de casas nuevas. Si cambia de opinión, llámeme o envíeme un texto al ' + PHONE + '.'
       : 'Done. You won’t get any more new listing alerts. If you change your mind, call or text me at ' + PHONE + '.';
  return HtmlService.createHtmlOutput('<div style="font-family:Arial,sans-serif;max-width:520px;margin:60px auto;padding:0 20px;color:#1a2237;font-size:17px;line-height:1.6"><h2 style="color:#13203b">Marcos Diaz · 605homesearch.com</h2><p>' + msg + '</p></div>')
    .setTitle('Listing alerts');
}

// ---------- Daily check (8 AM) ----------
function sendAlerts() {
  const sh = sheet_(), rows = sh.getDataRange().getValues();
  const now = new Date();
  const oh = openHouses_();
  let sent = 0;
  for (let i = 1; i < rows.length && sent < MAX_EMAILS_PER_RUN; i++) {
    const r = rows[i];
    if (String(r[C.Status]).trim() !== 'Active' || !validEmail_(String(r[C.Email]))) continue;
    const last = r[C['Last sent']] instanceof Date ? r[C['Last sent']] : new Date(now.getTime() - 86400000);
    const weekly = /week/i.test(String(r[C['How often']]));
    if (weekly && now - last < 6.5 * 86400000) continue;
    const a = rowToSearch_(r);
    let homes, saved = [];
    try { homes = changes_(a, String(r[C.ID]), last); } catch (err) { console.error('search failed for row ' + (i + 1), err); continue; }
    try { saved = savedChanges_(String(r[C.ID]).toLowerCase(), oh); } catch (err) { console.error('saved homes failed for row ' + (i + 1), err); }
    const seen = {}; saved.forEach(function (h) { seen[h.mlsId] = 1; });
    homes = saved.concat(homes.filter(function (h) { return !seen[h.mlsId]; }));
    if (!homes.length) continue;
    homes.forEach(function (h) { seen[h.mlsId] = 1; if (!h._oh && oh[h.mlsId]) h._oh = oh[h.mlsId][0]; });
    const recs = ((changesAll_ || []).filter(function (h) { return !seen[h.mlsId]; })).slice(0, 3);
    try {
      sendEmail_(a, r[C.ID], homes.slice(0, MAX_HOMES_PER_EMAIL), false, homes.length, homes, recs);
      sh.getRange(i + 1, C['Last sent'] + 1, 1, 2).setValues([[now, (Number(r[C['Homes sent']]) || 0) + homes.length]]);
      sent++;
    } catch (err) { console.error('email failed for row ' + (i + 1), err); }
  }
  console.log('alert emails sent: ' + sent);
}

let changesAll_ = [];   // every home matching the last search checked (used for "Our recommendations for you")

// New listings, price drops and back-on-market homes for one person since their last email.
// Each home gets h._kind = 'new' | 'drop' | 'back' (and h._was = old price for drops).
function changes_(a, id, since) {
  const all = search_(a, null, 500);
  changesAll_ = all;
  const full = all.length < 500;                        // did we get every matching home?
  const key = criteriaKey_(a);
  const snap = getSnapshot_(id);
  const out = [];
  const prevKnown = snap && snap.key === key ? snap.data : null;   // search changed? start fresh, no drops/back
  all.forEach(function (h) {
    const t = new Date((h.mls && h.mls.originalEntryTimestamp) || h.listDate || 0);
    const was = prevKnown ? prevKnown[h.mlsId] : undefined;
    if (t > since) { h._kind = 'new'; out.push(h); return; }
    if (!prevKnown) return;
    if (was !== undefined && h.listPrice && was && h.listPrice < was) { h._kind = 'drop'; h._was = was; out.push(h); return; }
    if (was === undefined && full && prevKnown._full) {
      // wasn't a match last time: either its price came down into their range, or it came back on the market
      if (h.originalListPrice && h.listPrice && h.listPrice < h.originalListPrice) { h._kind = 'drop'; h._was = h.originalListPrice; }
      else h._kind = 'back';
      out.push(h);
    }
  });
  const data = {}; all.forEach(function (h) { data[h.mlsId] = h.listPrice || 0; }); data._full = full;
  saveSnapshot_(id, key, data);
  const order = { 'new': 0, drop: 1, back: 2 };
  return out.sort(function (x, y) { return order[x._kind] - order[y._kind]; });
}

function criteriaKey_(a) {
  return [a.q, a.minprice, a.maxprice, a.minbeds, a.minbaths, a.type, a.q ? '' : a.points].join('~');
}
function snapSheet_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName('Snapshots');
  if (!sh) { sh = ss.insertSheet('Snapshots'); sh.getRange(1, 1, 1, 4).setValues([['ID', 'Search', 'Homes', 'Updated']]); sh.hideSheet(); }
  return sh;
}
function getSnapshot_(id) {
  const sh = snapSheet_(), last = sh.getLastRow(); if (last < 2) return null;
  const rows = sh.getRange(2, 1, last - 1, 3).getValues();
  for (let i = 0; i < rows.length; i++) if (String(rows[i][0]) === id) {
    try { return { key: String(rows[i][1]), data: JSON.parse(rows[i][2]) }; } catch (e) { return null; }
  }
  return null;
}
function saveSnapshot_(id, key, data) {
  const sh = snapSheet_(), last = sh.getLastRow();
  let json = JSON.stringify(data);
  if (json.length > 49000) json = JSON.stringify({ _full: false });   // too big for one cell: skip drop/back for this person
  if (last >= 2) {
    const ids = sh.getRange(2, 1, last - 1, 1).getValues();
    for (let i = 0; i < ids.length; i++) if (String(ids[i][0]) === id) { sh.getRange(i + 2, 2, 1, 3).setValues([[key, json, new Date()]]); return; }
  }
  sh.appendRow([id, key, json, new Date()]);
}

// ---------- Learning from what they view ----------
function handleView_(p) {
  const id = String(p.id || '').toLowerCase(), mlsId = String(p.mlsId || '').replace(/[^0-9]/g, '').slice(0, 12);
  if (!UUID_RE.test(id) || !mlsId) return;
  const cache = CacheService.getScriptCache();
  const dayKey = 'v_' + id.slice(0, 8) + '_' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd');
  const today = Number(cache.get(dayKey) || 0);
  if (today >= 60) return;                               // safety limit per person per day
  cache.put(dayKey, String(today + 1), 21600);

  const lock = LockService.getScriptLock();
  lock.tryLock(10000);
  try {
    const sh = sheet_(); ensureHeaders_(sh);
    const rowNum = findRow_(sh, id); if (!rowNum) return;
    const r = sh.getRange(rowNum, 1, 1, HEADERS.length).getValues()[0];
    if (String(r[C.Status]).trim() !== 'Active') return;

    // look the home up on the MLS (don't trust details sent by the browser)
    const res = UrlFetchApp.fetch(LISTINGS_API + '/' + mlsId + '?include=compliance', { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return;
    const h = JSON.parse(res.getContentText()), hp = h.property || {}, ad = h.address || {};
    const baths = (hp.bathsFull || 0) + (hp.bathsHalf ? 0.5 * hp.bathsHalf : 0) || hp.bathrooms || '';
    const addr = h.internetAddressDisplay === false ? '' : cleanAddr_(ad.full);
    const act = activity_();
    const before = recentViews_(act, id);               // this person's views before this one
    act.appendRow([new Date(), r[C.Name], r[C.Email], h.listingId || mlsId, h.listPrice || '', hp.bedrooms || '', baths, ad.city || '', addr, id]);
    const views = (Number(r[C.Views]) || 0) + 1;
    sh.getRange(rowNum, C.Views + 1).setValue(views);

    const mine = myViews_(act, id);
    hotLead_(r, id, mlsId, mine, h, addr);
    try { browsingAlert_(r, id, before, h.listingId || mlsId, addr, (h.address || {}).city || ''); } catch (err) { console.error('browsing alert failed', err); }
    if (String(r[C['Auto-adjust']] || 'Yes').trim().toLowerCase() !== 'no' && mine.length >= 3) learn_(sh, rowNum, mine);
  } finally {
    lock.releaseLock();
  }
}

// last 12 homes this person viewed (newest first), one entry per home
function myViews_(act, id) {
  const last = act.getLastRow(); if (last < 2) return [];
  const start = Math.max(2, last - 3000);
  const rows = act.getRange(start, 1, last - start + 1, ACT_HEADERS.length).getValues();
  const seen = {}, out = [], counts = {};
  for (let i = rows.length - 1; i >= 0; i--) {
    const x = rows[i]; if (String(x[9]) !== id) continue;
    const k = String(x[3]); counts[k] = (counts[k] || 0) + 1;
    if (seen[k]) continue; seen[k] = true;
    if (out.length < 12) out.push({ mls: k, price: Number(x[4]) || 0, beds: Number(x[5]) || 0, city: String(x[7] || '') });
  }
  out.counts = counts;
  return out;
}

function learn_(sh, rowNum, v) {
  const prices = v.map(function (x) { return x.price; }).filter(Boolean).sort(function (a, b) { return a - b; });
  if (!prices.length) return;
  const lo = Math.max(0, Math.floor(prices[0] * 0.9 / 10000) * 10000);
  const hi = Math.ceil(prices[prices.length - 1] * 1.1 / 10000) * 10000;
  const beds = v.map(function (x) { return x.beds; }).filter(Boolean);
  const minBeds = beds.length ? Math.min(5, Math.min.apply(null, beds)) : '';
  const byCity = {}; v.forEach(function (x) { if (x.city) byCity[x.city] = (byCity[x.city] || 0) + 1; });
  const top = Object.keys(byCity).sort(function (a, b) { return byCity[b] - byCity[a]; })[0];
  const cityShare = top ? byCity[top] / v.length : 0;
  const cities = Object.keys(byCity);

  sh.getRange(rowNum, C['Min price'] + 1, 1, 3).setValues([[lo || '', hi, minBeds]]);
  if (cityShare >= 0.6) {
    sh.getRange(rowNum, C.Search + 1).setValue(top);
    sh.getRange(rowNum, C['Map area'] + 1).setValue('');
  } else if (cities.length > 1) {
    // looking in several towns: search the whole area they've been browsing, by price and beds
    sh.getRange(rowNum, C.Search + 1).setValue('');
  }
  const tz = Session.getScriptTimeZone();
  sh.getRange(rowNum, C.Learned + 1).setValue(Utilities.formatDate(new Date(), tz, 'MMM d') + ': from ' + v.length + ' homes viewed · ' +
    (cityShare >= 0.6 ? top : cities.join(', ')) + ' · ' + money_(lo) + '–' + money_(hi) + (minBeds ? ' · ' + minBeds + '+ beds' : ''));
}

function hotLead_(r, id, mlsId, mine, h, addr) {
  const listingId = String(h.listingId || mlsId);
  const n = (mine.counts && mine.counts[listingId]) || 0;
  if (n < 3) return;
  const props = PropertiesService.getScriptProperties(), key = 'hot_' + id.slice(0, 8) + '_' + listingId;
  if (props.getProperty(key)) return;
  props.setProperty(key, '1');
  const name = String(r[C.Name]), first = name.split(' ')[0];
  const tel = String(r[C.Phone] || '').replace(/[^0-9+]/g, '');
  const where = (addr ? addr + ', ' : '') + ((h.address || {}).city || '');
  const subject = '🔥 HOT LEAD: ' + name + ' keeps looking at ' + where;
  const html = '<div style="font-family:Arial,sans-serif;font-size:15px;color:#1a2237">' +
    '<h2 style="margin:0 0 12px;color:#13203b">' + esc_(name) + ' has opened this home ' + n + ' times</h2>' +
    '<p><b>' + esc_(money_(h.listPrice)) + '</b> · ' + esc_(where) + ' · MLS #' + esc_(listingId) + '<br>' +
    '<a href="' + SEARCH_PAGE + '#home=' + encodeURIComponent(mlsId) + '">See the home</a></p>' +
    '<p><b>Email:</b> ' + esc_(String(r[C.Email])) + '<br><b>Phone:</b> ' + (tel ? '<a href="tel:' + tel + '">' + esc_(String(r[C.Phone])) + '</a>' : '(not given)') + '</p>' +
    (tel ? '<p><a href="tel:' + tel + '" style="background:#b98b5c;color:#fff;padding:10px 18px;text-decoration:none">Call ' + esc_(first) + '</a> &nbsp; <a href="sms:' + tel + '" style="background:#13203b;color:#fff;padding:10px 18px;text-decoration:none">Text ' + esc_(first) + '</a></p>' : '') +
    '<p style="color:#8a8579;font-size:12px">From your Listing Alert Leads sheet (Activity tab): ' + SpreadsheetApp.getActive().getUrl() + '</p></div>';
  GmailApp.sendEmail(OWNER_EMAIL, subject, subject, { htmlBody: html, name: '605homesearch Alerts' });
  try { pushHot_(name, n, where, h, mlsId, tel, String(r[C.Email])); } catch (err) { console.error('hot phone alert failed', err); }
}

// 🔥 alert on Marcos's phone (ntfy app) with buttons to call/text them or open the home
function pushHot_(name, n, where, h, mlsId, tel, email) {
  if (!NTFY_TOPIC) return;
  const home = SEARCH_PAGE + '#home=' + encodeURIComponent(mlsId);
  const actions = [];
  if (tel) actions.push({ action: 'view', label: 'Call', url: 'tel:' + tel, clear: false });
  if (tel) actions.push({ action: 'view', label: 'Text', url: 'sms:' + tel, clear: false });
  actions.push({ action: 'view', label: 'See home', url: home, clear: false });
  UrlFetchApp.fetch('https://ntfy.sh', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    payload: JSON.stringify({
      topic: NTFY_TOPIC, priority: 5, tags: ['fire'],
      title: 'Hot lead: ' + name + ' opened a home ' + n + ' times',
      message: [money_(h.listPrice) + ' · ' + where, tel ? 'Phone: ' + tel : '', email ? 'Email: ' + email : ''].filter(String).join('\n'),
      click: tel ? 'tel:' + tel : home,
      actions: actions,
    }),
  });
}

function activity_() {
  const ss = SpreadsheetApp.getActive();
  let act = ss.getSheetByName('Activity');
  if (!act) {
    act = ss.insertSheet('Activity');
    act.getRange(1, 1, 1, ACT_HEADERS.length).setValues([ACT_HEADERS]).setFontWeight('bold').setBackground('#13203b').setFontColor('#ffffff');
    act.setFrozenRows(1); act.hideColumns(ACT_HEADERS.length);
  }
  return act;
}

function findRow_(sh, id) {
  const last = sh.getLastRow(); if (last < 2) return 0;
  const ids = sh.getRange(2, C.ID + 1, last - 1, 1).getValues();
  for (let i = 0; i < ids.length; i++) if (String(ids[i][0]).toLowerCase() === String(id).toLowerCase()) return i + 2;
  return 0;
}

function ensureHeaders_(sh) {
  const cur = sh.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  if (cur.join('|') === HEADERS.join('|')) return;
  sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold').setBackground('#13203b').setFontColor('#ffffff');
}

// ---------- Listing search ----------
function search_(a, since, limit) {
  const q = [];
  const add = function (k, v) { if (v !== '' && v != null) q.push(k + '=' + encodeURIComponent(v)); };
  add('q', a.q); add('minprice', a.minprice); add('maxprice', a.maxprice);
  add('minbeds', a.minbeds); add('minbaths', a.minbaths); add('type', a.type);
  if (a.type === 'residential') add('subtype', 'SingleFamilyResidence');  // "House" = single-family only (RASE files townhomes as residential too)
  if (!a.q && a.points) a.points.split('|').forEach(function (pt) { add('points', pt); });
  add('status', 'Active'); add('sort', '-listdate'); add('limit', limit || 50); add('include', 'compliance');
  const res = UrlFetchApp.fetch(LISTINGS_API + '?' + q.join('&'), { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) throw new Error('listings ' + res.getResponseCode());
  return JSON.parse(res.getContentText()).filter(function (h) {
    if (h.internetEntireListingDisplay === false) return false;
    if (!since) return true;
    const t = new Date((h.mls && h.mls.originalEntryTimestamp) || h.listDate || 0);
    return t > since;
  });
}

function rowToSearch_(r) {
  const typeKey = Object.keys(TYPES).filter(function (k) { return TYPES[k] === r[C.Type]; })[0] || '';
  return { id: String(r[C.ID]), name: String(r[C.Name]), email: String(r[C.Email]), q: String(r[C.Search] || ''), minprice: r[C['Min price']], maxprice: r[C['Max price']],
           minbeds: r[C.Beds], minbaths: r[C.Baths], type: typeKey, points: String(r[C['Map area']] || ''),
           freq: String(r[C['How often']]), lang: r[C.Language] === 'Español' ? 'Español' : 'English' };
}

function describe_(a, es) {
  const bits = [];
  bits.push(a.q ? a.q : (a.points ? (es ? 'el área del mapa que escogió' : 'the map area you picked') : 'Sioux Falls area'));
  if (a.minprice && a.maxprice) bits.push(money_(a.minprice) + '–' + money_(a.maxprice));
  else if (a.maxprice) bits.push((es ? 'hasta ' : 'up to ') + money_(a.maxprice));
  else if (a.minprice) bits.push(money_(a.minprice) + '+');
  if (a.minbeds) bits.push(a.minbeds + '+ ' + (es ? 'recámaras' : 'beds'));
  if (a.minbaths) bits.push(a.minbaths + '+ ' + (es ? 'baños' : 'baths'));
  if (a.type) bits.push(TYPES[a.type]);
  return bits.join(' · ');
}

// ---------- Emails ----------
function pushOwner_(a) {
  if (!NTFY_TOPIC) return;
  const tel = (a.phone || '').replace(/[^0-9+]/g, '');
  const actions = [];
  if (tel) actions.push({ action: 'view', label: 'Call', url: 'tel:' + tel, clear: false });
  if (tel) actions.push({ action: 'view', label: 'Text', url: 'sms:' + tel, clear: false });
  actions.push({ action: 'view', label: 'Email', url: 'mailto:' + a.email, clear: false });
  UrlFetchApp.fetch('https://ntfy.sh', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    payload: JSON.stringify({
      topic: NTFY_TOPIC, priority: 4, tags: ['bell'],
      title: 'Alert sign-up: ' + a.name + (a.lang === 'Español' ? ' (Español)' : ''),
      message: [describe_(a, false), a.freq + ' emails', a.phone, a.email].filter(String).join('\n'),
      click: tel ? 'tel:' + tel : 'mailto:' + a.email,
      actions: actions,
    }),
  });
}

function notifyOwner_(a) {
  const first = a.name.split(' ')[0];
  const subject = '🔔 NEW ALERT LEAD: ' + a.name + ' – ' + describe_(a, false);
  const tel = (a.phone || '').replace(/[^0-9+]/g, '');
  const html = '<div style="font-family:Arial,sans-serif;font-size:15px;color:#1a2237">' +
    '<h2 style="margin:0 0 12px;color:#13203b">New listing alert sign-up' + (a.lang === 'Español' ? ' (Español)' : '') + '</h2>' +
    '<p><b>Name:</b> ' + esc_(a.name) + '<br><b>Email:</b> <a href="mailto:' + esc_(a.email) + '">' + esc_(a.email) + '</a><br>' +
    '<b>Phone:</b> ' + (tel ? '<a href="tel:' + tel + '">' + esc_(a.phone) + '</a>' : '(not given)') + '<br>' +
    '<b>Looking for:</b> ' + esc_(describe_(a, false)) + '<br><b>Emails:</b> ' + a.freq + '</p>' +
    (tel ? '<p><a href="tel:' + tel + '" style="background:#b98b5c;color:#fff;padding:10px 18px;text-decoration:none">Call ' + esc_(first) + '</a> &nbsp; <a href="sms:' + tel + '" style="background:#13203b;color:#fff;padding:10px 18px;text-decoration:none">Text ' + esc_(first) + '</a></p>' : '') +
    '<p style="color:#8a8579;font-size:12px">Saved to your Listing Alert Leads sheet: ' + SpreadsheetApp.getActive().getUrl() + '</p></div>';
  GmailApp.sendEmail(OWNER_EMAIL, subject, subject, { htmlBody: html, name: '605homesearch Alerts' });
}

// ---------- Alert emails (laid out like Zillow's, in Marcos's navy + copper) ----------
const NAVY = '#13203b', COPPER = '#8a6236', INK = '#111827', GRAY = '#4b5563', LINE = '#d1d5db';

// a = the person's search, homes = cards to show, welcome = first email after sign-up,
// total = how many changes in all, allHomes = every change (for the subject), recs = "Our recommendations for you"
function sendEmail_(a, id, homes, welcome, total, allHomes, recs) {
  const es = a.lang === 'Español';
  const t = function (en, sp) { return es ? sp : en; };
  const first = a.name.split(' ')[0];
  const unsub = WEBAPP_URL + '?unsub=' + encodeURIComponent(id);
  const page = (es ? SEARCH_PAGE_ES : SEARCH_PAGE) + '?a=' + encodeURIComponent(id);
  const what = describe_(a, es);
  const list = allHomes || homes;
  const searchLink = '<a href="' + page + '" style="color:' + NAVY + ';text-decoration:underline">' + t('My Saved Search', 'Mi búsqueda guardada') + '</a>';
  const matchLine = t('This home matches your search ', 'Esta casa coincide con su búsqueda ') + searchLink + ': ' + esc_(what) + '.';
  let subject, headline, sub;

  if (welcome) {
    subject = t('Your home alerts are set up, ', 'Sus alertas de casas están listas, ') + first;
    headline = t('You’re all set, ', 'Listo, ') + esc_(first);
    sub = t('I’ll email you as soon as new homes hit the market that match your search ', 'Le enviaré un correo apenas salgan casas nuevas que coincidan con su búsqueda ') + searchLink + ': ' + esc_(what) + '.' +
      (homes.length ? ' ' + t('Here’s what’s for sale right now:', 'Estas están en venta ahora mismo:') : '');
  } else if (list.length === 1) {
    const h = list[0], ad = h.address || {}, street = h.internetAddressDisplay === false ? '' : cleanAddr_(ad.full);
    const place = [street, ad.city].filter(Boolean).join(', ');
    const town = (ad.city || '') + ', SD' + (ad.postalCode ? ' ' + ad.postalCode : '');
    const saved = h._saved;
    const k = h._kind || 'new';
    if (k === 'new') {
      subject = shortMoney_(h.listPrice) + t(' home just listed in ', ' casa nueva en ') + town;
      headline = t('New listing for sale at ', 'Casa nueva en venta por ') + money_(h.listPrice);
      sub = matchLine;
    } else if (k === 'drop') {
      subject = t('Price cut: ', 'Bajó de precio: ') + place + t(' is now ', ' ahora cuesta ') + money_(h.listPrice);
      headline = saved ? t('Price cut on a home you saved', 'Bajó el precio de una casa que guardó') : t('Price cut on a home that matches your search', 'Bajó el precio de una casa de su búsqueda');
      sub = saved ? t('Good news. The price just dropped on a home you’re watching.', 'Buenas noticias. Bajó el precio de una casa que usted sigue.') : matchLine;
    } else if (k === 'back') {
      subject = t('Back on the market: ', 'De vuelta en el mercado: ') + place;
      headline = saved ? t('A home you saved is back on the market', 'Una casa que guardó está en venta otra vez') : t('Back on the market and matches your search', 'De vuelta en el mercado y coincide con su búsqueda');
      sub = t('This home was off the market and is for sale again. It may not last long.', 'Esta casa salió del mercado y ahora está en venta otra vez. Puede venderse pronto.');
    } else if (k === 'oh') {
      subject = t('Open house ', 'Casa abierta ') + ohDay_(h._oh, es) + ': ' + place;
      headline = t('Open house at a home you saved', 'Casa abierta en una casa que guardó');
      sub = t('Come see it in person. No appointment needed.', 'Venga a verla en persona. No necesita cita.');
    } else if (k === 'pending') {
      subject = t('Update: ', 'Novedad: ') + place + t(' is now pending', ' ya está en contrato');
      headline = t('A home you saved is now pending', 'Una casa que guardó ya está en contrato');
      sub = t('This home is under contract. Pending homes sometimes come back on the market, and I’ll let you know if it does.', 'Esta casa ya tiene una oferta aceptada. A veces vuelven al mercado, y le aviso si pasa.');
    } else {
      subject = t('Update: ', 'Novedad: ') + place + t(' has sold', ' se vendió');
      headline = t('A home you saved has sold', 'Una casa que guardó se vendió');
      sub = t('This one is off the market. Let’s find the next one. Here are similar homes for sale.', 'Esta casa ya se vendió. Busquemos la próxima. Aquí hay casas parecidas en venta.');
    }
  } else {
    const allNew = list.every(function (h) { return (h._kind || 'new') === 'new'; });
    const prices = list.map(function (h) { return h.listPrice || 0; }).filter(Boolean);
    const area = a.q || t('your area', 'su área');
    if (allNew) {
      subject = list.length + t(' new homes for you in ', ' casas nuevas para usted en ') + area + (prices.length ? t(', starting at ', ', desde ') + shortMoney_(Math.min.apply(null, prices)) : '');
      headline = list.length + t(' new listings match your search', ' casas nuevas coinciden con su búsqueda');
    } else {
      subject = summary_(list, es) + ': ' + what;
      headline = t('Updates on homes for you', 'Novedades de casas para usted');
    }
    sub = t('These homes match your search ', 'Estas casas coinciden con su búsqueda ') + searchLink + ': ' + esc_(what) + '.' +
      (list.some(function (h) { return h._saved; }) ? ' ' + t('Plus updates on homes you saved.', 'Y novedades de las casas que guardó.') : '');
  }

  const cards = homes.map(function (h) { return card_(h, es, id); }).join('');
  const more = total && total > homes.length ? ' ' + t('(' + (total - homes.length) + ' more on the site)', '(' + (total - homes.length) + ' más en el sitio)') : '';
  const recHtml = recs && recs.length ? recs_(recs, es, id, list.some(function (h) { return h._kind === 'sold' || h._kind === 'pending'; })) : '';
  const call = list.some(function (h) { return h._kind === 'oh'; }) ? t('Can’t make it? Text or call me for a private showing.', '¿No puede ir? Llámeme o mándeme un texto para verla en privado.')
    : list.some(function (h) { return h._kind === 'sold' || h._kind === 'pending'; }) ? t('Missed this one? Let’s find the next one. Text or call me.', '¿Se le fue esta? Busquemos la próxima. Llámeme o mándeme un texto.')
    : t('Want to see one? Text or call me.', '¿Quiere ver alguna? Llámeme o mándeme un texto.');

  const html =
    '<div style="background:#f3f4f6;padding:16px 0">' +
    '<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;background:#ffffff;color:' + INK + ';font-size:16px;line-height:1.5">' +
    // logo
    '<table cellpadding="0" cellspacing="0" style="margin:0 28px;padding-top:22px"><tr>' +
    '<td style="width:42px;vertical-align:middle">' + mono_(38, 15) + '</td>' +
    '<td style="padding-left:10px;font-family:Georgia,serif;font-size:22px;font-weight:bold;color:' + NAVY + '">Marcos Díaz</td></tr></table>' +
    // headline
    '<div style="padding:22px 28px 0">' +
    '<h1 style="margin:0 0 10px;font-size:26px;line-height:1.2;font-weight:800;color:' + INK + '">' + headline + '</h1>' +
    '<p style="margin:0">' + sub + more + '</p></div>' +
    '<div style="padding:4px 28px 0">' + cards + '</div>' +
    // search button
    '<div style="padding:18px 28px 0">' + button_(page, t('See latest search results', 'Ver los resultados más nuevos'), false) + '</div>' +
    recHtml +
    // contact
    '<table cellpadding="0" cellspacing="0" width="100%" style="margin-top:32px;border-top:1px solid #e5e7eb"><tr><td style="padding:22px 28px">' +
    '<table cellpadding="0" cellspacing="0"><tr>' +
    '<td style="width:50px;vertical-align:middle">' + mono_(46, 17) + '</td>' +
    '<td style="padding-left:14px;font-size:14px;line-height:1.5"><b style="font-size:16px">' + call + '</b><br>' +
    '<span style="color:' + GRAY + '">Marcos Díaz · Broker Associate · REALTOR® · Keller Williams Realty Sioux Falls</span><br>' +
    '<a href="tel:+16058389140" style="color:' + NAVY + ';font-weight:bold;text-decoration:none">' + PHONE + '</a> · ' +
    '<a href="mailto:' + OWNER_EMAIL + '" style="color:' + NAVY + ';font-weight:bold;text-decoration:none">' + OWNER_EMAIL + '</a></td></tr></table>' +
    '</td></tr></table>' +
    // fine print
    '<div style="background:#f9fafb;padding:16px 28px 22px;font-size:11px;color:' + GRAY + ';line-height:1.5">' +
    t('You’re getting this because you asked for home alerts on 605homesearch.com. Your alerts adjust to the homes you open and save. ', 'Recibe este correo porque pidió alertas de casas en 605homesearch.com. Sus alertas se ajustan según las casas que abre y guarda. ') +
    '<a href="' + page + '" style="color:' + GRAY + '">' + t('Edit my search', 'Cambiar mi búsqueda') + '</a> · ' +
    '<a href="' + unsub + '" style="color:' + GRAY + '">' + t('Unsubscribe', 'Cancelar alertas') + '</a><br>' +
    t('Listing information is deemed reliable but not guaranteed and should be independently verified. ', 'La información de las casas se considera confiable pero no está garantizada y debe verificarse. ') +
    t('Listings are courtesy of the listing brokerage named on each listing. ', 'Las casas son cortesía de la correduría indicada en cada una. ') +
    'Listing data provided by the REALTOR® Association of the Sioux Empire MLS.<br>' +
    'Marcos Diaz, Broker Associate · ' + OFFICE + '. Each office is independently owned and operated. Equal Housing Opportunity.</div>' +
    '</div></div>';
  GmailApp.sendEmail(a.email, subject, t('Open this email in HTML to see the homes. Unsubscribe: ', 'Abra este correo en HTML para ver las casas. Cancelar: ') + unsub,
    { htmlBody: html, name: OWNER_NAME, replyTo: OWNER_EMAIL });
}

// MD monogram circle (fixed size so it stays round in every email app)
function mono_(size, font) {
  return '<div style="width:' + size + 'px;height:' + size + 'px;line-height:' + size + 'px;border-radius:50%;background:' + NAVY + ';border:2px solid #b98b5c;text-align:center;color:#e7b98a;font-family:Georgia,serif;font-weight:bold;font-size:' + font + 'px">MD</div>';
}

function button_(href, label, full) {
  return '<table cellpadding="0" cellspacing="0"' + (full ? ' width="100%"' : '') + '><tr><td style="background:' + NAVY + ';border-radius:8px;text-align:center">' +
    '<a href="' + href + '" style="display:block;padding:' + (full ? '13px 0' : '12px 18px') + ';color:#ffffff;text-decoration:none;font-weight:bold;font-size:' + (full ? '17' : '16') + 'px">' + label + '</a></td></tr></table>';
}

function pill_(label, solid, dot) {
  return solid
    ? '<span style="display:inline-block;background:' + COPPER + ';color:#ffffff;font-size:12px;font-weight:bold;padding:3px 9px;border-radius:6px;margin:0 6px 6px 0">' + label + '</span>'
    : '<span style="display:inline-block;background:#ffffff;border:1px solid ' + LINE + ';color:' + INK + ';font-size:12px;font-weight:bold;padding:2px 9px;border-radius:6px;margin:0 6px 6px 0"><span style="color:' + (dot || COPPER) + '">●</span> ' + label + '</span>';
}

function homeLink_(h, es, id) {
  return (es ? SEARCH_PAGE_ES : SEARCH_PAGE) + (id ? '?a=' + encodeURIComponent(id) : '') + '#home=' + h.mlsId;
}
function bathsOf_(p) { return (p.bathsFull || 0) + (p.bathsHalf ? 0.5 * p.bathsHalf : 0) || p.bathrooms || ''; }

function card_(h, es, id) {
  const t = function (en, sp) { return es ? sp : en; };
  const p = h.property || {}, ad = h.address || {}, ag = h.agent || {}, of = h.office || {};
  const street = h.internetAddressDisplay === false ? '' : cleanAddr_(ad.full);
  const photo = h.photos && h.photos[0];
  const link = homeLink_(h, es, id);
  const k = h._kind || 'new';
  const off = k === 'pending' || k === 'sold';
  const contact = (h.compliance && h.compliance.attributionContact) || (of.contact && (of.contact.office || of.contact.email)) || '';
  const agent = [ag.firstName, ag.lastName].filter(Boolean).join(' ');
  const courtesy = (of.name ? esc_(of.name) : '') + (agent ? ' · ' + esc_(agent) : '') + (contact ? ' · ' + esc_(contact) : '');

  let pills = off ? pill_(k === 'sold' ? t('Sold', 'Vendida') : t('Pending', 'En contrato'), false, GRAY) : pill_(t('For sale', 'En venta'), false);
  if (k === 'new') pills += pill_(t('New', 'Nueva'), true);
  if (k === 'drop') pills += pill_(t('Price cut', 'Bajó de precio'), true);
  if (k === 'back') pills += pill_(t('Back on market', 'De vuelta'), true);
  if (h._oh && !off) pills += pill_(t('Open house', 'Casa abierta'), true);
  if (h._saved) pills += pill_(t('Saved', 'Guardada'), false, '#b91c1c');

  let price = '<div style="font-size:26px;font-weight:800;color:' + INK + '">' + money_(h.listPrice) +
    (k === 'drop' && h._was ? ' <span style="font-size:16px;font-weight:normal;color:' + GRAY + ';text-decoration:line-through">' + money_(h._was) + '</span>' : '') + '</div>';
  if (k === 'drop' && h._was) price += '<div style="font-size:14px;font-weight:bold;color:' + COPPER + '">' + t('Down ', 'Bajó ') + money_(h._was - h.listPrice) + '</div>';

  const stats = '<b>' + (p.bedrooms || 0) + '</b> ' + t('bd', 'rec') + ' &nbsp;|&nbsp; <b>' + bathsOf_(p) + '</b> ' + t('ba', 'baños') +
    (p.area ? ' &nbsp;|&nbsp; <b>' + Number(p.area).toLocaleString('en-US') + '</b> ' + t('sqft', 'pies²') : '');
  const oh = h._oh && !off ? '<div style="margin-top:10px;background:#f4ebe2;border-radius:8px;padding:9px 12px;font-size:15px;color:#7a4a1e"><b>' + t('Open house: ', 'Casa abierta: ') + '</b>' + esc_(ohWhen_(h._oh, es)) + '</div>' : '';

  return '<table cellpadding="0" cellspacing="0" width="100%" style="border:1px solid ' + LINE + ';border-radius:10px;margin:18px 0 0;border-collapse:separate;overflow:hidden"><tr><td>' +
    (photo ? '<a href="' + link + '"><img src="' + esc_(photo) + '" width="544" style="display:block;width:100%;height:auto;border:0;border-radius:10px 10px 0 0" alt=""></a>' : '') +
    '<div style="padding:14px 16px 16px">' + pills + price +
    '<div style="font-size:15px">' + stats + '</div>' +
    '<div style="font-size:15px">' + esc_([street, ad.city].filter(Boolean).join(', ')) + ', SD</div>' + oh +
    (courtesy ? '<div style="font-size:13px;color:' + GRAY + ';padding-top:6px">' + t('Listing courtesy of ', 'Cortesía de ') + courtesy + '</div>' : '') +
    '<div style="padding-top:14px">' + button_(link, off ? t('See home details', 'Ver detalles') : t('Explore this home', 'Ver esta casa'), true) + '</div>' +
    '</div></td></tr></table>';
}

function recs_(homes, es, id, similar) {
  const t = function (en, sp) { return es ? sp : en; };
  const cells = homes.slice(0, 3).map(function (h) {
    const p = h.property || {}, ad = h.address || {}, photo = h.photos && h.photos[0], link = homeLink_(h, es, id);
    return '<td width="33%" style="vertical-align:top;padding:0 5px">' +
      '<table cellpadding="0" cellspacing="0" width="100%" style="border:1px solid ' + LINE + ';border-radius:10px;border-collapse:separate;overflow:hidden"><tr><td>' +
      (photo ? '<a href="' + link + '"><img src="' + esc_(photo) + '" width="170" style="display:block;width:100%;height:auto;border:0;border-radius:10px 10px 0 0" alt=""></a>' : '') +
      '<div style="padding:8px 10px;font-size:12px;line-height:1.45"><a href="' + link + '" style="color:' + INK + ';text-decoration:none"><b style="font-size:16px">' + money_(h.listPrice) + '</b></a><br>' +
      '<b>' + (p.bedrooms || 0) + '</b> ' + t('bd', 'rec') + ' | <b>' + bathsOf_(p) + '</b> ' + t('ba', 'baños') + '<br>' +
      '<span style="color:' + GRAY + '">' + esc_(ad.city || '') + '</span></div></td></tr></table></td>';
  }).join('');
  return '<div style="padding:34px 28px 0">' +
    '<h2 style="margin:0;font-size:22px;font-weight:800;color:' + INK + '">' + (similar ? t('Similar homes for sale', 'Casas parecidas en venta') : t('Our recommendations for you', 'Le recomendamos estas casas')) + '</h2>' +
    '<p style="margin:2px 0 14px">' + t('Based on your recent activity', 'Según lo que ha visto') + '</p>' +
    '<table cellpadding="0" cellspacing="0" width="100%" style="margin:0 -5px"><tr>' + cells + '</tr></table></div>';
}

function summary_(homes, es) {
  const c = { 'new': 0, drop: 0, back: 0, oh: 0, pending: 0, sold: 0 };
  homes.forEach(function (h) { c[h._kind || 'new']++; });
  const bits = [];
  const add = function (n, en1, enN, es1, esN) { if (n) bits.push(n + ' ' + (es ? (n === 1 ? es1 : esN) : (n === 1 ? en1 : enN))); };
  add(c['new'], 'new home', 'new homes', 'casa nueva', 'casas nuevas');
  add(c.drop, 'price cut', 'price cuts', 'bajó de precio', 'bajaron de precio');
  add(c.back, 'back on the market', 'back on the market', 'de vuelta en el mercado', 'de vuelta en el mercado');
  add(c.oh, 'open house', 'open houses', 'casa abierta', 'casas abiertas');
  add(c.pending, 'now pending', 'now pending', 'en contrato', 'en contrato');
  add(c.sold, 'sold', 'sold', 'vendida', 'vendidas');
  return bits.join(', ');
}

function shortMoney_(n) {
  n = Number(n) || 0;
  if (n >= 1e6) return '$' + (n / 1e6).toFixed(2).replace(/\.?0+$/, '') + 'M';
  return '$' + Math.round(n / 1000) + 'K';
}

const DAYS_ES = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'], MONTHS_ES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
function ohDay_(o, es) {
  const d = new Date(o.start), tz = 'America/Chicago';
  if (!es) return Utilities.formatDate(d, tz, 'EEE, MMM d');
  return DAYS_ES[Number(Utilities.formatDate(d, tz, 'u')) % 7] + ' ' + Utilities.formatDate(d, tz, 'd') + ' ' + MONTHS_ES[Number(Utilities.formatDate(d, tz, 'M')) - 1];
}
function ohWhen_(o, es) {
  const tz = 'America/Chicago';
  const tm = function (d) { return Utilities.formatDate(new Date(d), tz, 'h:mm a').replace(':00', ''); };
  return ohDay_(o, es) + ' · ' + tm(o.start) + (o.end ? ' – ' + tm(o.end) : '');
}

// ---------- Saved homes (the ♥ on the website) ----------
const SAVED_HEADERS = ['ID', 'MLS ID', 'Saved on', 'Price', 'Status', 'Open house told'];
function savedSheet_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName('Saved homes');
  if (!sh) {
    sh = ss.insertSheet('Saved homes');
    sh.getRange(1, 1, 1, SAVED_HEADERS.length).setValues([SAVED_HEADERS]).setFontWeight('bold').setBackground('#13203b').setFontColor('#ffffff');
    sh.setFrozenRows(1);
  }
  return sh;
}

// The website sends action=save when a signed-up person taps ♥ (on=1) or un-saves (on=0)
function saveHomes_(id, ids, on) {
  id = String(id || '').toLowerCase();
  ids = ids.map(function (x) { return String(x).replace(/[^0-9]/g, '').slice(0, 12); }).filter(String).slice(0, 40);
  if (!UUID_RE.test(id) || !ids.length) return;
  const lock = LockService.getScriptLock();
  lock.tryLock(10000);
  try {
    if (!findRow_(sheet_(), id)) return;                 // only for people signed up for alerts
    const sh = savedSheet_(), last = sh.getLastRow();
    const rows = last >= 2 ? sh.getRange(2, 1, last - 1, 2).getValues() : [];
    if (on) {
      const have = {}; rows.forEach(function (r) { if (String(r[0]) === id) have[String(r[1])] = 1; });
      if (rows.filter(function (r) { return String(r[0]) === id; }).length >= 60) return;
      let added = 0;
      ids.forEach(function (m) { if (!have[m]) { sh.appendRow([id, m, new Date(), '', '', '']); have[m] = 1; added++; } });
      if (added) { try { savedAlert_(id, added); } catch (err) { console.error('saved alert failed', err); } }
    } else {
      for (let i = rows.length - 1; i >= 0; i--) if (String(rows[i][0]) === id && ids.indexOf(String(rows[i][1])) > -1) sh.deleteRow(i + 2);
    }
  } finally {
    lock.releaseLock();
  }
}

// ---------- "They're browsing a lot – call them" alerts ----------
// Sends Marcos an email + phone alert (ntfy) when a signed-up person:
//   • opens BROWSE_HOMES or more different homes within BROWSE_HOURS hours (at most once every 3 days per person)
//   • comes back and opens a home after QUIET_DAYS+ days without looking (at most once every 3 days per person)
//   • saves (♥) a home (at most once a day per person)
const BROWSE_HOMES = 6;
const BROWSE_HOURS = 24;
const QUIET_DAYS = 14;

// This person's views (newest first) from the Activity tab: [{ when: Date, mls: '...' }]
function recentViews_(act, id) {
  const last = act.getLastRow(); if (last < 2) return [];
  const start = Math.max(2, last - 3000);
  const rows = act.getRange(start, 1, last - start + 1, ACT_HEADERS.length).getValues();
  const out = [];
  for (let i = rows.length - 1; i >= 0; i--) {
    if (String(rows[i][9]) !== id) continue;
    const d = rows[i][0] instanceof Date ? rows[i][0] : new Date(rows[i][0]);
    if (!isNaN(d)) out.push({ when: d, mls: String(rows[i][3]) });
  }
  return out;
}

function browsingAlert_(r, id, before, listingId, addr, city) {
  const now = new Date(), props = PropertiesService.getScriptProperties();
  const coolKey = 'browse_' + id.slice(0, 8), cool = Number(props.getProperty(coolKey) || 0);
  if (now.getTime() - cool < 3 * 86400000) return;      // already told Marcos in the last 3 days

  const lastSeen = before.length ? before[0].when : null;
  if (lastSeen && now - lastSeen >= QUIET_DAYS * 86400000) {
    const days = Math.round((now - lastSeen) / 86400000);
    props.setProperty(coolKey, String(now.getTime()));
    activityNotice_(r, 'is back looking at homes after ' + days + ' days',
      'Just opened ' + ((addr ? addr + ', ' : '') + city || 'a home') + ' (MLS #' + listingId + ').', listingId);
    return;
  }

  const since = now.getTime() - BROWSE_HOURS * 3600000, homes = {};
  homes[String(listingId)] = 1;
  before.forEach(function (v) { if (v.when.getTime() >= since) homes[v.mls] = 1; });
  const n = Object.keys(homes).length;
  if (n >= BROWSE_HOMES) {
    props.setProperty(coolKey, String(now.getTime()));
    activityNotice_(r, 'opened ' + n + ' different homes in the last ' + BROWSE_HOURS + ' hours',
      'Latest: ' + ((addr ? addr + ', ' : '') + city || 'a home') + ' (MLS #' + listingId + '). See everything they opened on the Activity tab.', listingId);
  }
}

function savedAlert_(id, added) {
  const props = PropertiesService.getScriptProperties();
  const day = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd');
  const key = 'saved_' + id.slice(0, 8) + '_' + day;
  if (props.getProperty(key)) return;
  const sh = sheet_(), rowNum = findRow_(sh, id); if (!rowNum) return;
  const r = sh.getRange(rowNum, 1, 1, HEADERS.length).getValues()[0];
  if (String(r[C.Status]).trim() !== 'Active') return;
  props.setProperty(key, '1');
  activityNotice_(r, 'just saved ' + (added === 1 ? 'a home' : added + ' homes') + ' ♥',
    'See which ones on the Saved homes tab.', '');
}

// Email + phone alert to Marcos with Call / Text buttons
function activityNotice_(r, what, detail, mlsId) {
  const name = String(r[C.Name]), first = name.split(' ')[0];
  const tel = String(r[C.Phone] || '').replace(/[^0-9+]/g, '');
  const email = String(r[C.Email] || '');
  const search = [r[C.Search], (r[C['Min price']] || r[C['Max price']]) ? money_(r[C['Min price']]) + '–' + money_(r[C['Max price']]) : '', r[C.Beds] ? r[C.Beds] + '+ beds' : ''].filter(String).join(' · ');
  const subject = '📈 CALL NOW: ' + name + ' ' + what;
  const home = mlsId ? SEARCH_PAGE + '#home=' + encodeURIComponent(String(mlsId).replace(/[^0-9]/g, '')) : '';
  const html = '<div style="font-family:Arial,sans-serif;font-size:15px;color:#1a2237">' +
    '<h2 style="margin:0 0 12px;color:#13203b">' + esc_(name) + ' ' + esc_(what) + '</h2>' +
    '<p>' + esc_(detail) + (home ? ' <a href="' + home + '">See the home</a>' : '') + '</p>' +
    (search ? '<p><b>Their search:</b> ' + esc_(search) + '</p>' : '') +
    '<p><b>Email:</b> ' + esc_(email) + '<br><b>Phone:</b> ' + (tel ? '<a href="tel:' + tel + '">' + esc_(String(r[C.Phone])) + '</a>' : '(not given)') + '</p>' +
    (tel ? '<p><a href="tel:' + tel + '" style="background:#b98b5c;color:#fff;padding:10px 18px;text-decoration:none">Call ' + esc_(first) + '</a> &nbsp; <a href="sms:' + tel + '" style="background:#13203b;color:#fff;padding:10px 18px;text-decoration:none">Text ' + esc_(first) + '</a></p>' : '') +
    '<p style="color:#8a8579;font-size:12px">Tip: mention a home they looked at, not that you saw them browsing. From your Listing Alert Leads sheet: ' + SpreadsheetApp.getActive().getUrl() + '</p></div>';
  GmailApp.sendEmail(OWNER_EMAIL, subject, subject, { htmlBody: html, name: '605homesearch Alerts' });
  if (!NTFY_TOPIC) return;
  const actions = [];
  if (tel) actions.push({ action: 'view', label: 'Call', url: 'tel:' + tel, clear: false });
  if (tel) actions.push({ action: 'view', label: 'Text', url: 'sms:' + tel, clear: false });
  if (home) actions.push({ action: 'view', label: 'See home', url: home, clear: false });
  UrlFetchApp.fetch('https://ntfy.sh', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    payload: JSON.stringify({
      topic: NTFY_TOPIC, priority: 5, tags: ['chart_with_upwards_trend'],
      title: 'Call now: ' + name + ' ' + what,
      message: [detail, tel ? 'Phone: ' + tel : '', email ? 'Email: ' + email : ''].filter(String).join('\n'),
      click: tel ? 'tel:' + tel : (home || SEARCH_PAGE),
      actions: actions,
    }),
  });
}

// Upcoming public open houses by MLS id: { mlsId: [{start, end}] }
function openHouses_() {
  const map = {};
  try {
    const res = UrlFetchApp.fetch(LISTINGS_API.replace(/\/properties$/, '/openhouses'), { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return map;
    const now = Date.now();
    JSON.parse(res.getContentText()).forEach(function (o) {
      if (!o || !o.mlsId || new Date(o.end || o.start).getTime() < now) return;
      (map[o.mlsId] = map[o.mlsId] || []).push(o);
    });
    Object.keys(map).forEach(function (k) { map[k].sort(function (x, y) { return new Date(x.start) - new Date(y.start); }); });
  } catch (err) { console.error('open houses failed', err); }
  return map;
}

function statusOf_(h) {
  const s = String((h.mls && h.mls.status) || '');
  if (/closed|sold/i.test(s)) return 'Sold';
  if (/pending|undercontract|contingent/i.test(s)) return 'Pending';
  if (/^active$|comingsoon/i.test(s) || !s) return 'Active';
  return 'Off market';
}

// Changes to one person's saved homes since last check: price cut, back on market, pending, sold, open house this week.
function savedChanges_(id, oh) {
  const sh = savedSheet_(), last = sh.getLastRow(); if (last < 2) return [];
  const rows = sh.getRange(2, 1, last - 1, SAVED_HEADERS.length).getValues();
  const mine = []; rows.forEach(function (r, i) { if (String(r[0]) === id) mine.push({ row: i + 2, r: r }); });
  if (!mine.length) return [];
  const res = UrlFetchApp.fetchAll(mine.map(function (m) { return { url: LISTINGS_API + '/' + encodeURIComponent(m.r[1]) + '?include=compliance', muteHttpExceptions: true }; }));
  const out = [], weekOut = Date.now() + 7 * 864e5;
  mine.forEach(function (m, i) {
    const code = res[i].getResponseCode();
    if (code === 404) { sh.getRange(m.row, 5).setValue('Off market'); return; }
    if (code !== 200) return;
    let h; try { h = JSON.parse(res[i].getContentText()); } catch (e) { return; }
    if (!h || h.internetEntireListingDisplay === false) return;
    const st = statusOf_(h), prevSt = String(m.r[4] || ''), prevPrice = Number(m.r[3]) || 0;
    let kind = '';
    if (prevSt) {
      if (st === 'Sold' && prevSt !== 'Sold') kind = 'sold';
      else if (st === 'Pending' && prevSt !== 'Pending' && prevSt !== 'Sold') kind = 'pending';
      else if (st === 'Active' && prevSt !== 'Active') kind = 'back';
      else if (st === 'Active' && h.listPrice && prevPrice && h.listPrice < prevPrice) { kind = 'drop'; h._was = prevPrice; }
    }
    const next = st === 'Active' ? (oh[h.mlsId] || []).filter(function (o) { return new Date(o.start).getTime() < weekOut; })[0] : null;
    if (next) h._oh = next;
    const ohKey = next ? String(next.start) : String(m.r[5] || '');
    if (!kind && next && String(m.r[5]) !== String(next.start)) kind = 'oh';
    sh.getRange(m.row, 4, 1, 3).setValues([[h.listPrice || '', st, ohKey]]);
    if (kind) { h._kind = kind; h._saved = true; out.push(h); }
  });
  return out;
}

// ---------- One-time setup ----------
function setup() {
  const sh = sheet_();
  sh.setName('Alert Leads');
  sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold').setBackground('#13203b').setFontColor('#ffffff');
  sh.setFrozenRows(1);
  sh.getRange(2, C.Status + 1, 1000, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['Active', 'Paused', 'Unsubscribed'], true).build());
  sh.getRange(2, C['How often'] + 1, 1000, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['Daily', 'Weekly'], true).build());
  sh.getRange(2, C['Auto-adjust'] + 1, 1000, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['Yes', 'No'], true).build());
  sh.hideColumns(C['Map area'] + 1); sh.hideColumns(C.ID + 1);
  activity_(); snapSheet_(); savedSheet_();
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'sendAlerts') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('sendAlerts').timeBased().everyDays(1).atHour(8).create();
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'weeklyLeadReport') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('weeklyLeadReport').timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).create();
  // quick test that the listings connection works
  const test = search_({ q: 'Sioux Falls' }, null);
  console.log('Setup done. Listings connection OK: ' + test.length + ' homes found.');
}

// ---------- Monday "who to call this week" report ----------
function weeklyLeadReport() {
  const sh = sheet_(), rows = sh.getDataRange().getValues().slice(1).filter(function (r) { return r[C.Email]; });
  const now = new Date(), DAY = 864e5, weekAgo = new Date(now - 7 * DAY), twoWeeks = new Date(now - 14 * DAY);
  const tz = Session.getScriptTimeZone(), day = function (d) { return Utilities.formatDate(new Date(d), tz, 'MMM d'); };

  // what each person opened (Activity tab)
  const act = activity_(), last = act.getLastRow(), byId = {};
  if (last >= 2) {
    const start = Math.max(2, last - 5000);
    act.getRange(start, 1, last - start + 1, ACT_HEADERS.length).getValues().forEach(function (x) {
      const id = String(x[9] || '').toLowerCase(); if (!id) return;
      const p = byId[id] || (byId[id] = { week: 0, lastSeen: null, homes: {}, prices: [], cities: {} });
      const when = new Date(x[0]);
      if (!p.lastSeen || when > p.lastSeen) p.lastSeen = when;
      if (when < weekAgo) return;
      p.week++;
      const k = String(x[3]);
      const hm = p.homes[k] || (p.homes[k] = { n: 0, price: x[4], addr: x[8], city: x[7] });
      hm.n++;
      if (x[4]) p.prices.push(Number(x[4]));
      if (x[7]) p.cities[x[7]] = (p.cities[x[7]] || 0) + 1;
    });
  }

  const people = rows.map(function (r) {
    const id = String(r[C.ID] || '').toLowerCase(), a = byId[id] || { week: 0, lastSeen: null, homes: {}, prices: [], cities: {} };
    const homes = Object.keys(a.homes).map(function (k) { return Object.assign({ mls: k }, a.homes[k]); }).sort(function (x, y) { return y.n - x.n; });
    const signed = new Date(r[C['Signed up']]);
    const isNew = signed >= weekAgo;
    const repeat = homes.length && homes[0].n >= 2 ? homes[0] : null;
    const score = a.week + (repeat ? repeat.n * 3 : 0) + (isNew ? 5 : 0) + (r[C.Phone] ? 2 : 0);
    return { r: r, a: a, homes: homes, isNew: isNew, repeat: repeat, score: score, signed: signed,
             active: String(r[C.Status]).trim() === 'Active' };
  });
  const act7 = people.filter(function (p) { return p.active && (p.a.week || p.isNew); }).sort(function (x, y) { return y.score - x.score; });
  const quiet = people.filter(function (p) { return p.active && !p.isNew && (!p.a.lastSeen || p.a.lastSeen < twoWeeks) && p.signed < twoWeeks; });
  const totalActive = people.filter(function (p) { return p.active; }).length;
  const newCount = people.filter(function (p) { return p.isNew; }).length;
  const views = people.reduce(function (s, p) { return s + p.a.week; }, 0);

  const btn = function (href, label, bg) { return '<a href="' + href + '" style="background:' + bg + ';color:#fff;padding:7px 12px;text-decoration:none;border-radius:4px;font-size:13px;margin-right:6px">' + label + '</a>'; };
  const person = function (p, i) {
    const r = p.r, name = String(r[C.Name]), first = name.split(' ')[0], tel = String(r[C.Phone] || '').replace(/[^0-9+]/g, '');
    const pr = p.a.prices.slice().sort(function (x, y) { return x - y; });
    const towns = Object.keys(p.a.cities).sort(function (x, y) { return p.a.cities[y] - p.a.cities[x]; }).slice(0, 3).join(', ');
    const bits = [];
    if (p.isNew) bits.push('<b style="color:#b98b5c">New this week</b> (' + day(p.signed) + ')');
    if (p.a.week) bits.push(p.a.week + ' home view' + (p.a.week === 1 ? '' : 's'));
    if (towns) bits.push(esc_(towns));
    if (pr.length) bits.push(money_(pr[0]) + (pr.length > 1 && pr[pr.length - 1] !== pr[0] ? '–' + money_(pr[pr.length - 1]) : ''));
    if (!p.a.week && r[C.Search]) bits.push('alert: ' + esc_(String(r[C.Search])));
    const rep = p.repeat ? '<br>🔥 Opened <b>' + esc_((p.repeat.addr ? p.repeat.addr + ', ' : '') + (p.repeat.city || '')) + '</b> (' + money_(p.repeat.price) + ') ' + p.repeat.n + ' times · <a href="' + SEARCH_PAGE + '#home=' + encodeURIComponent(p.repeat.mls) + '">see it</a>' : '';
    return '<tr><td style="padding:10px 0;border-bottom:1px solid #e2d8ca;vertical-align:top">' +
      '<b style="font-size:16px">' + (i + 1) + '. ' + esc_(name) + '</b>' + (String(r[C.Language]) === 'Español' ? ' (Español)' : '') + '<br>' +
      '<span style="color:#4a5063">' + bits.join(' · ') + '</span>' + rep + '<br>' +
      '<span style="font-size:13px">' + esc_(String(r[C.Email])) + (tel ? ' · ' + esc_(String(r[C.Phone])) : ' · no phone') + '</span>' +
      '<div style="margin-top:8px">' + (tel ? btn('tel:' + tel, 'Call ' + esc_(first), '#b98b5c') + btn('sms:' + tel, 'Text', '#13203b') : '') + btn('mailto:' + encodeURIComponent(String(r[C.Email])), 'Email', '#4a5063') + '</div>' +
      '</td></tr>';
  };
  const top = act7.slice(0, 15);
  const html = '<div style="font-family:Arial,sans-serif;font-size:15px;color:#1a2237;max-width:620px">' +
    '<h2 style="margin:0 0 6px;color:#13203b">Who to call this week</h2>' +
    '<p style="margin:0 0 14px;color:#4a5063">' + newCount + ' new sign-up' + (newCount === 1 ? '' : 's') + ' · ' + views + ' home views · ' + totalActive + ' people getting alerts</p>' +
    (top.length ? '<p style="margin:0">Most active first:</p><table cellpadding="0" cellspacing="0" width="100%">' + top.map(person).join('') + '</table>' + (act7.length > 15 ? '<p>+ ' + (act7.length - 15) + ' more in the sheet.</p>' : '')
                : '<p>No one signed up or opened homes this week.</p>') +
    (quiet.length ? '<h3 style="color:#13203b;margin:22px 0 4px">Gone quiet (no homes opened in 2+ weeks)</h3><p style="margin:0;color:#4a5063">A quick check-in text can bring them back:</p><p>' +
      quiet.slice(0, 20).map(function (p) { const tel = String(p.r[C.Phone] || '').replace(/[^0-9+]/g, ''); return esc_(String(p.r[C.Name])) + (tel ? ' · <a href="sms:' + tel + '">text</a>' : ' · <a href="mailto:' + encodeURIComponent(String(p.r[C.Email])) + '">email</a>') + (p.a.lastSeen ? ' (last seen ' + day(p.a.lastSeen) + ')' : ''); }).join('<br>') +
      (quiet.length > 20 ? '<br>+ ' + (quiet.length - 20) + ' more' : '') + '</p>' : '') +
    '<p style="color:#8a8579;font-size:12px;margin-top:22px">From your Listing Alert Leads sheet: ' + SpreadsheetApp.getActive().getUrl() + '</p></div>';
  const subject = '📋 Who to call this week: ' + (top.length ? top.slice(0, 3).map(function (p) { return String(p.r[C.Name]).split(' ')[0]; }).join(', ') + (top.length > 3 ? ' + ' + (top.length - 3) + ' more' : '') : 'quiet week');
  GmailApp.sendEmail(OWNER_EMAIL, subject, subject, { htmlBody: html, name: '605homesearch Alerts' });
}

// ---------- Test: emails Marcos samples of the alert emails using real homes for sale ----------
// Pick "sendTestEmails" in the function menu → Run. Sends 2 emails to OWNER_EMAIL only.
function sendTestEmails() {
  const a = { name: OWNER_NAME, email: OWNER_EMAIL, q: 'Sioux Falls', maxprice: 400000, minbeds: 3, lang: 'English' };
  const homes = search_(a, null, 20);
  if (homes.length < 6) throw new Error('Not enough homes found for the test');
  const oh = openHouses_();
  homes.forEach(function (h) { if (oh[h.mlsId]) h._oh = oh[h.mlsId][0]; });
  const one = Object.assign({}, homes[0], { _kind: 'new' });
  sendEmail_(a, 'test', [one], false, 1, [one], homes.slice(3, 6));
  const mix = [Object.assign({}, homes[0], { _kind: 'new' }), Object.assign({}, homes[1], { _kind: 'drop', _was: (homes[1].listPrice || 0) + 10000, _saved: true }), Object.assign({}, homes[2], { _kind: 'back' })];
  sendEmail_(a, 'test', mix, false, 3, mix, homes.slice(3, 6));
}

// ---------- Helpers ----------
function sheet_() { return SpreadsheetApp.getActive().getSheets()[0]; }
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function clean_(v, n) { return String(v || '').replace(/[<>]/g, '').replace(/^[=+\-@]+/, '').trim().slice(0, n); }
function digits_(v) { const d = String(v || '').replace(/[^0-9]/g, '').slice(0, 9); return d ? Number(d) : ''; }
function cleanPoints_(v) {
  return String(v || '').split('|').filter(function (pt) { return /^-?\d{1,3}\.\d{1,6},-?\d{1,3}\.\d{1,6}$/.test(pt); }).slice(0, 30).join('|');
}
function validEmail_(e) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e); }
function esc_(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
function money_(n) { return n ? '$' + Math.round(Number(n)).toLocaleString('en-US') : ''; }
function underDailyLimit_() {
  const props = PropertiesService.getScriptProperties();
  const key = 'signups_' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd');
  const n = Number(props.getProperty(key) || 0);
  if (n >= MAX_SIGNUPS_PER_DAY) return false;
  props.setProperty(key, String(n + 1));
  return true;
}
// RASE sends addresses like "508 E Plum Creek Rd Road" - drop the repeated spelled-out street type
function cleanAddr_(full) {
  const S = { rd: 'road', dr: 'drive', st: 'street', ave: 'avenue', av: 'avenue', ln: 'lane', ct: 'court', cir: 'circle', pl: 'place', blvd: 'boulevard', trl: 'trail', pkwy: 'parkway', ter: 'terrace', hwy: 'highway', cv: 'cove', pt: 'point', sq: 'square', xing: 'crossing' };
  const w = String(full || '').split(/\s+/), out = [];
  for (let i = 0; i < w.length; i++) {
    const prev = out.length ? out[out.length - 1].replace(/\.$/, '').toLowerCase() : '';
    if (prev && S[prev] && S[prev] === w[i].toLowerCase()) continue;
    out.push(w[i]);
  }
  return out.join(' ');
}
