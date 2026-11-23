// Visitor tracking for 605homesearch.com: Google Analytics 4 + Meta (Facebook/Instagram) Pixel.
// Loaded on every page by site.js. Paste the two IDs below. If an ID is left empty, that tool stays off.
//
//   GA_ID:    Google Analytics → Admin → Data streams → your site → "Measurement ID" (looks like G-AB12CD34EF)
//   PIXEL_ID: Meta Events Manager → Data sources → your Pixel/dataset → "ID" (15–16 digits)
//
// Lead events sent to both tools:
//   generate_lead / Lead       → contact form, home value form, guide download, market update signup,
//                                listing alert signup, "ask about this home", ad landing pages
//   schedule_showing / Schedule → a showing booked through Calendly
//   contact_click / Contact    → someone taps to call, text or email Marcos
(function () {
  var GA_ID = '';
  var PIXEL_ID = '';

  if (window.__mdAnalytics) return;
  window.__mdAnalytics = true;

  var META = { generate_lead: 'Lead', schedule_showing: 'Schedule', contact_click: 'Contact' };

  // Google Analytics
  window.dataLayer = window.dataLayer || [];
  function ga() { window.dataLayer.push(arguments); }
  if (GA_ID) {
    var s = document.createElement('script');
    s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    ga('js', new Date());
    ga('config', GA_ID);
  }

  // Meta Pixel (standard snippet)
  if (PIXEL_ID) {
    !function (f, b, e, v, n, t, s) { if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
      if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = []; t = b.createElement(e); t.async = !0;
      t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s); }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    window.fbq('init', PIXEL_ID);
    window.fbq('track', 'PageView');
  }

  // One gtag() for the whole site: sends to Google, and copies lead events to Meta
  var last = {};
  window.gtag = function () {
    var a = arguments;
    if (a[0] === 'event') {
      var key = a[1] + '|' + ((a[2] && a[2].method) || '');
      if (last[key] && Date.now() - last[key] < 3000) return; // ignore double fires
      last[key] = Date.now();
      if (META[a[1]] && window.fbq) window.fbq('track', META[a[1]], { content_name: (a[2] && a[2].method) || a[1] });
    }
    if (GA_ID) ga.apply(null, a);
  };
  window.mdTrack = function (name, method) { window.gtag('event', name, { method: method || name }); };

  // Main contact / home value forms (site.js wizard) — fires only after the lead is sent
  document.addEventListener('wizard:sent', function (e) {
    var f = e.target, kind = (f && f.dataset && f.dataset.kind) || 'contact';
    window.mdTrack('generate_lead', kind);
  }, true);

  // Showing booked in Calendly
  window.addEventListener('message', function (e) {
    if (/calendly\.com$/.test(String(e.origin).replace(/^https?:\/\//, '')) && e.data && e.data.event === 'calendly.event_scheduled') {
      window.mdTrack('schedule_showing', 'calendly');
    }
  });

  // Taps on call / text / email links
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="tel:"],a[href^="sms:"],a[href^="mailto:"]');
    if (a) window.mdTrack('contact_click', a.getAttribute('href').split(':')[0]);
  }, true);
})();
