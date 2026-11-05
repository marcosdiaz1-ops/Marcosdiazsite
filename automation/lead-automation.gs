/**
 * 605homesearch.com – Lead automation (Google Apps Script)
 *
 * What it does, for every website form submission:
 *   1. Saves the lead as a new row in the "605homesearch.com – Website Leads" sheet.
 *   2. Sends Marcos an instant "NEW LEAD" alert email (and, optionally, a text message).
 *   3. Sends the lead an automatic reply from Marcos's Gmail, in English or Spanish.
 * Plus: every Monday morning, emails Marcos a summary of last week's leads.
 *
 * Setup (one time):
 *   - Open the Leads sheet → Extensions → Apps Script → paste this whole file → Save.
 *   - Run the "setup" function once and approve the permissions.
 *   - Deploy → New deployment → type "Web app" → Execute as: Me → Who has access: Anyone → Deploy.
 *   - Copy the Web app URL and send it to Claude to connect it to the website form.
 */

// ---------- Settings ----------
const OWNER_EMAIL = 'marcosdiaz1@kw.com';
const OWNER_NAME = 'Marcos Diaz';
const PHONE = '605-838-9140';
const SITE = 'https://605homesearch.com';
// Optional: text-message alerts. Put your carrier's email-to-text address here,
// e.g. '6058389140@vtext.com' (Verizon), '6058389140@tmomail.net' (T-Mobile),
// '6058389140@txt.att.net' (AT&T). Leave '' to skip.
const SMS_EMAIL = '';
const MAX_AUTOREPLIES_PER_DAY = 25; // safety limit against spam abuse

const HEADERS = ['Date', 'Name', 'Phone', 'Email', 'Looking to', 'Timeline', 'Language', 'Status', 'Notes'];
const STATUSES = ['New', 'Contacted', 'Appointment set', 'Client', 'Not a fit'];

// ---------- Web endpoint (called by the website form) ----------
function doPost(e) {
  const p = (e && e.parameter) || {};
  // Spam trap: real visitors never fill this hidden field
  if (p.botcheck) return out_({ ok: true });

  const lead = {
    name: clean_(p['Name'], 100),
    phone: clean_(p['Phone'], 40),
    email: clean_(p['email'], 120).toLowerCase(),
    looking: clean_(p['Looking to'], 60),
    timeline: clean_(p['Timeline'], 60),
    language: /espa/i.test(p['Language'] || '') ? 'Español' : 'English',
  };
  if (!lead.name || !lead.phone || !lead.email) return out_({ ok: false, error: 'missing fields' });

  const lock = LockService.getScriptLock();
  lock.tryLock(10000);
  try {
    const sheet = sheet_();
    sheet.appendRow([new Date(), lead.name, "'" + lead.phone, lead.email, lead.looking, lead.timeline, lead.language, 'New', '']);
  } finally {
    lock.releaseLock();
  }

  try { alertOwner_(lead); } catch (err) { console.error('alert failed', err); }
  try { if (validEmail_(lead.email) && underDailyLimit_()) autoReply_(lead); } catch (err) { console.error('autoreply failed', err); }

  return out_({ ok: true });
}

function doGet() {
  return out_({ ok: true, service: '605homesearch lead automation' });
}

// ---------- Alerts and replies ----------
function alertOwner_(lead) {
  const first = lead.name.split(' ')[0];
  const subject = '🔔 NEW LEAD: ' + lead.name + ' – ' + (lead.looking || 'Website inquiry') + (lead.timeline ? ' (' + lead.timeline + ')' : '');
  const telDigits = lead.phone.replace(/[^0-9+]/g, '');
  const html =
    '<div style="font-family:Arial,sans-serif;font-size:15px;color:#1a2237">' +
    '<h2 style="margin:0 0 12px;color:#13203b">New website lead' + (lead.language === 'Español' ? ' 🇲🇽 (Español)' : '') + '</h2>' +
    row_('Name', lead.name) +
    row_('Phone', '<a href="tel:' + telDigits + '">' + esc_(lead.phone) + '</a>', true) +
    row_('Email', '<a href="mailto:' + esc_(lead.email) + '">' + esc_(lead.email) + '</a>', true) +
    row_('Looking to', lead.looking) +
    row_('Timeline', lead.timeline) +
    row_('Language', lead.language) +
    '<p style="margin-top:18px"><a href="tel:' + telDigits + '" style="background:#b98b5c;color:#fff;padding:10px 18px;text-decoration:none">Call ' + esc_(first) + '</a>' +
    ' &nbsp; <a href="sms:' + telDigits + '" style="background:#13203b;color:#fff;padding:10px 18px;text-decoration:none">Text ' + esc_(first) + '</a></p>' +
    '<p style="color:#8a8579;font-size:12px">An automatic reply was sent to the lead. Saved to your Website Leads sheet: ' + SpreadsheetApp.getActive().getUrl() + '</p></div>';
  GmailApp.sendEmail(OWNER_EMAIL, subject, subject + '\nPhone: ' + lead.phone + '\nEmail: ' + lead.email, { htmlBody: html, name: '605homesearch Leads' });
  if (SMS_EMAIL) {
    GmailApp.sendEmail(SMS_EMAIL, '', 'NEW LEAD: ' + lead.name + ' ' + lead.phone + ' – ' + (lead.looking || '') + ' ' + (lead.timeline || ''));
  }
}

function autoReply_(lead) {
  const first = lead.name.split(' ')[0];
  const es = lead.language === 'Español';
  const subject = es ? 'Gracias por contactarme, ' + first + ' – Marcos Diaz' : 'Thanks for reaching out, ' + first + ' – Marcos Diaz';
  const lines = es ? [
    'Hola ' + first + ',',
    'Gracias por contactarme a través de mi sitio web. Recibí su información y me comunicaré con usted personalmente muy pronto, por lo general el mismo día.',
    'Si necesita hablar conmigo antes, llámeme o envíeme un mensaje de texto al ' + PHONE + '.',
    'Mientras tanto, puede ver todas las casas en venta en Sioux Falls aquí: ' + SITE + '/es/',
    'Saludos,',
    'Marcos Diaz<br>REALTOR® · Keller Williams Realty Sioux Falls<br>' + PHONE + ' · ' + OWNER_EMAIL,
  ] : [
    'Hi ' + first + ',',
    'Thanks for reaching out through my website. I received your information and will reach out to you personally very soon, usually the same day.',
    'If you need me sooner, call or text me at ' + PHONE + '.',
    'In the meantime, you can browse homes for sale in Sioux Falls here: ' + SITE,
    'Talk soon,',
    'Marcos Diaz<br>REALTOR® · Keller Williams Realty Sioux Falls<br>' + PHONE + ' · ' + OWNER_EMAIL + '<br>Se habla español',
  ];
  const html = '<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#1a2237">' +
    lines.map(function (l) { return '<p>' + l + '</p>'; }).join('') + '</div>';
  const text = lines.join('\n\n').replace(/<br>/g, '\n');
  GmailApp.sendEmail(lead.email, subject, text, { htmlBody: html, name: OWNER_NAME, replyTo: OWNER_EMAIL });
}

// ---------- Weekly summary (Mondays) ----------
function weeklySummary() {
  const sheet = sheet_();
  const values = sheet.getDataRange().getValues().slice(1);
  const since = new Date(Date.now() - 7 * 24 * 3600 * 1000);
  const recent = values.filter(function (r) { return r[0] instanceof Date && r[0] >= since; });
  const open = values.filter(function (r) { return String(r[7]) === 'New'; });
  const tz = Session.getScriptTimeZone();
  const fmt = function (d) { return Utilities.formatDate(d, tz, 'EEE MMM d'); };
  const rowHtml = function (r) {
    return '<tr><td>' + fmt(r[0]) + '</td><td>' + esc_(r[1]) + '</td><td>' + esc_(String(r[2])) + '</td><td>' + esc_(r[4]) + '</td><td>' + esc_(r[5]) + '</td><td>' + esc_(r[6]) + '</td><td><b>' + esc_(r[7]) + '</b></td></tr>';
  };
  const table = function (rows) {
    if (!rows.length) return '<p style="color:#8a8579">None.</p>';
    return '<table cellpadding="6" style="border-collapse:collapse;font-size:13px"><tr style="background:#13203b;color:#fff"><th>Date</th><th>Name</th><th>Phone</th><th>Looking to</th><th>Timeline</th><th>Language</th><th>Status</th></tr>' + rows.map(rowHtml).join('') + '</table>';
  };
  const html = '<div style="font-family:Arial,sans-serif;color:#1a2237">' +
    '<h2>Website leads: last 7 days (' + recent.length + ')</h2>' + table(recent) +
    '<h3 style="margin-top:28px">Still marked "New" – follow up (' + open.length + ')</h3>' + table(open) +
    '<p style="color:#8a8579;font-size:12px">Update the Status column in your sheet as you follow up: ' + SpreadsheetApp.getActive().getUrl() + '</p></div>';
  GmailApp.sendEmail(OWNER_EMAIL, 'Weekly website leads: ' + recent.length + ' new, ' + open.length + ' to follow up', 'See HTML version.', { htmlBody: html, name: '605homesearch Leads' });
}

// ---------- One-time setup ----------
function setup() {
  const sheet = sheet_();
  sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold').setBackground('#13203b').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  sheet.getRange('A2:A').setNumberFormat('mmm d, yyyy h:mm am/pm');
  const rule = SpreadsheetApp.newDataValidation().requireValueInList(STATUSES, true).build();
  sheet.getRange('H2:H').setDataValidation(rule);
  sheet.setColumnWidths(1, HEADERS.length, 150);
  sheet.setColumnWidth(9, 280);
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'weeklySummary') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('weeklySummary').timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(8).create();
  return 'Setup complete';
}

// ---------- Helpers ----------
function sheet_() { return SpreadsheetApp.getActive().getSheets()[0]; }
function clean_(v, max) { return String(v || '').replace(/[\r\n\t]+/g, ' ').trim().slice(0, max); }
function validEmail_(e) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e); }
function esc_(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
function row_(label, value, raw) { return '<p style="margin:4px 0"><b style="display:inline-block;width:100px;color:#b98b5c">' + label + '</b>' + (raw ? value : esc_(value || '—')) + '</p>'; }
function out_(obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); }
function underDailyLimit_() {
  const props = PropertiesService.getScriptProperties();
  const key = 'replies_' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMdd');
  const n = Number(props.getProperty(key) || 0);
  if (n >= MAX_AUTOREPLIES_PER_DAY) return false;
  props.setProperty(key, String(n + 1));
  return true;
}
