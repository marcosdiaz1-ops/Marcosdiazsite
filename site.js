// Shared site behavior for 605homesearch.com (English + Spanish pages)
(function () {
  const ES = (document.documentElement.lang || 'en').toLowerCase().startsWith('es');
  const T = ES ? {
    step: (n, t) => 'Paso <b>' + n + '</b> de ' + t,
    sent: 'Enviado',
    sending: 'Enviando…',
    retry: 'Intentar de nuevo',
    need: label => 'Por favor agregue su ' + label + '.',
    fail: 'Lo sentimos, su mensaje no se envió. Inténtelo de nuevo o llame/envíe un texto al <a href="tel:+16058389140">605-838-9140</a>.',
    timeout: 'tiempo agotado',
    showReview: n => 'Mostrar reseña ' + n
  } : {
    step: (n, t) => 'Step <b>' + n + '</b> of ' + t,
    sent: 'Sent',
    sending: 'Sending…',
    retry: 'Try Again',
    need: label => 'Please add your ' + label + '.',
    fail: 'Sorry, your message didn\'t go through. Please try again, or call/text <a href="tel:+16058389140">605-838-9140</a>.',
    timeout: 'timed out',
    showReview: n => 'Show review ' + n
  };

  // Footer year
  document.querySelectorAll('.year').forEach(el => { el.textContent = new Date().getFullYear(); });

  // Header: solid after scrolling (always solid on pages without a photo hero)
  const header = document.getElementById('header');
  if (header) {
    const solid = document.body.classList.contains('subpage');
    const onScroll = () => header.classList.toggle('scrolled', solid || window.scrollY > 40);
    onScroll(); window.addEventListener('scroll', onScroll, { passive: true });
    const btn = header.querySelector('.menu-btn'), links = header.querySelector('.links');
    if (btn && links) {
      btn.addEventListener('click', () => {
        const open = links.classList.toggle('open');
        header.classList.toggle('menu-open', open);
        btn.setAttribute('aria-expanded', open);
      });
      links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => { links.classList.remove('open'); header.classList.remove('menu-open'); }));
    }
  }

  // Lead form: one question per step, Continue after selecting, send in background
  (function () {
    const form = document.getElementById('leadForm');
    if (!form) return;
    const steps = [...form.querySelectorAll('fieldset.step')];
    const sent = form.querySelector('.sent');
    const bar = form.querySelector('.progress span');
    const count = form.querySelector('.step-count');
    let i = 0;
    const show = n => {
      form.classList.toggle('going-back', n < i);
      steps.forEach((s, k) => s.classList.toggle('active', k === n));
      bar.style.width = ((n + 1) / steps.length * 100) + '%';
      count.innerHTML = T.step(n + 1, steps.length);
      i = n;
      if (n === steps.length - 1) setTimeout(() => form.querySelector('[name="Name"]').focus({ preventScroll: true }), 450);
    };
    steps.forEach((step, k) => {
      const next = step.querySelector('.next');
      if (!next) return;
      const texts = [...step.querySelectorAll('input[type=text]')];
      const ready = () => step.querySelector('input:checked') || (texts.length && texts.every(t => t.value.trim().length > 3));
      step.querySelectorAll('input[type=radio]').forEach(r => r.addEventListener('change', () => { next.disabled = false; }));
      texts.forEach(t => {
        t.addEventListener('input', () => { next.disabled = !ready(); });
        t.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (ready()) show(k + 1); } });
      });
      next.addEventListener('click', () => { if (ready()) show(k + 1); });
    });
    form.querySelectorAll('.back').forEach(b => b.addEventListener('click', () => show(i - 1)));
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const last = steps[steps.length - 1];
      const err = last.querySelector('.error');
      for (const el of last.querySelectorAll('[required]')) {
        if (!el.checkValidity()) { err.textContent = T.need(el.closest('label').firstChild.textContent.trim().toLowerCase()); el.focus(); return; }
      }
      err.textContent = '';
      const btn = last.querySelector('button[type=submit]');
      btn.disabled = true; btn.textContent = T.sending;
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 15000);
      const fd = new FormData(form);
      fd.set('Language', ES ? 'Español' : 'English');
      if (form.dataset.kind === 'home-value') fd.set('Looking to', 'Home value: ' + (fd.get('Address') || '').trim());
      // Lead tracker + instant alert + auto-reply (Google Apps Script), sent alongside the email
      const sheetUrl = form.dataset.sheet;
      if (sheetUrl) {
        fetch(sheetUrl, { method: 'POST', mode: 'no-cors', body: new URLSearchParams(fd), keepalive: true }).catch(() => {});
      }
      try {
        const res = await fetch(form.action, {
          method: 'POST', headers: { 'Accept': 'application/json' }, body: fd, signal: ctrl.signal
        });
        clearTimeout(timer);
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.success !== true) throw new Error(data.message || 'send failed');
        const first = form.querySelector('[name="Name"]').value.trim().split(' ')[0];
        sent.querySelector('.sent-name').textContent = first ? ', ' + first : '';
        steps.forEach(s => s.classList.remove('active'));
        bar.style.width = '100%'; count.textContent = T.sent;
        sent.classList.add('active');
      } catch (e2) {
        clearTimeout(timer);
        btn.disabled = false; btn.textContent = T.retry;
        const why = e2 && e2.name === 'AbortError' ? T.timeout : (e2 && e2.message ? e2.message : 'unknown');
        console.warn('Lead form error:', why);
        err.innerHTML = T.fail + '<br><small class="why">(' + String(why).replace(/</g, '') + ')</small>';
      }
    });
    show(0);
  })();

  // Mobile: sticky Text / Call bar
  (function () {
    const bar = document.createElement('div');
    bar.className = 'mobile-cta';
    bar.innerHTML = '<a href="sms:+16058389140" class="m-text">' +
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M4 3h16a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/></svg>' +
      (ES ? 'Enviar texto' : 'Text Marcos') + '</a>' +
      '<a href="tel:+16058389140" class="m-call">' +
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>' +
      (ES ? 'Llamar' : 'Call') + '</a>';
    document.body.appendChild(bar);
    document.body.classList.add('has-mobile-cta');
  })();

  // Reviews slider: one at a time, auto-advance
  (function () {
    const slider = document.querySelector('.review-slider');
    if (!slider) return;
    const slides = [...slider.querySelectorAll('.review')];
    const dotsBox = slider.querySelector('.dots');
    let i = 0, timer = null;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const dots = slides.map((_, k) => {
      const d = document.createElement('button');
      d.type = 'button'; d.className = 'dot'; d.setAttribute('aria-label', T.showReview(k + 1));
      d.addEventListener('click', () => { go(k); restart(); });
      dotsBox.appendChild(d); return d;
    });
    function go(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach((s, k) => { s.classList.toggle('active', k === i); s.setAttribute('aria-hidden', k !== i); });
      dots.forEach((d, k) => d.classList.toggle('active', k === i));
    }
    function restart() { clearInterval(timer); if (!reduce) timer = setInterval(() => go(i + 1), 7000); }
    slider.querySelector('.prev').addEventListener('click', () => { go(i - 1); restart(); });
    slider.querySelector('.next').addEventListener('click', () => { go(i + 1); restart(); });
    slider.addEventListener('mouseenter', () => clearInterval(timer));
    slider.addEventListener('mouseleave', restart);
    let x0 = null;
    slider.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
    slider.addEventListener('touchend', e => {
      if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) { go(i + (dx < 0 ? 1 : -1)); restart(); }
    });
    go(0); restart();
  })();

  // Mortgage calculator
  (function () {
    const calc = document.getElementById('mortgageCalc');
    if (!calc) return;
    const $ = n => calc.querySelector('[name="' + n + '"]');
    const money = v => '$' + Math.round(v).toLocaleString(ES ? 'es-US' : 'en-US');
    const num = el => parseFloat(String(el.value).replace(/[^0-9.]/g, '')) || 0;
    const out = k => calc.querySelector('[data-out="' + k + '"]');
    function update() {
      const price = num($('price'));
      const downPct = Math.min(num($('down')), 100);
      const rate = num($('rate'));
      const years = num($('term')) || 30;
      const taxPct = num($('tax'));
      const ins = num($('insurance'));
      const hoa = num($('hoa'));
      const loan = Math.max(price * (1 - downPct / 100), 0);
      const n = years * 12, r = rate / 100 / 12;
      const pi = loan === 0 ? 0 : (r === 0 ? loan / n : loan * r / (1 - Math.pow(1 + r, -n)));
      const tax = price * taxPct / 100 / 12;
      const insM = ins / 12;
      const total = pi + tax + insM + hoa;
      out('total').textContent = money(total);
      out('pi').textContent = money(pi);
      out('tax').textContent = money(tax);
      out('ins').textContent = money(insM);
      out('hoa').textContent = money(hoa);
      out('loan').textContent = money(loan);
      out('downAmt').textContent = money(price * downPct / 100);
      const parts = [pi, tax, insM, hoa];
      const bars = calc.querySelectorAll('.calc-bar span');
      bars.forEach((b, k) => { b.style.width = (total ? parts[k] / total * 100 : 0) + '%'; });
    }
    calc.addEventListener('input', update);
    calc.addEventListener('change', update);
    update();
  })();
})();
