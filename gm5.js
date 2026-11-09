// Give Me Five Buying Plan quiz (605homesearch.com/give-me-five/ and /es/califica-give-me-five/)
// Estimates only. Assumptions are shown on the page; update RATE when SD Housing's rate sheet changes.
(function () {
  const form = document.getElementById('leadForm');
  if (!form || form.dataset.kind !== 'gm5') return;
  const ES = document.documentElement.lang.startsWith('es');

  const RATE = 0.0675;        // SD Housing Give Me Five rate (higher of 6.375% / 6.75%, effective Nov 2, 2026)
  const FHA_DOWN = 0.035;     // FHA minimum down payment
  const UFMIP = 0.0175;       // FHA upfront mortgage insurance, added to the loan
  const MIP = 0.0055;         // FHA annual mortgage insurance
  const TAX = 0.012;          // property tax estimate, per year
  const INS = 175;            // homeowners insurance estimate, per month
  const CLOSING = 0.03;       // closing cost estimate
  const LIMIT = 410000;
  const HARD = ['owned', 'notprimary', 'price'];

  const money = n => '$' + Math.round(n).toLocaleString('en-US');
  const round = (n, to) => Math.round(n / to) * to;
  const checked = name => form.querySelector('input[name="' + name + '"]:checked');

  function plan() {
    const p = checked('Price range');
    const price = p ? Number(p.dataset.price || 0) : 0;
    const flags = [...form.querySelectorAll('input[type=radio]:checked')].map(r => r.dataset.flag).filter(Boolean);
    const tier = flags.some(f => HARD.includes(f)) ? 'no' : (flags.length ? 'check' : 'fit');
    if (!price || price > LIMIT) return { tier, flags, price: 0 };
    const base = price * (1 - FHA_DOWN);
    const assist = base * 0.05;
    const down = price * FHA_DOWN;
    const closing = price * CLOSING;
    const cash = Math.max(0, down + closing - assist);
    const loan = base * (1 + UFMIP);
    const r = RATE / 12, n = 360;
    const pi = loan * r / (1 - Math.pow(1 + r, -n));
    const monthly = pi + base * MIP / 12 + price * TAX / 12 + INS;
    return { tier, flags, price, assist, down, closing, cash, monthly };
  }

  const set = (sel, v) => form.querySelectorAll(sel).forEach(el => { el.textContent = v; });

  form.addEventListener('wizard:step', e => {
    const step = e.detail.step;
    if (!step.classList.contains('gm5-teaser')) return;
    const d = plan();
    const yes = d.price && d.tier !== 'no';
    step.querySelector('.teaser-yes').hidden = !yes;
    step.querySelector('.teaser-no').hidden = yes;
    if (d.price) { set('.v-assist', money(d.assist)); set('.v-price', money(d.price)); }
  });

  form.addEventListener('wizard:submit', e => {
    const d = plan();
    const label = { fit: 'strong fit', check: 'check', no: 'may not fit' }[d.tier];
    e.detail.fd.set('Looking to', 'Give Me Five: ' + label + (d.price ? ' ' + money(d.price) : '') + (d.flags.length ? ' (' + d.flags.join(', ') + ')' : ''));
  });

  form.addEventListener('wizard:sent', () => {
    const d = plan();
    form.querySelectorAll('.gm5-tier').forEach(t => { t.hidden = t.dataset.tier !== d.tier; });
    form.querySelectorAll('.gm5-flags li').forEach(li => { li.hidden = !d.flags.includes(li.dataset.flag); });
    const table = form.querySelector('.gm5-plan');
    table.hidden = !d.price || d.tier === 'no';
    form.querySelector('.gm5-note').hidden = table.hidden;
    if (d.price) {
      set('.v-price', money(d.price));
      set('.v-assist', money(d.assist));
      set('.v-down', money(d.down));
      set('.v-closing', money(round(d.closing, 100)));
      set('.v-cash', d.cash < 500 ? (ES ? 'Casi nada' : 'Close to $0') : money(round(d.cash, 100)));
      set('.v-monthly', money(round(d.monthly, 10)));
    }
  });
})();
