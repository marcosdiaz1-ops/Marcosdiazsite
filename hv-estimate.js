// Instant home value estimate for the "What's my home worth?" forms (EN + ES, regular and ad landing pages).
// Adds a "Tell me about the home" step to the form. While the visitor answers the next questions, it finds
// the address on the map (free ArcGIS lookup) and pulls similar homes for sale nearby from the live MLS feed,
// then shows an estimated range on the thank-you screen (after they give their name and contact info).
// The estimate and home details are added to the lead so Marcos sees them in the sheet / email / phone alert.
// Must load BEFORE site.js (both use defer) so the lead form picks up the new step.
(function () {
  var form = document.querySelector('form#leadForm[data-kind="home-value"]');
  if (!form) return;
  var ES = document.documentElement.lang === 'es';
  function t(en, es) { return ES ? es : en; }
  var API = 'https://listings.605homesearch.com/properties';
  var GEO = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates';
  // Town centers, used if the map lookup can't find the exact address
  var TOWNS = { 'sioux falls': [43.5446, -96.7311], tea: [43.4464, -96.8359], harrisburg: [43.4314, -96.6975], brandon: [43.5947, -96.5717],
    hartford: [43.6233, -96.9428], crooks: [43.6647, -96.8112], lennox: [43.3542, -96.8928], canton: [43.3008, -96.5928], garretson: [43.7172, -96.5028],
    worthing: [43.3300, -96.7670], 'dell rapids': [43.8261, -96.7128], baltic: [43.7611, -96.7406], renner: [43.6280, -96.7240] };

  // ---------- the new step ----------
  var step1 = form.querySelector('fieldset.step[data-step="1"]');
  if (!step1) return;
  var fs = document.createElement('fieldset');
  fs.className = 'step info hv-details';
  fs.innerHTML =
    '<legend>' + t('Tell me about the home', 'Cuénteme sobre la casa') + '</legend>' +
    '<p class="hv-why">' + t('This lets me show you an instant estimate.', 'Así le puedo mostrar un cálculo al instante.') + '</p>' +
    '<div class="hv-grid">' +
      '<label>' + t('Type', 'Tipo') + '<select name="Home type">' +
        '<option value="House">' + t('House', 'Casa') + '</option>' +
        '<option value="Townhome">' + t('Townhome / twin home', 'Townhome / casa gemela') + '</option>' +
        '<option value="Condo">' + t('Condo', 'Condominio') + '</option></select></label>' +
      '<label>' + t('Bedrooms', 'Recámaras') + '<select name="Bedrooms">' + [1, 2, 3, 4, 5, 6].map(function (n) { return '<option' + (n === 3 ? ' selected' : '') + ' value="' + n + '">' + n + (n === 6 ? '+' : '') + '</option>'; }).join('') + '</select></label>' +
      '<label>' + t('Bathrooms', 'Baños') + '<select name="Bathrooms">' + ['1', '1.5', '2', '2.5', '3', '3.5', '4+'].map(function (n) { return '<option' + (n === '2' ? ' selected' : '') + '>' + n + '</option>'; }).join('') + '</select></label>' +
      '<label>' + t('Year built', 'Año construida') + '<input type="text" name="Year built" inputmode="numeric" maxlength="4" placeholder="' + t('e.g. 1998', 'ej. 1998') + '"></label>' +
      '<label class="full">' + t('Finished square feet (all levels)', 'Pies cuadrados terminados (todos los niveles)') + '<input type="text" name="Finished sq ft" inputmode="numeric" maxlength="6" placeholder="' + t('e.g. 1,850', 'ej. 1,850') + '"></label>' +
    '</div>' +
    '<p class="hv-skip"><button type="button" class="hv-dunno">' + t("Not sure? Skip this and I'll look it up", 'No sé, sáltelo y yo lo busco') + '</button></p>' +
    '<p class="error" role="alert"></p>' +
    '<div class="nav-btns"><button type="button" class="btn-back back">' + t('← Back', '← Atrás') + '</button><button type="button" class="btn btn-gold next hv-next">' + t('Continue', 'Continuar') + '</button></div>';
  step1.after(fs);
  // renumber data-step on the steps after it
  form.querySelectorAll('fieldset.step, .step.sent').forEach(function (s, k) { s.setAttribute('data-step', String(k + 1)); });

  // Optional: home value updates by email (added to the contact step)
  var lastStep = [].slice.call(form.querySelectorAll('fieldset.step')).pop();
  var err0 = lastStep.querySelector('.error');
  if (err0) {
    var lab = document.createElement('label');
    lab.className = 'hv-optin';
    lab.innerHTML = '<input type="checkbox" name="Value updates" value="Yes"> <span>' + t("Email me my home's value every few months", 'Envíenme el valor de mi casa cada pocos meses') + '</span>';
    err0.before(lab);
  }

  var num = function (v) { return +String(v || '').replace(/[^0-9.]/g, '') || 0; };
  var skipped = false;
  function details() {
    var g = function (n) { var el = form.querySelector('[name="' + n + '"]'); return el ? el.value : ''; };
    return { type: g('Home type'), beds: num(g('Bedrooms')), baths: g('Bathrooms'), sqft: num(g('Finished sq ft')), year: num(g('Year built')), address: (g('Address') || '').trim() };
  }
  function valid(d) {
    var e = fs.querySelector('.error');
    if (!d.sqft || d.sqft < 400 || d.sqft > 15000) { e.textContent = t('Please enter the finished square feet (for example 1,850).', 'Escriba los pies cuadrados terminados (por ejemplo 1,850).'); return false; }
    if (d.year && (d.year < 1850 || d.year > new Date().getFullYear() + 1)) { e.textContent = t('Please check the year built.', 'Revise el año de construcción.'); return false; }
    e.textContent = ''; return true;
  }
  // Runs before site.js's own Continue handler (capture phase): only let them continue with good numbers
  fs.querySelector('.hv-next').addEventListener('click', function (e) {
    if (skipped) { skipped = false; job = null; jobKey = ''; return; }
    if (!valid(details())) { e.stopImmediatePropagation(); return; }
    start();
  }, true);
  fs.querySelector('.hv-dunno').addEventListener('click', function () {
    skipped = true; fs.querySelector('.error').textContent = '';
    fs.querySelector('[name="Finished sq ft"]').value = ''; fs.querySelector('[name="Year built"]').value = '';
    fs.querySelector('.hv-next').dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  // Enter key: go through the same check (and keep site.js from skipping it)
  fs.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.matches('input')) { e.preventDefault(); e.stopPropagation(); fs.querySelector('.hv-next').click(); }
  }, true);

  // ---------- the estimate ----------
  var job = null, jobKey = '';
  function start() {
    var d = details();
    if (!d.sqft) { job = null; return; }
    var key = JSON.stringify(d);
    if (key === jobKey && job) return;
    jobKey = key; job = estimate(d).catch(function () { return null; });
  }
  function locate(addr) {
    var q = addr + (/\b(sd|south dakota)\b/i.test(addr) ? '' : ', SD');
    return fetch(GEO + '?f=json&maxLocations=1&outFields=Score&SingleLine=' + encodeURIComponent(q)).then(function (r) { return r.json(); }).then(function (j) {
      var c = (j.candidates || [])[0];
      if (c && c.score >= 80 && c.location && Math.abs(c.location.y - 43.5) < 1 && Math.abs(c.location.x + 96.75) < 1) return [c.location.y, c.location.x];
      throw 0;
    }).catch(function () {
      var low = addr.toLowerCase();
      for (var k in TOWNS) if (low.indexOf(k) > -1) return TOWNS[k];
      return TOWNS['sioux falls'];
    });
  }
  function box(ll, miles) {
    var dy = miles / 69, dx = miles / (69 * Math.cos(ll[0] * Math.PI / 180));
    return [[ll[0] + dy, ll[1] - dx], [ll[0] + dy, ll[1] + dx], [ll[0] - dy, ll[1] + dx], [ll[0] - dy, ll[1] - dx]].map(function (p) { return p[0].toFixed(5) + ',' + p[1].toFixed(5); });
  }
  function dist(a, b) { var dy = (a[0] - b[0]) * 69, dx = (a[1] - b[1]) * 69 * Math.cos(a[0] * Math.PI / 180); return Math.sqrt(dx * dx + dy * dy); }
  function comps(ll, d, miles) {
    var q = new URLSearchParams();
    q.append('status', 'Active'); q.append('status', 'Pending');
    q.set('type', 'residential');
    if (d.type === 'House') q.set('subtype', 'SingleFamilyResidence');
    q.set('minbeds', Math.max(1, d.beds - 1)); if (d.beds < 6) q.set('maxbeds', d.beds + 1);
    q.set('minarea', Math.round(d.sqft * 0.7)); q.set('maxarea', Math.round(d.sqft * 1.35));
    box(ll, miles).forEach(function (p) { q.append('points', p); });
    q.set('limit', '50');
    return fetch(API + '?' + q.toString()).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (list) {
      return (list || []).filter(function (h) {
        var p = h.property || {};
        if (!h.listPrice || !p.area || p.area < 300) return false;
        if (d.type !== 'House' && p.subType === 'SingleFamilyResidence') return false;
        var ppsf = h.listPrice / p.area; return ppsf > 60 && ppsf < 600;
      });
    });
  }
  function estimate(d) {
    return locate(d.address).then(function (ll) {
      var tries = [1.5, 3, 6], i = 0;
      function next() {
        return comps(ll, d, tries[i]).then(function (list) {
          if (list.length >= 6 || i === tries.length - 1) return list;
          i++; return next();
        });
      }
      return next().then(function (list) {
        if (list.length < 4) return null;
        var pts = list.map(function (h) {
          var p = h.property || {}, g = h.geo || {};
          var w = 1;
          if (g.lat && g.lng) w /= 1 + dist(ll, [g.lat, g.lng]);
          w /= 1 + Math.abs(p.area - d.sqft) / d.sqft * 3;
          if (d.year && p.yearBuilt) w /= 1 + Math.abs(p.yearBuilt - d.year) / 15;
          if (p.bedrooms) w /= 1 + Math.abs(p.bedrooms - d.beds) * 0.3;
          return { v: h.listPrice / p.area, w: w };
        }).sort(function (a, b) { return a.v - b.v; });
        var tot = pts.reduce(function (s, p) { return s + p.w; }, 0), acc = 0, med = pts[0].v;
        for (var k = 0; k < pts.length; k++) { acc += pts[k].w; if (acc >= tot / 2) { med = pts[k].v; break; } }
        // homes usually sell a little under the asking price
        var value = d.sqft * med * 0.975;
        // how much the similar homes disagree decides how wide the range is
        var dev = pts.map(function (p) { return Math.abs(p.v - med) / med; }).sort(function (a, b) { return a - b; });
        var spread = Math.min(0.12, Math.max(0.06, dev[Math.floor(dev.length / 2)] * 0.8 + (list.length < 8 ? 0.02 : 0)));
        var r5 = function (v) { return Math.round(v / 5000) * 5000; };
        return { low: r5(value * (1 - spread)), high: r5(value * (1 + spread)), mid: Math.round(value / 1000) * 1000, n: list.length };
      });
    });
  }
  var money = function (v) { return '$' + Math.round(v).toLocaleString('en-US'); };

  // add the details + estimate to the lead (sheet, email, phone alert)
  var result = null;
  form.addEventListener('wizard:submit', function (e) {
    var fd = e.detail && e.detail.fd; if (!fd) return;
    var d = details(), home = d.sqft
      ? d.type + ' ' + d.beds + 'bd/' + d.baths + 'ba ' + d.sqft.toLocaleString('en-US') + ' sf' + (d.year ? ' built ' + d.year : '')
      : d.type + ' ' + d.beds + 'bd/' + d.baths + 'ba (size not given)';
    var est = result ? money(result.low) + ' – ' + money(result.high) + ' (from ' + result.n + ' similar homes for sale nearby)' : 'none shown';
    var wants = !!fd.get('Value updates');
    // The lead sheet keeps only ~60 characters of "Looking to", so the details go in the message (Notes column)
    if (wants) fd.set('Looking to', 'Value updates · ' + (fd.get('Looking to') || 'Home value'));
    fd.set('message', 'Address: ' + d.address + '\nHome details: ' + home + '\nInstant estimate shown: ' + est +
      (wants ? '\nWants home value updates by email: Yes' : ''));
    fd.set('Home details', home);
    fd.set('Instant estimate', est);
  });
  // when they reach the contact step, wait (briefly) for the estimate so it can go with the lead
  form.addEventListener('wizard:step', function (e) {
    if (e.detail && e.detail.step === lastStep && job) job.then(function (r) { result = r; });
  });
  form.addEventListener('wizard:sent', function () {
    var sent = form.querySelector('.step.sent'); if (!sent) return;
    var h3 = sent.querySelector('h3');
    var boxEl = document.createElement('div');
    boxEl.className = 'hv-result';
    var show = function (r) {
      if (!r) { boxEl.remove(); return; }
      boxEl.innerHTML = '<p class="hv-label">' + t('Your instant estimate', 'Su cálculo al instante') + '</p>' +
        '<p class="hv-range">' + money(r.low) + ' – ' + money(r.high) + '</p>' +
        '<p class="hv-basis">' + t('Based on ' + r.n + ' similar homes for sale near you.', 'Basado en ' + r.n + ' casas parecidas en venta cerca de usted.') + '</p>' +
        '<p class="hv-note">' + t("This is a quick estimate, not an appraisal. Updates, condition and recent sales can move the number, so my free report uses real recent sales near you.",
          'Esto es un cálculo rápido, no un avalúo. Las mejoras, la condición y las ventas recientes pueden cambiar el número, por eso mi reporte gratis usa ventas reales y recientes cerca de usted.') + '</p>';
    };
    if (h3) h3.after(boxEl); else sent.prepend(boxEl);
    if (result) show(result);
    else if (job) { boxEl.innerHTML = '<p class="hv-label">' + t('Working on your estimate…', 'Calculando su valor…') + '</p>'; job.then(show); }
    else boxEl.remove();
  });
})();
