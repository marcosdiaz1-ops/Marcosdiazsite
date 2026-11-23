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
 *   6. Besides new listings, alert emails include PRICE DROPS on homes that match and homes
 *      BACK ON THE MARKET. A hidden "Snapshots" tab remembers each person's matching homes and
 *      prices so it can spot the changes.
 *   7. Monday 7 AM "who to call this week" email to Marcos: new sign-ups, the most active
 *      people (ranked), homes they keep opening, and everyone gone quiet for 2+ weeks.
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
  let sent = 0;
  for (let i = 1; i < rows.length && sent < MAX_EMAILS_PER_RUN; i++) {
    const r = rows[i];
    if (String(r[C.Status]).trim() !== 'Active' || !validEmail_(String(r[C.Email]))) continue;
    const last = r[C['Last sent']] instanceof Date ? r[C['Last sent']] : new Date(now.getTime() - 86400000);
    const weekly = /week/i.test(String(r[C['How often']]));
    if (weekly && now - last < 6.5 * 86400000) continue;
    const a = rowToSearch_(r);
    let homes;
    try { homes = changes_(a, String(r[C.ID]), last); } catch (err) { console.error('search failed for row ' + (i + 1), err); continue; }
    if (!homes.length) continue;
    try {
      sendEmail_(a, r[C.ID], homes.slice(0, MAX_HOMES_PER_EMAIL), false, homes.length, homes);
      sh.getRange(i + 1, C['Last sent'] + 1, 1, 2).setValues([[now, (Number(r[C['Homes sent']]) || 0) + homes.length]]);
      sent++;
    } catch (err) { console.error('email failed for row ' + (i + 1), err); }
  }
  console.log('alert emails sent: ' + sent);
}

// New listings, price drops and back-on-market homes for one person since their last email.
// Each home gets h._kind = 'new' | 'drop' | 'back' (and h._was = old price for drops).
function changes_(a, id, since) {
  const all = search_(a, null, 500);
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
    const res = UrlFetchApp.fetch(LISTINGS_API + '/' + mlsId, { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return;
    const h = JSON.parse(res.getContentText()), hp = h.property || {}, ad = h.address || {};
    const baths = (hp.bathsFull || 0) + (hp.bathsHalf ? 0.5 * hp.bathsHalf : 0) || hp.bathrooms || '';
    const addr = h.internetAddressDisplay === false ? '' : cleanAddr_(ad.full);
    const act = activity_();
    act.appendRow([new Date(), r[C.Name], r[C.Email], h.listingId || mlsId, h.listPrice || '', hp.bedrooms || '', baths, ad.city || '', addr, id]);
    const views = (Number(r[C.Views]) || 0) + 1;
    sh.getRange(rowNum, C.Views + 1).setValue(views);

    const mine = myViews_(act, id);
    hotLead_(r, id, mlsId, mine, h, addr);
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
  add('status', 'Active'); add('sort', '-listdate'); add('limit', limit || 50);
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

function sendEmail_(a, id, homes, welcome, total, allHomes) {
  const es = a.lang === 'Español';
  const first = a.name.split(' ')[0];
  const unsub = WEBAPP_URL + '?unsub=' + encodeURIComponent(id);
  const what = describe_(a, es);
  const n = total || homes.length;
  const subject = welcome
    ? (es ? 'Sus alertas de casas están listas, ' + first : 'Your home alerts are set up, ' + first)
    : summary_(allHomes || homes, es) + ': ' + what;
  const intro = welcome
    ? (es ? 'Hola ' + first + ', listo. Le enviaré casas nuevas apenas salgan al mercado que coincidan con: <b>' + esc_(what) + '</b>.' + (homes.length ? ' Estas están en venta ahora mismo:' : '')
          : 'Hi ' + first + ', you’re all set. I’ll send you new homes as soon as they hit the market that match: <b>' + esc_(what) + '</b>.' + (homes.length ? ' Here’s what’s for sale right now:' : ''))
    : (es ? 'Hola ' + first + ', hay novedades en su búsqueda (<b>' + esc_(what) + '</b>): ' + summary_(allHomes || homes, true) + '.'
          : 'Hi ' + first + ', here’s what changed in your search (<b>' + esc_(what) + '</b>): ' + summary_(allHomes || homes, false) + '.');
  const cards = homes.map(function (h) { return card_(h, es, id); }).join('');
  const more = total && total > homes.length
    ? '<p><a href="' + (es ? SEARCH_PAGE_ES : SEARCH_PAGE) + '?a=' + encodeURIComponent(id) + '" style="color:#8a6236">' + (es ? 'Ver más casas →' : 'See more homes →') + '</a></p>' : '';
  const html =
    '<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;color:#1a2237;font-size:15px;line-height:1.5">' +
    '<div style="background:#13203b;color:#fff;padding:16px 20px"><b style="font-size:18px">Marcos Diaz</b><br><span style="color:#d7b48c;font-size:12px;letter-spacing:2px">KELLER WILLIAMS REALTY SIOUX FALLS</span></div>' +
    '<div style="padding:18px 20px"><p>' + intro + '</p>' + cards + more +
    '<p style="margin-top:20px">' + (es ? '¿Quiere ver alguna? Llámeme o envíeme un texto al ' : 'Want to see one? Call or text me at ') +
    '<a href="tel:+16058389140" style="color:#8a6236"><b>' + PHONE + '</b></a>.</p>' +
    '<p>Marcos Diaz<br><span style="color:#4a5063;font-size:13px">Broker Associate · REALTOR® · Keller Williams Realty Sioux Falls</span></p></div>' +
    '<div style="padding:14px 20px;border-top:1px solid #e2d8ca;font-size:11px;color:#777;line-height:1.5">' +
    (es ? 'Recibe este correo porque pidió alertas de casas en 605homesearch.com. Sus alertas se ajustan según las casas que abre. ' : 'You’re getting this because you asked for home alerts on 605homesearch.com. Your alerts adjust to the homes you open. ') +
    '<a href="' + unsub + '" style="color:#777">' + (es ? 'Cancelar alertas' : 'Unsubscribe') + '</a>.<br>' +
    (es ? 'La información de las casas se considera confiable pero no está garantizada y debe verificarse. ' : 'Listing information is deemed reliable but not guaranteed and should be independently verified. ') +
    (es ? 'Las casas son cortesía de la correduría indicada en cada una. ' : 'Listings are courtesy of the listing brokerage named on each listing. ') +
    'Listing data provided by the REALTOR® Association of the Sioux Empire MLS.<br>' +
    'Marcos Diaz, Broker Associate · ' + OFFICE + '. Each office is independently owned and operated. Equal Housing Opportunity.</div></div>';
  GmailApp.sendEmail(a.email, subject, (es ? 'Abra este correo en HTML para ver las casas. Cancelar: ' : 'Open this email in HTML to see the homes. Unsubscribe: ') + unsub,
    { htmlBody: html, name: OWNER_NAME, replyTo: OWNER_EMAIL });
}

function summary_(homes, es) {
  const c = { 'new': 0, drop: 0, back: 0 };
  homes.forEach(function (h) { c[h._kind || 'new']++; });
  const bits = [];
  if (c['new']) bits.push(c['new'] + (es ? (c['new'] === 1 ? ' casa nueva' : ' casas nuevas') : (c['new'] === 1 ? ' new home' : ' new homes')));
  if (c.drop) bits.push(c.drop + (es ? (c.drop === 1 ? ' bajó de precio' : ' bajaron de precio') : (c.drop === 1 ? ' price drop' : ' price drops')));
  if (c.back) bits.push(c.back + (es ? ' de vuelta en el mercado' : ' back on the market'));
  return bits.join(', ');
}

function card_(h, es, id) {
  const p = h.property || {}, ad = h.address || {}, ag = h.agent || {}, of = h.office || {};
  const showAddr = h.internetAddressDisplay !== false;
  const street = showAddr ? cleanAddr_(ad.full) + ', ' : '';
  const baths = (p.bathsFull || 0) + (p.bathsHalf ? 0.5 * p.bathsHalf : 0) || p.bathrooms || '';
  const photo = h.photos && h.photos[0];
  const link = (es ? SEARCH_PAGE_ES : SEARCH_PAGE) + (id ? '?a=' + encodeURIComponent(id) : '') + '#home=' + h.mlsId;
  const contact = (of.contact && (of.contact.office || of.contact.email)) || '';
  const courtesy = (es ? 'Cortesía de ' : 'Listing courtesy of ') + esc_(of.name || '') + ([ag.firstName, ag.lastName].filter(Boolean).length ? ' · ' + esc_([ag.firstName, ag.lastName].filter(Boolean).join(' ')) : '') + (contact ? ' · ' + esc_(contact) : '');
  return '<table cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e2d8ca;border-radius:10px;margin:14px 0;border-collapse:separate;overflow:hidden"><tr><td>' +
    (photo ? '<a href="' + link + '"><img src="' + esc_(photo) + '" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0" alt=""></a>' : '') +
    '<div style="padding:12px 14px">' +
    badge_(h, es) +
    '<div style="font-size:22px;font-weight:bold;color:#1a2237">' + money_(h.listPrice) +
    (h._kind === 'drop' && h._was ? ' <span style="font-size:15px;font-weight:normal;color:#8a8579;text-decoration:line-through">' + money_(h._was) + '</span>' : '') + '</div>' +
    '<div>' + (p.bedrooms || 0) + (es ? ' rec · ' : ' bd · ') + baths + (es ? ' baños' : ' ba') + (p.area ? ' · ' + Number(p.area).toLocaleString() + (es ? ' pies²' : ' sq ft') : '') + '</div>' +
    '<div style="color:#4a5063">' + esc_(street + (ad.city || '')) + '</div>' +
    '<div style="font-size:13px;color:#1a2237;margin-top:6px">' + courtesy + '</div>' +
    '<a href="' + link + '" style="display:inline-block;margin-top:10px;background:#b98b5c;color:#fff;padding:9px 16px;text-decoration:none;border-radius:6px">' + (es ? 'Ver esta casa' : 'See this home') + '</a>' +
    '</div></td></tr></table>';
}

function badge_(h, es) {
  const k = h._kind;
  if (!k) return '';
  const label = k === 'drop' ? (es ? 'BAJÓ DE PRECIO' : 'PRICE DROP') + (h._was ? ' · ' + money_(h._was - h.listPrice) + (es ? ' menos' : ' off') : '')
    : k === 'back' ? (es ? 'DE VUELTA EN EL MERCADO' : 'BACK ON THE MARKET') : (es ? 'NUEVA' : 'NEW');
  const bg = k === 'drop' ? '#b98b5c' : '#13203b';
  return '<span style="display:inline-block;background:' + bg + ';color:#fff;font-size:11px;font-weight:bold;letter-spacing:1px;padding:3px 8px;border-radius:12px;margin-bottom:6px">' + label + '</span><br>';
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
  activity_(); snapSheet_();
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
