// Website chat helper (EN + ES). Loaded on every page by site.js (not on the /lp/ ad pages).
// - Quick-answer buttons work instantly with no AI.
// - Typed questions go to the "chat" Cloudflare Worker (tools/chat-worker.js), which uses Cloudflare's free AI.
//   If that's not set up yet or is busy, the helper says so and offers Text Marcos / Leave my number.
// - "Leave my number" sends a lead (with the chat) to the Website Leads sheet + email, like the other forms.
(function () {
  if (window.__mdChat) return; window.__mdChat = true;
  var CHAT_API = 'https://chat.marcosdiaz1.workers.dev';
  var SHEET = 'https://script.google.com/macros/s/AKfycbw5PdoEEaGDAquTmKqO_1SkhtTaJG3G0584Xy4VIqG74FsaaH-tnxYpeIdrqTcCjZ0w/exec';
  var W3F = 'd0023d26-ed18-4970-8a35-c3de9e5f7e6c';
  var ES = document.documentElement.lang === 'es';
  function t(en, es) { return ES ? es : en; }
  var P = ES ? '/es/' : '/';
  var KEY = 'mdChat';

  var QUICK = ES ? [
    ['¿Cuánto necesito para el pago inicial?', 'Menos de lo que mucha gente cree. Algunos préstamos piden de 3% a 3.5%, los préstamos VA pueden ser con $0 para veteranos que califiquen, y hay programas de ayuda como Give Me Five. Vea /es/ayuda-pago-inicial/ y un prestamista le confirma para qué califica.'],
    ['¿Cuánto vale mi casa?', 'Puede ver un cálculo al instante en /es/valor-de-casa/. Marcos también le prepara un reporte gratis con ventas reales y recientes cerca de usted.'],
    ['Quiero ver una casa', 'Busque casas en /es/buscar-casas/ y toque "Pedir una visita" en la casa que le guste. O mándele un texto a Marcos al 605-838-9140.'],
    ['¿Habla español?', 'Sí. Marcos es bilingüe y le ayuda en todo el proceso en español o en inglés, desde la primera llamada hasta el cierre.']
  ] : [
    ['How much do I need down?', 'Less than many people think. Some loans need 3% to 3.5% down, VA loans can be $0 down for eligible veterans, and programs like Give Me Five help first-time buyers. See /down-payment-assistance/ and a lender can confirm what you qualify for.'],
    ["What's my home worth?", 'You can get an instant estimate at /home-value/. Marcos can also put together a free report based on real recent sales near you.'],
    ['I want to see a home', 'Search homes at /search/ and tap "Request a showing" on any home you like. Or text Marcos at 605-838-9140.'],
    ['How are buyer agents paid?', "Buyers now sign a written agreement with their agent before touring homes, and it spells out how the agent is paid. Often the seller ends up covering some or all of it, but it's negotiable. Marcos walks you through your options first."]
  ];

  var state = { open: false, msgs: [] };
  try { var saved = JSON.parse(sessionStorage.getItem(KEY) || 'null'); if (saved && Array.isArray(saved.msgs)) state.msgs = saved.msgs.slice(-30); } catch (e) {}
  function save() { try { sessionStorage.setItem(KEY, JSON.stringify({ msgs: state.msgs.slice(-30) })); } catch (e) {} }
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  // turn site paths and the phone number into links
  function linkify(s) {
    return esc(s)
      .replace(/(^|[\s(])((?:\/es)?\/[a-z0-9\-\/]*(?:\.html)?(?:#[a-z]+)?)(?=[\s).,!?]|$)/gi, function (m, a, path) {
        if (path.length < 2) return m;
        var clean = path.replace(/[.,]$/, '');
        return a + '<a href="' + clean + '">' + clean.replace(/^\/es\//, '/es/') + '</a>';
      })
      .replace(/605-838-9140/g, '<a href="sms:+16058389140">605-838-9140</a>')
      .replace(/\n/g, '<br>');
  }

  // ---------- markup ----------
  var root = document.createElement('div');
  root.className = 'mdc';
  root.innerHTML =
    '<button type="button" class="mdc-bubble" aria-expanded="false" aria-controls="mdc-panel">' +
      '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path fill="currentColor" d="M4 3h16a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm3 7a1.3 1.3 0 1 0 0 .01zm5 0a1.3 1.3 0 1 0 0 .01zm5 0a1.3 1.3 0 1 0 0 .01z"/></svg>' +
      '<span class="mdc-bubble-txt">' + t('Questions?', '¿Preguntas?') + '</span></button>' +
    '<section class="mdc-panel" id="mdc-panel" role="dialog" aria-label="' + t('Chat with Marcos\'s assistant', 'Chat con el asistente de Marcos') + '" hidden>' +
      '<header class="mdc-head"><img src="/images/logo.svg" alt="" width="30" height="30">' +
        '<div><strong>' + t("Marcos's assistant", 'Asistente de Marcos') + '</strong><small>' + t('Automated · English & Español', 'Automático · Español & English') + '</small></div>' +
        '<button type="button" class="mdc-x" aria-label="' + t('Close chat', 'Cerrar chat') + '">×</button></header>' +
      '<div class="mdc-log" aria-live="polite"></div>' +
      '<div class="mdc-quick"></div>' +
      '<form class="mdc-lead" hidden novalidate>' +
        '<p class="mdc-lead-t">' + t("Leave your number and Marcos will text you back, usually the same day.", 'Deje su número y Marcos le escribe, normalmente el mismo día.') + '</p>' +
        '<input type="text" name="Name" placeholder="' + t('First & last name', 'Nombre y apellido') + '" autocomplete="name" required>' +
        '<input type="tel" name="Phone" placeholder="' + t('Phone', 'Teléfono') + '" autocomplete="tel" required>' +
        '<input type="email" name="email" placeholder="' + t('Email (optional)', 'Correo (opcional)') + '" autocomplete="email">' +
        '<p class="mdc-fine">' + t('By sending, you agree that Marcos Diaz may contact you by call, text or email at the phone and email you gave, which may include automated messages. Consent is not required to buy or sell a home. Message and data rates may apply. Reply STOP to opt out of texts.',
          'Al enviar, acepta que Marcos Diaz le contacte por llamada, mensaje de texto o correo al teléfono y correo que proporcionó, lo cual puede incluir mensajes automatizados. Su consentimiento no es requisito para comprar o vender una casa. Pueden aplicar tarifas de mensajes y datos. Responda STOP para dejar de recibir textos.') + '</p>' +
        '<p class="mdc-err" role="alert"></p>' +
        '<div class="mdc-lead-btns"><button type="button" class="mdc-cancel">' + t('Cancel', 'Cancelar') + '</button><button type="submit" class="mdc-send-lead">' + t('Send', 'Enviar') + '</button></div>' +
      '</form>' +
      '<form class="mdc-ask"><label class="sr-only" for="mdc-in">' + t('Type your question', 'Escriba su pregunta') + '</label>' +
        '<input id="mdc-in" type="text" maxlength="600" autocomplete="off" placeholder="' + t('Type a question…', 'Escriba su pregunta…') + '">' +
        '<button type="submit" aria-label="' + t('Send', 'Enviar') + '"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M3 20.5 21 12 3 3.5 3 10l12 2-12 2z"/></svg></button></form>' +
      '<div class="mdc-foot"><a href="sms:+16058389140" class="mdc-text">' + t('Text Marcos', 'Texto a Marcos') + '</a><button type="button" class="mdc-num">' + t('Leave my number', 'Dejar mi número') + '</button></div>' +
      '<p class="mdc-disc">' + t("Automated answers can be wrong. For anything important, check with Marcos.", 'Las respuestas automáticas pueden tener errores. Para algo importante, consulte con Marcos.') + '</p>' +
    '</section>';
  document.body.appendChild(root);

  var $ = function (s) { return root.querySelector(s); };
  var bubble = $('.mdc-bubble'), panel = $('.mdc-panel'), log = $('.mdc-log'), quick = $('.mdc-quick'), ask = $('.mdc-ask'), input = $('#mdc-in'), lead = $('.mdc-lead');

  function add(role, text, extra) {
    var d = document.createElement('div');
    d.className = 'mdc-msg ' + (role === 'user' ? 'me' : 'bot') + (extra ? ' ' + extra : '');
    d.innerHTML = role === 'user' ? esc(text) : linkify(text);
    log.appendChild(d); log.scrollTop = log.scrollHeight;
    return d;
  }
  function render() {
    log.innerHTML = '';
    add('assistant', t("Hi! I'm Marcos's assistant. Ask me about buying, selling, or homes around Sioux Falls, or tap a question below.",
      '¡Hola! Soy el asistente de Marcos. Pregúnteme sobre comprar, vender o casas en Sioux Falls, o toque una pregunta abajo.'));
    state.msgs.forEach(function (m) { add(m.role, m.content); });
    quick.innerHTML = QUICK.map(function (q, i) { return '<button type="button" data-q="' + i + '">' + esc(q[0]) + '</button>'; }).join('');
    quick.hidden = state.msgs.length > 2;
  }
  function openChat(on) {
    state.open = on; panel.hidden = !on; bubble.setAttribute('aria-expanded', String(on));
    root.classList.toggle('open', on);
    if (on) {
      if (!log.childNodes.length) render();
      setTimeout(function () { if (window.matchMedia('(min-width: 700px)').matches) input.focus(); }, 50);
      if (window.gtag) gtag('event', 'chat_open');
    }
  }
  bubble.addEventListener('click', function () { openChat(!state.open); });
  $('.mdc-x').addEventListener('click', function () { openChat(false); bubble.focus(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && state.open) openChat(false); });

  quick.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-q]'); if (!b) return;
    var q = QUICK[+b.dataset.q];
    state.msgs.push({ role: 'user', content: q[0] }); add('user', q[0]);
    state.msgs.push({ role: 'assistant', content: q[1] }); add('assistant', q[1]);
    save(); quick.hidden = true;
  });

  var busy = false;
  ask.addEventListener('submit', function (e) {
    e.preventDefault();
    var q = input.value.trim(); if (!q || busy) return;
    input.value = ''; quick.hidden = true;
    state.msgs.push({ role: 'user', content: q }); add('user', q); save();
    busy = true;
    var typing = add('assistant', '…', 'typing');
    var ctrl = new AbortController(), timer = setTimeout(function () { ctrl.abort(); }, 20000);
    fetch(CHAT_API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctrl.signal,
      body: JSON.stringify({ lang: ES ? 'es' : 'en', page: location.pathname, messages: state.msgs.slice(-12) }) })
      .then(function (r) { return r.json().then(function (j) { if (!r.ok || !j.reply) throw 0; return j.reply; }); })
      .then(function (reply) { typing.remove(); state.msgs.push({ role: 'assistant', content: reply }); add('assistant', reply); save(); })
      .catch(function () {
        typing.remove();
        add('assistant', t("Sorry, I can't answer that right now. Text Marcos at 605-838-9140, or tap \"Leave my number\" and he'll get back to you.",
          'Perdón, ahorita no puedo contestar eso. Mándele un texto a Marcos al 605-838-9140, o toque "Dejar mi número" y él le contesta.'));
      })
      .then(function () { clearTimeout(timer); busy = false; });
  });

  // ---------- leave my number ----------
  $('.mdc-num').addEventListener('click', function () { lead.hidden = false; ask.hidden = true; lead.querySelector('[name=Name]').focus(); log.scrollTop = log.scrollHeight; });
  $('.mdc-cancel').addEventListener('click', function () { lead.hidden = true; ask.hidden = false; });
  lead.addEventListener('submit', function (e) {
    e.preventDefault();
    var err = lead.querySelector('.mdc-err');
    var name = lead.Name.value.trim(), phone = lead.Phone.value.trim(), email = lead.email.value.trim();
    if (name.length < 2) { err.textContent = t('Please enter your name.', 'Escriba su nombre.'); return; }
    if (phone.replace(/\D/g, '').length < 10) { err.textContent = t('Please enter a 10-digit phone number.', 'Escriba un teléfono de 10 dígitos.'); return; }
    if (email && !lead.email.checkValidity()) { err.textContent = t('Please check your email.', 'Revise su correo.'); return; }
    err.textContent = '';
    var chat = state.msgs.slice(-12).map(function (m) { return (m.role === 'user' ? 'Them: ' : 'Bot: ') + m.content; }).join('\n');
    var firstQ = (state.msgs.filter(function (m) { return m.role === 'user'; })[0] || {}).content || '';
    var fd = new FormData();
    fd.set('access_key', W3F);
    fd.set('subject', 'Website chat: ' + name + ' wants a text back');
    fd.set('from_name', 'Marcos Diaz Website');
    fd.set('Name', name); fd.set('Phone', phone); fd.set('email', email || '');
    fd.set('Looking to', 'Chat' + (firstQ ? ': ' + firstQ.slice(0, 80) : ''));
    fd.set('Timeline', 'Chat helper');
    fd.set('Language', ES ? 'Español' : 'English');
    fd.set('message', 'From the chat helper on ' + location.pathname + (chat ? '\n\n' + chat : ''));
    var btn = lead.querySelector('.mdc-send-lead'); btn.disabled = true; btn.textContent = t('Sending…', 'Enviando…');
    fetch(SHEET, { method: 'POST', mode: 'no-cors', body: new URLSearchParams(fd), keepalive: true }).catch(function () {});
    fetch('https://api.web3forms.com/submit', { method: 'POST', headers: { Accept: 'application/json' }, body: fd }).catch(function () {}).then(function () {
      lead.hidden = true; ask.hidden = false; btn.disabled = false; btn.textContent = t('Send', 'Enviar');
      var first = name.split(' ')[0];
      var msg = t('Thanks, ' + first + "! Marcos got your number and will text you soon, usually the same day.", '¡Gracias, ' + first + '! Marcos recibió su número y le escribe pronto, normalmente el mismo día.');
      state.msgs.push({ role: 'assistant', content: msg }); add('assistant', msg); save();
      if (window.gtag) gtag('event', 'generate_lead', { method: 'chat' });
    });
  });
})();
