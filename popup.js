// "New listings by email" pop-up (EN + ES). Loaded on every page by site.js.
// - Shows once per visitor: after ~40 seconds on a page, or after scrolling about halfway (never in the first 12 seconds).
// - Never shows to people already signed up for alerts, on pages where they're already filling out a form
//   (search, home value, ad landing pages, thank-you), or while they're typing in a form.
// - Closing it (X, "No thanks", Esc) hides it for 30 days. Signing up hides it for good.
// - Sign-ups go to the same Listing Alert Leads sheet as the search page alerts, with Source "Pop-up: <page>".
//   On a town page the alert is set to that town; everywhere else it covers the Sioux Falls area.
(function () {
  var ALERTS_URL = 'https://script.google.com/macros/s/AKfycbxklqP-b5JNN1e2hsuwLXQvC0P6_4ZmJBORJLDojLWMwqWiUx5JFn0oiKDVXvu4c-6-/exec';
  var AREA = '43.80000,-97.05000|43.80000,-96.45000|43.25000,-96.45000|43.25000,-97.05000';
  var SKIP = /^\/(es\/)?(search|buscar-casas|search-preview|buscar-casas-preview|home-value|valor-de-casa|lp|give-me-five|dame-cinco)(\/|$)|thank-you|gracias/;
  var path = location.pathname;
  if (SKIP.test(path)) return;
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  if (get('mdAlertId') || get('mdPopDone')) return;
  var snooze = +get('mdPopSnooze') || 0;
  if (snooze && Date.now() < snooze) return;

  var ES = /^es/i.test(document.documentElement.lang || '') || /^\/es\//.test(path);
  var t = function (en, es) { return ES ? es : en; };
  var feat = document.getElementById('featured');
  var city = feat && feat.getAttribute('data-cities');
  var pts = feat && feat.getAttribute('data-points');
  var townName = '';
  if (city || pts) {
    townName = city || '';
    if (pts) { var last = (document.querySelector('.tp-hero .crumbs') || {}).textContent || ''; townName = last.split('/').pop().trim() || 'Sioux Falls'; }
  }
  var where = townName || 'Sioux Falls';
  var started = Date.now(), shown = false, typing = false;

  document.addEventListener('focusin', function (e) { if (e.target.closest && e.target.closest('form') && !e.target.closest('.np')) typing = true; });

  function ok() { return !shown && !typing && Date.now() - started > 12000 && !document.querySelector('.cw-open, .chat-open, dialog[open]'); }
  function tryShow() { if (ok()) show(); }
  var timer = setTimeout(tryShow, 40000);
  var retry = setInterval(function () { if (shown) return clearInterval(retry); if (Date.now() - started > 40000) tryShow(); }, 5000);
  window.addEventListener('scroll', function () {
    var h = document.documentElement.scrollHeight - innerHeight;
    if (h > 400 && scrollY / h > 0.5) tryShow();
  }, { passive: true });

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) { var r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); });
  }

  function show() {
    shown = true; clearTimeout(timer); clearInterval(retry);
    var box = document.createElement('aside');
    box.className = 'np';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-labelledby', 'np-h');
    box.innerHTML =
      '<button type="button" class="np-x" aria-label="' + t('Close', 'Cerrar') + '">×</button>' +
      '<p class="np-eye">' + t('Free listing alerts', 'Alertas gratis') + '</p>' +
      '<h2 id="np-h"></h2>' +
      '<p class="np-sub">' + t('Get new homes in your inbox the day they hit the market, plus price drops. Free, no spam, unsubscribe anytime.', 'Reciba casas nuevas en su correo el día que salen al mercado, y bajas de precio. Gratis, sin spam, cancele cuando quiera.') + '</p>' +
      '<form class="np-f" novalidate>' +
        '<div class="np-row"><input name="name" autocomplete="given-name" placeholder="' + t('First name', 'Nombre') + '" aria-label="' + t('First name', 'Nombre') + '" required>' +
        '<input name="email" type="email" autocomplete="email" placeholder="' + t('Email', 'Correo') + '" aria-label="' + t('Email', 'Correo') + '" required></div>' +
        '<input name="botcheck" class="np-hp" tabindex="-1" autocomplete="off" aria-hidden="true">' +
        '<button type="submit" class="np-go">' + t('Send me new listings', 'Envíenme casas nuevas') + '</button>' +
        '<p class="np-fine">' + t('By signing up you agree to get listing emails from Marcos Diaz. Unsubscribe anytime. ', 'Al registrarse acepta recibir correos de casas de Marcos Diaz. Cancele cuando quiera. ') + '<a href="/privacy.html" target="_blank">' + t('Privacy', 'Privacidad') + '</a></p>' +
        '<p class="np-msg" role="status"></p>' +
      '</form>' +
      '<button type="button" class="np-no">' + t('No thanks', 'No, gracias') + '</button>';
    box.querySelector('#np-h').textContent = t('New homes in ' + where + ', first.', 'Casas nuevas en ' + where + ', primero.');
    document.body.appendChild(box);
    requestAnimationFrame(function () { box.classList.add('in'); });
    if (window.gtag) gtag('event', 'popup_shown', { page: path });

    function close(days) {
      box.classList.remove('in');
      setTimeout(function () { box.remove(); }, 400);
      set('mdPopSnooze', String(Date.now() + days * 864e5));
      document.removeEventListener('keydown', esc);
    }
    function esc(e) { if (e.key === 'Escape') close(30); }
    document.addEventListener('keydown', esc);
    box.querySelector('.np-x').onclick = function () { close(30); };
    box.querySelector('.np-no').onclick = function () { close(30); };

    var f = box.querySelector('form'), msg = box.querySelector('.np-msg'), btn = box.querySelector('.np-go');
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = f.name.value.trim(), email = f.email.value.trim();
      if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { msg.textContent = t('Please add your first name and email.', 'Escriba su nombre y correo.'); return; }
      var id = uuid();
      var d = new URLSearchParams();
      d.set('id', id); d.set('name', name); d.set('email', email);
      if (city) d.set('q', city); else d.set('points', pts || AREA);
      d.set('freq', 'Daily'); d.set('lang', ES ? 'es' : 'en'); d.set('consent', 'yes');
      d.set('source', 'Pop-up: ' + path); d.set('botcheck', f.botcheck.value);
      btn.disabled = true; btn.textContent = t('Sending…', 'Enviando…');
      fetch(ALERTS_URL, { method: 'POST', mode: 'no-cors', body: d }).then(function () {
        set('mdAlertId', id); set('mdPopDone', '1');
        f.innerHTML = '<p class="np-done"><span aria-hidden="true">✓</span> ' + t("You're in, " + name + "! Check your inbox for your first homes.", '¡Listo, ' + name + '! Revise su correo para ver sus primeras casas.') + '</p>';
        box.querySelector('.np-no').textContent = t('Close', 'Cerrar');
        box.querySelector('.np-no').onclick = function () { box.classList.remove('in'); setTimeout(function () { box.remove(); }, 400); };
        if (window.gtag) gtag('event', 'generate_lead', { method: 'popup' });
        if (window.fbq) fbq('track', 'Lead', { content_name: 'Listing alerts pop-up' });
      }).catch(function () {
        btn.disabled = false; btn.textContent = t('Send me new listings', 'Envíenme casas nuevas');
        msg.textContent = t('Something went wrong. Please try again, or call/text 605-838-9140.', 'Algo falló. Intente de nuevo o llame al 605-838-9140.');
      });
    });
  }
})();
