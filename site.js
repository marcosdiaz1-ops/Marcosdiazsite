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
      // Give Me Five quiz: work out the result from the flagged answers
      let gm5 = null;
      if (form.dataset.kind === 'gm5') {
        const flags = [...form.querySelectorAll('input[type=radio]:checked')].map(r => r.dataset.flag).filter(Boolean);
        const hard = ['owned', 'notprimary'];
        const tier = flags.some(f => hard.includes(f)) ? 'no' : (flags.length ? 'check' : 'fit');
        gm5 = { tier, flags };
        const label = { fit: 'strong fit', check: 'check', no: 'may not fit' }[tier];
        fd.set('Looking to', 'Give Me Five: ' + label + (flags.length ? ' (' + flags.join(', ') + ')' : ''));
      }
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
        if (gm5) {
          sent.querySelectorAll('.gm5-tier').forEach(t => { t.hidden = t.dataset.tier !== gm5.tier; });
          sent.querySelectorAll('.gm5-flags li').forEach(li => { li.hidden = !gm5.flags.includes(li.dataset.flag); });
        }
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

  // Affordability calculator
  (function () {
    const c = document.getElementById('affordCalc');
    if (!c) return;
    const $ = n => c.querySelector('[name="' + n + '"]');
    const num = el => parseFloat(String(el.value).replace(/[^0-9.]/g, '')) || 0;
    const money = v => '$' + Math.round(Math.max(v, 0)).toLocaleString(ES ? 'es-US' : 'en-US');
    const out = k => c.querySelector('[data-out="' + k + '"]');
    function update() {
      const income = num($('income')), debts = num($('debts')), down = num($('down'));
      const rate = num($('rate')), dti = num($('dti')) / 100, taxPct = num($('tax')) / 100, ins = num($('insurance'));
      const maxPay = income / 12 * dti - debts;          // max total monthly housing payment
      const r = rate / 100 / 12, n = 360;
      const k = r === 0 ? 1 / n : r / (1 - Math.pow(1 + r, -n)); // P&I per $1 of loan
      let price = 0, pmiRate = 0.005;
      for (let i = 0; i < 3; i++) {                        // PMI depends on down %, iterate
        const pmi = price > 0 && down / price >= 0.2 ? 0 : pmiRate;
        price = (maxPay - ins / 12 + down * (k + pmi / 12)) / (k + taxPct / 12 + pmi / 12);
        price = Math.max(price, 0);
      }
      const pmi = price > 0 && down / price >= 0.2 ? 0 : pmiRate;
      const loan = Math.max(price - down, 0);
      const pi = loan * k, tip = price * taxPct / 12 + ins / 12 + loan * pmi / 12;
      const ok = maxPay > ins / 12 && price > down;
      out('price').textContent = ok ? money(Math.floor(price / 1000) * 1000) : '$0';
      out('payment').textContent = ok ? money(pi + tip) : '$0';
      out('pi').textContent = ok ? money(pi) : '$0';
      out('tip').textContent = ok ? money(tip) : '$0';
      out('loan').textContent = ok ? money(loan) : '$0';
      out('downPct').textContent = ok && price ? (down / price * 100).toFixed(1) + '%' : '0%';
      out('warn').hidden = ok;
    }
    c.addEventListener('input', update); c.addEventListener('change', update); update();
  })();

  // Seller net sheet
  (function () {
    const c = document.getElementById('netSheet');
    if (!c) return;
    const $ = n => c.querySelector('[name="' + n + '"]');
    const num = el => parseFloat(String(el.value).replace(/[^0-9.]/g, '')) || 0;
    const money = v => (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString(ES ? 'es-US' : 'en-US');
    const out = k => c.querySelector('[data-out="' + k + '"]');
    function update() {
      const price = num($('price')), payoff = num($('payoff'));
      const comm = price * num($('commission')) / 100;
      const transfer = Math.ceil(price / 500) * 0.5;       // SDCL 43-4-21: 50 cents per $500 or fraction
      const other = num($('closing')) + num($('concessions')) + num($('repairs')) + num($('taxes'));
      const net = price - payoff - comm - transfer - other;
      out('net').textContent = money(net);
      out('price').textContent = money(price);
      out('payoff').textContent = '-' + money(payoff);
      out('commission').textContent = '-' + money(comm);
      out('transfer').textContent = '-' + money(transfer);
      out('other').textContent = '-' + money(other);
    }
    c.addEventListener('input', update); c.addEventListener('change', update); update();
  })();

  // ---------- Free guides: lead capture + download reveal ----------
  (() => {
    const form = document.getElementById('guideForm');
    if (!form) return;
    const ES = document.documentElement.lang === 'es';
    const err = form.querySelector('.error');
    const btn = form.querySelector('button[type=submit]');
    const NAMES = ES ? { buyer: 'Guía para Compradores', seller: 'Guía para Vendedores', moving: 'Mudarse a Sioux Falls' }
                     : { buyer: "Buyer's Guide", seller: "Seller's Guide", moving: 'Moving to Sioux Falls' };
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const picked = [...form.querySelectorAll('[name=guide]:checked')].map(c => c.value);
      if (!picked.length) { err.textContent = ES ? 'Escoja al menos una guía.' : 'Pick at least one guide.'; return; }
      for (const el of form.querySelectorAll('.guide-fields [required]')) {
        if (!el.checkValidity()) {
          err.textContent = ES ? 'Escriba su nombre y un correo válido.' : 'Please enter your name and a valid email.';
          el.focus(); return;
        }
      }
      err.textContent = '';
      btn.disabled = true; btn.textContent = ES ? 'Enviando…' : 'Sending…';
      const fd = new FormData(form);
      fd.delete('guide');
      const list = picked.map(k => NAMES[k]).join(', ');
      fd.set('Looking to', 'Guide: ' + list);
      fd.set('Timeline', 'Guide download');
      fd.set('Language', ES ? 'Español' : 'English');
      fd.set('message', 'Downloaded free guide(s): ' + list);
      if (form.dataset.sheet) {
        fetch(form.dataset.sheet, { method: 'POST', mode: 'no-cors', body: new URLSearchParams(fd), keepalive: true }).catch(() => {});
      }
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 10000);
      try {
        await fetch(form.action, { method: 'POST', headers: { 'Accept': 'application/json' }, body: fd, signal: ctrl.signal });
      } catch (_) { /* still give them the guides */ }
      clearTimeout(timer);
      const first = (fd.get('Name') || '').trim().split(' ')[0];
      const done = form.querySelector('.guide-done');
      done.querySelector('.sent-name').textContent = first ? ', ' + first : '';
      form.querySelectorAll('.guide-dl').forEach(a => { a.hidden = !picked.includes(a.dataset.guide); });
      form.querySelector('.guides-list').hidden = true;
      form.querySelector('.guide-form').hidden = true;
      form.querySelectorAll('.eyebrow').forEach(x => x.hidden = true);
      done.hidden = false;
      done.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (window.gtag) gtag('event', 'generate_lead', { method: 'guide' });
    });
  })();

  // ---------- Monthly market update signup ----------
  document.querySelectorAll('.news-form').forEach(form => {
    const ES = document.documentElement.lang === 'es';
    const msg = form.querySelector('.news-msg');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      for (const el of form.querySelectorAll('[required]')) {
        if (!el.checkValidity()) { msg.textContent = ES ? 'Escriba su nombre y un correo válido.' : 'Please enter your name and a valid email.'; el.focus(); return; }
      }
      const btn = form.querySelector('button'); btn.disabled = true;
      const fd = new FormData(form);
      fd.set('Looking to', form.dataset.looking || 'Monthly market update email');
      fd.set('Timeline', form.dataset.timeline || 'Newsletter signup');
      fd.set('Language', ES ? 'Español' : 'English');
      fd.set('message', (form.dataset.looking || 'Signed up for the monthly Sioux Falls market update') + ' — from ' + location.pathname);
      if (form.dataset.sheet) fetch(form.dataset.sheet, { method: 'POST', mode: 'no-cors', body: new URLSearchParams(fd), keepalive: true }).catch(() => {});
      const ctrl = new AbortController(); const timer = setTimeout(() => ctrl.abort(), 10000);
      try { await fetch(form.action, { method: 'POST', headers: { 'Accept': 'application/json' }, body: fd, signal: ctrl.signal }); } catch (_) {}
      clearTimeout(timer);
      const first = (fd.get('Name') || '').trim().split(' ')[0];
      form.classList.add('done');
      msg.textContent = form.dataset.done ? form.dataset.done.replace('{name}', first ? ', ' + first : '') : (ES ? `¡Listo${first ? ', ' + first : ''}! Recibirá el próximo reporte del mercado.` : `You're in${first ? ', ' + first : ''}! Watch for the next market update.`);
      if (window.gtag) gtag('event', 'generate_lead', { method: 'newsletter' });
    });
  });

})();
