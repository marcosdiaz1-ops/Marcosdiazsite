// Featured Homes carousel on the homepage (EN + ES).
// Shows the newest active homes in Sioux Falls and the surrounding towns from the live RASE MLS feed
// (same Cloudflare Worker the search page uses). Tapping a card opens the full photo view on the search page.
(function () {
  var box = document.getElementById('featured');
  if (!box) return;
  var track = box.querySelector('.fh-track');
  var ES = document.documentElement.lang === 'es';
  function t(en, es) { return ES ? es : en; }
  var API = 'https://listings.605homesearch.com/properties';
  var SEARCH = ES ? '/es/buscar-casas/' : '/search/';
  // Sioux Falls plus Tea, Harrisburg, Brandon, Hartford, Crooks, Lennox, Canton and Garretson
  var AREA = ['43.80000,-97.05000', '43.80000,-96.45000', '43.25000,-96.45000', '43.25000,-97.05000'];

  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var money = function (n) { return n ? '$' + Math.round(n).toLocaleString() : ''; };
  // smaller copy of the MLS photo (same trick as the search page)
  function px(u, w) { return String(u || '').replace(/(\/ParagonImages\/Property\/[^\/]+\/[^\/]+\/\d+\/\d+\/)\d+\/\d+\//, '$1' + w + '/' + Math.round(w * 3 / 4) + '/'); }
  var SUFFIX = { rd:'road', dr:'drive', st:'street', ave:'avenue', av:'avenue', ln:'lane', ct:'court', cir:'circle', pl:'place', blvd:'boulevard', trl:'trail', pkwy:'parkway', ter:'terrace', hwy:'highway', cv:'cove', pt:'point', sq:'square', xing:'crossing' };
  function cleanAddr(full) {
    var w = String(full || '').split(/\s+/), out = [];
    for (var i = 0; i < w.length; i++) {
      var prev = out.length ? out[out.length - 1].replace(/\.$/, '').toLowerCase() : '';
      if (prev && SUFFIX[prev] && SUFFIX[prev] === w[i].toLowerCase()) continue;
      out.push(w[i]);
    }
    return out.join(' ');
  }
  function baths(h) { var f = h.property || {}, n = function (x) { return +x || 0; }; return (n(f.bathsFull) + n(f.bathsThreeQuarter) + 0.5 * n(f.bathsHalf)) || n(f.bathrooms) || 0; }
  function isNew(h) { var d = h.listDate ? (Date.now() - new Date(h.listDate).getTime()) / 864e5 : NaN; return !isNaN(d) && d <= 7; }
  // RASE IDX rule: listing firm, listing agent and contact shown with every listing
  function courtesy(h) {
    var ag = h.agent || {}, of = h.office || {}, oc = of.contact || {}, ac = ag.contact || {};
    var name = [ag.firstName, ag.lastName].filter(Boolean).join(' ');
    var c = (h.compliance && h.compliance.attributionContact) || oc.office || oc.email || ac.office || ac.email || '';
    var office = of.name || of.servingName || '';
    return t('Listing courtesy of ', 'Cortesía de ') + esc(office) + (name ? ' · ' + esc(name) : '') + (c ? ' · ' + esc(c) : '');
  }

  function card(h) {
    var p = h.property || {}, a = h.address || {};
    var addr = h.internetAddressDisplay !== false ? cleanAddr(a.full) : '';
    var photo = (h.photos || [])[0];
    var tag = isNew(h) ? t('New', 'Nueva') : ((h.originalListPrice && h.listPrice && h.originalListPrice > h.listPrice) ? t('Price cut', 'Bajó de precio') : '');
    var b = baths(h);
    return '<a class="fh-card" href="' + SEARCH + '#home=' + encodeURIComponent(h.mlsId) + '">' +
      '<div class="fh-ph">' + (photo ? '<img src="' + esc(px(photo, 800)) + '" alt="' + esc(t('Photo of ', 'Foto de ') + (addr || a.city || t('home for sale', 'casa en venta'))) + '" loading="lazy">' : '') +
      (tag ? '<span class="fh-tag">' + tag + '</span>' : '') + '</div>' +
      '<div class="fh-in"><div class="fh-pr">' + money(h.listPrice) + '</div>' +
      '<div class="fh-st">' + (p.bedrooms || 0) + t(' bd', ' rec') + (b ? ' · ' + b + t(' ba', ' baños') : '') + (p.area ? ' · ' + p.area.toLocaleString() + t(' sq ft', ' pies²') : '') + '</div>' +
      '<div class="fh-ad">' + (addr ? esc(addr) + ', ' : '') + esc(a.city || '') + '</div>' +
      '<div class="fh-co">' + courtesy(h) + '</div></div></a>';
  }

  var q = new URLSearchParams();
  q.append('status', 'Active');
  q.set('type', 'residential');
  AREA.forEach(function (pt) { q.append('points', pt); });
  q.set('sort', '-listdate');
  q.set('limit', '12');
  q.set('include', 'compliance');

  fetch(API + '?' + q.toString()).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (list) {
    list = (list || []).filter(function (h) { return h && h.mlsId && h.photos && h.photos.length && h.listPrice; });
    if (!list.length) throw 0;
    track.innerHTML = list.map(card).join('');
    box.classList.add('fh-ready');
  }).catch(function () { box.classList.add('fh-empty'); });

  // arrows on a computer; swipe on a phone
  box.addEventListener('click', function (e) {
    var b = e.target.closest('.fh-nav'); if (!b) return;
    var c = track.querySelector('.fh-card'); var step = c ? c.getBoundingClientRect().width + 20 : 300;
    track.scrollBy({ left: b.classList.contains('n') ? step : -step, behavior: 'smooth' });
  });
})();
