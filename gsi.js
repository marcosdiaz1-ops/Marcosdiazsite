// "Continue with Google" for the listing-alert sign-up box on the search pages (EN + ES).
// When the sign-up box opens, Google's one-tap prompt offers the visitor's Google account, and a
// "Continue with Google" button sits at the top of the form. Choosing an account fills in their name and
// email; they still check the consent box and tap the button themselves.
// GOOGLE_CLIENT_ID: from Google Cloud → APIs & Services → Credentials → OAuth client ID (Web), with
// https://605homesearch.com as an authorized JavaScript origin. Empty = this feature stays off.
(function () {
  var GOOGLE_CLIENT_ID = '';
  var modal = document.getElementById('al'), form = document.getElementById('al-form');
  if (!GOOGLE_CLIENT_ID || !modal || !form) return;
  var ES = document.documentElement.lang === 'es';
  var ready = false, loading = false, prompted = false;

  var slot = document.createElement('div');
  slot.className = 'al-google';
  slot.innerHTML = '<div class="al-gbtn"></div><p class="al-or"><span>' + (ES ? 'o escriba sus datos' : 'or type your info') + '</span></p>';
  var nameLabel = form.querySelector('label[for="al-name"]');
  if (nameLabel) nameLabel.before(slot); else form.prepend(slot);
  slot.hidden = true;

  function decode(jwt) {
    try {
      var b = jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(decodeURIComponent(atob(b).split('').map(function (c) { return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2); }).join('')));
    } catch (e) { return null; }
  }
  function onCred(res) {
    var p = res && res.credential && decode(res.credential);
    if (!p || !p.email || p.email_verified === false) return;
    var n = document.getElementById('al-name'), em = document.getElementById('al-email');
    if (n && !n.value.trim()) n.value = p.name || [p.given_name, p.family_name].filter(Boolean).join(' ');
    if (em) em.value = p.email;
    var c = form.querySelector('[name="consent"]');
    var msg = document.getElementById('al-msg');
    if (msg) msg.textContent = ES ? 'Listo. Marque la casilla y toque el botón para activar sus alertas.' : 'Got it. Check the box and tap the button to turn on your alerts.';
    if (c) c.focus();
    if (window.gtag) gtag('event', 'google_one_tap');
  }
  function init() {
    if (ready || !window.google || !google.accounts || !google.accounts.id) return;
    google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: onCred, auto_select: false, cancel_on_tap_outside: true, context: 'signup', itp_support: true, use_fedcm_for_prompt: true });
    google.accounts.id.renderButton(slot.querySelector('.al-gbtn'), { theme: 'outline', size: 'large', text: 'continue_with', shape: 'pill', width: 280, locale: ES ? 'es' : 'en' });
    ready = true; slot.hidden = false;
  }
  function load(cb) {
    if (ready) return cb();
    if (loading) return;
    loading = true;
    var s = document.createElement('script');
    s.src = 'https://accounts.google.com/gsi/client' + (ES ? '?hl=es' : '');
    s.async = true; s.onload = function () { init(); cb(); };
    document.head.appendChild(s);
  }
  // when the sign-up box opens: show the button, and offer one-tap once per visit
  new MutationObserver(function () {
    if (!modal.classList.contains('open') || form.hidden) return;
    load(function () {
      if (!ready || prompted) return;
      prompted = true;
      try { google.accounts.id.prompt(); } catch (e) {}
    });
  }).observe(modal, { attributes: true, attributeFilter: ['class'] });
})();
