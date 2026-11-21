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
const LISTINGS_API = 'https://listings.605homesearch.com/properties';
const MAX_HOMES_PER_EMAIL = 12;
const MAX_EMAILS_PER_RUN = 80;                    // stay well under Gmail's daily sending limit
const MAX_SIGNUPS_PER_DAY = 40;                   // safety limit against spam abuse
const OFFICE = 'Keller Williams Realty Sioux Falls, 6300 S Connie Ave, Sioux Falls, SD 57108 · 605-275-0555';

const HEADERS = ['Signed up', 'Name', 'Email', 'Phone', 'Search', 'Min price', 'Max price', 'Beds', 'Baths', 'Type',
                 'Map area', 'How often', 'Language', 'Status', 'Last sent', 'Homes sent', 'Source', 'Notes', 'ID'];
const C = {}; HEADERS.forEach(function (h, i) { C[h] = i; });
const TYPES = { residential: 'House', condominium: 'Condo', multifamily: 'Multi-family', land: 'Land' };

// ---------- Website sign-up ----------
function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.botcheck) return json_({ ok: true });          // spam trap
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
    id = Utilities.getUuid();
    sh.appendRow([new Date(), a.name, a.email, a.phone ? "'" + a.phone : '', a.q, a.minprice, a.maxprice, a.minbeds, a.minbaths,
                  a.type ? TYPES[a.type] : '', a.points, a.freq, a.lang, 'Active', new Date(), 0, a.source, '', id]);
  } finally {
    lock.releaseLock();
  }
  let homes = [];
  try { homes = search_(a, null).slice(0, 6); } catch (err) { console.error('search failed', err); }
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
    try { homes = search_(a, last); } catch (err) { console.error('search failed for row ' + (i + 1), err); continue; }
    if (!homes.length) continue;
    try {
      sendEmail_(a, r[C.ID], homes.slice(0, MAX_HOMES_PER_EMAIL), false, homes.length);
      sh.getRange(i + 1, C['Last sent'] + 1, 1, 2).setValues([[now, (Number(r[C['Homes sent']]) || 0) + homes.length]]);
      sent++;
    } catch (err) { console.error('email failed for row ' + (i + 1), err); }
  }
  console.log('alert emails sent: ' + sent);
}

// ---------- Listing search ----------
function search_(a, since) {
  const q = [];
  const add = function (k, v) { if (v !== '' && v != null) q.push(k + '=' + encodeURIComponent(v)); };
  add('q', a.q); add('minprice', a.minprice); add('maxprice', a.maxprice);
  add('minbeds', a.minbeds); add('minbaths', a.minbaths); add('type', a.type);
  if (!a.q && a.points) a.points.split('|').forEach(function (pt) { add('points', pt); });
  add('status', 'Active'); add('sort', '-listdate'); add('limit', 50);
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
  return { name: String(r[C.Name]), email: String(r[C.Email]), q: String(r[C.Search] || ''), minprice: r[C['Min price']], maxprice: r[C['Max price']],
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

function sendEmail_(a, id, homes, welcome, total) {
  const es = a.lang === 'Español';
  const first = a.name.split(' ')[0];
  const unsub = ScriptApp.getService().getUrl() + '?unsub=' + encodeURIComponent(id);
  const what = describe_(a, es);
  const n = total || homes.length;
  const subject = welcome
    ? (es ? 'Sus alertas de casas están listas, ' + first : 'Your home alerts are set up, ' + first)
    : (es ? n + (n === 1 ? ' casa nueva' : ' casas nuevas') + ': ' + what : n + ' new ' + (n === 1 ? 'home' : 'homes') + ': ' + what);
  const intro = welcome
    ? (es ? 'Hola ' + first + ', listo. Le enviaré casas nuevas apenas salgan al mercado que coincidan con: <b>' + esc_(what) + '</b>.' + (homes.length ? ' Estas están en venta ahora mismo:' : '')
          : 'Hi ' + first + ', you’re all set. I’ll send you new homes as soon as they hit the market that match: <b>' + esc_(what) + '</b>.' + (homes.length ? ' Here’s what’s for sale right now:' : ''))
    : (es ? 'Hola ' + first + ', estas casas nuevas salieron al mercado y coinciden con su búsqueda (<b>' + esc_(what) + '</b>):'
          : 'Hi ' + first + ', these new homes just hit the market and match your search (<b>' + esc_(what) + '</b>):');
  const cards = homes.map(function (h) { return card_(h, es); }).join('');
  const more = total && total > homes.length
    ? '<p><a href="' + SEARCH_PAGE + '" style="color:#8a6236">' + (es ? 'Ver las ' + total + ' casas nuevas →' : 'See all ' + total + ' new homes →') + '</a></p>' : '';
  const html =
    '<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;color:#1a2237;font-size:15px;line-height:1.5">' +
    '<div style="background:#13203b;color:#fff;padding:16px 20px"><b style="font-size:18px">Marcos Diaz</b><br><span style="color:#d7b48c;font-size:12px;letter-spacing:2px">KELLER WILLIAMS REALTY SIOUX FALLS</span></div>' +
    '<div style="padding:18px 20px"><p>' + intro + '</p>' + cards + more +
    '<p style="margin-top:20px">' + (es ? '¿Quiere ver alguna? Llámeme o envíeme un texto al ' : 'Want to see one? Call or text me at ') +
    '<a href="tel:+16058389140" style="color:#8a6236"><b>' + PHONE + '</b></a>.</p>' +
    '<p>Marcos Diaz<br><span style="color:#4a5063;font-size:13px">Broker Associate · REALTOR® · Keller Williams Realty Sioux Falls</span></p></div>' +
    '<div style="padding:14px 20px;border-top:1px solid #e2d8ca;font-size:11px;color:#777;line-height:1.5">' +
    (es ? 'Recibe este correo porque pidió alertas de casas en 605homesearch.com. ' : 'You’re getting this because you asked for home alerts on 605homesearch.com. ') +
    '<a href="' + unsub + '" style="color:#777">' + (es ? 'Cancelar alertas' : 'Unsubscribe') + '</a>.<br>' +
    (es ? 'La información de las casas se considera confiable pero no está garantizada y debe verificarse. ' : 'Listing information is deemed reliable but not guaranteed and should be independently verified. ') +
    (es ? 'Las casas son cortesía de la correduría indicada en cada una. ' : 'Listings are courtesy of the listing brokerage named on each listing. ') +
    'Listing data provided by the REALTOR® Association of the Sioux Empire MLS.<br>' +
    'Marcos Diaz, Broker Associate · ' + OFFICE + '. Each office is independently owned and operated. Equal Housing Opportunity.</div></div>';
  GmailApp.sendEmail(a.email, subject, (es ? 'Abra este correo en HTML para ver las casas. Cancelar: ' : 'Open this email in HTML to see the homes. Unsubscribe: ') + unsub,
    { htmlBody: html, name: OWNER_NAME, replyTo: OWNER_EMAIL });
}

function card_(h, es) {
  const p = h.property || {}, ad = h.address || {}, ag = h.agent || {}, of = h.office || {};
  const showAddr = h.internetAddressDisplay !== false;
  const street = showAddr ? cleanAddr_(ad.full) + ', ' : '';
  const baths = (p.bathsFull || 0) + (p.bathsHalf ? 0.5 * p.bathsHalf : 0) || p.bathrooms || '';
  const photo = h.photos && h.photos[0];
  const link = SEARCH_PAGE + '#home=' + h.mlsId;
  const contact = (of.contact && (of.contact.office || of.contact.email)) || '';
  const courtesy = (es ? 'Cortesía de ' : 'Listing courtesy of ') + esc_(of.name || '') + ([ag.firstName, ag.lastName].filter(Boolean).length ? ' · ' + esc_([ag.firstName, ag.lastName].filter(Boolean).join(' ')) : '') + (contact ? ' · ' + esc_(contact) : '');
  return '<table cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e2d8ca;border-radius:10px;margin:14px 0;border-collapse:separate;overflow:hidden"><tr><td>' +
    (photo ? '<a href="' + link + '"><img src="' + esc_(photo) + '" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0" alt=""></a>' : '') +
    '<div style="padding:12px 14px">' +
    '<div style="font-size:22px;font-weight:bold;color:#1a2237">' + money_(h.listPrice) + '</div>' +
    '<div>' + (p.bedrooms || 0) + (es ? ' rec · ' : ' bd · ') + baths + (es ? ' baños' : ' ba') + (p.area ? ' · ' + Number(p.area).toLocaleString() + (es ? ' pies²' : ' sq ft') : '') + '</div>' +
    '<div style="color:#4a5063">' + esc_(street + (ad.city || '')) + '</div>' +
    '<div style="font-size:13px;color:#1a2237;margin-top:6px">' + courtesy + '</div>' +
    '<a href="' + link + '" style="display:inline-block;margin-top:10px;background:#b98b5c;color:#fff;padding:9px 16px;text-decoration:none;border-radius:6px">' + (es ? 'Ver esta casa' : 'See this home') + '</a>' +
    '</div></td></tr></table>';
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
  sh.hideColumns(C['Map area'] + 1); sh.hideColumns(C.ID + 1);
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'sendAlerts') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('sendAlerts').timeBased().everyDays(1).atHour(8).create();
  // quick test that the listings connection works
  const test = search_({ q: 'Sioux Falls' }, null);
  console.log('Setup done. Listings connection OK: ' + test.length + ' homes found.');
}

// ---------- Helpers ----------
function sheet_() { return SpreadsheetApp.getActive().getSheets()[0]; }
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function clean_(v, n) { return String(v || '').replace(/[<>]/g, '').replace(/^[=+\-@]+/, '').trim().slice(0, n); }
function digits_(v) { const d = String(v || '').replace(/[^0-9]/g, '').slice(0, 9); return d ? Number(d) : ''; }
function cleanPoints_(v) {
  return String(v || '').split('|').filter(function (pt) { return /^-?\d{1,3}\.\d{1,6},-?\d{1,3}\.\d{1,6}$/.test(pt); }).slice(0, 4).join('|');
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
