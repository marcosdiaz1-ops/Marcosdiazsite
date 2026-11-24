// Areas section on the home page (EN + ES): town list on the left, big photo on the right.
// Pointing at a town swaps the photo and the "Explore ..." card; clicking opens that town's page.
// On touch screens the first tap shows the photo and the second tap opens the page.
// The round arrows step through the towns.
(function () {
  var box = document.querySelector('.hoods');
  if (!box) return;
  var links = [].slice.call(box.querySelectorAll('.hood-list a'));
  var slides = [].slice.call(box.querySelectorAll('.hood-slide'));
  var card = box.querySelector('.hood-card');
  var title = card.querySelector('b');
  var cur = 0;
  var lastPointer = '';

  function show(i) {
    cur = (i + links.length) % links.length;
    for (var k = 0; k < links.length; k++) {
      links[k].classList.toggle('on', k === cur);
      if (k === cur) links[k].setAttribute('aria-current', 'true'); else links[k].removeAttribute('aria-current');
    }
    slides.forEach(function (s, n) { s.classList.toggle('on', n === cur); });
    card.href = links[cur].getAttribute('href');
    title.textContent = links[cur].querySelector('span').textContent;
  }

  links.forEach(function (a, k) {
    a.addEventListener('pointerdown', function (e) { lastPointer = e.pointerType; });
    a.addEventListener('mouseenter', function () { if (lastPointer !== 'touch') show(k); });
    a.addEventListener('focus', function () { if (!lastPointer) show(k); }); // keyboard
    a.addEventListener('click', function (e) {
      if ((lastPointer === 'touch' || lastPointer === 'pen') && !a.classList.contains('was-shown')) {
        e.preventDefault();
        links.forEach(function (x) { x.classList.remove('was-shown'); });
        a.classList.add('was-shown');
        show(k);
        box.querySelector('.hood-media').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      lastPointer = '';
    });
  });
  box.querySelector('.hood-prev').addEventListener('click', function () { show(cur - 1); });
  box.querySelector('.hood-next').addEventListener('click', function () { show(cur + 1); });

  // Load the other photos once the section is near the screen, so switching is instant
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (en, ob) {
      if (en[0].isIntersecting) { slides.forEach(function (s) { if (s.loading) s.loading = 'eager'; }); ob.disconnect(); }
    }, { rootMargin: '400px' }).observe(box);
  }
})();
