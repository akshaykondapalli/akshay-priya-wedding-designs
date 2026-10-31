/* The Atlas of Us — Direction 03 · Ultra-Luxury Editorial */
(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var revealedAll = false;

  /* masthead: split words into characters for a staggered masked rise */
  document.querySelectorAll('[data-split]').forEach(function (el) {
    var i = 0;
    function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var frag = document.createDocumentFragment();
          n.textContent.split('').forEach(function (c) {
            if (c === ' ') { frag.appendChild(document.createTextNode(' ')); return; }
            var s = document.createElement('span');
            s.className = 'ch'; s.textContent = c; s.style.setProperty('--i', i++);
            s.setAttribute('aria-hidden', 'true');
            frag.appendChild(s);
          });
          n.parentNode.replaceChild(frag, n);
        } else if (n.nodeType === 1) walk(n);
      });
    }
    walk(el);
    el.classList.add('is-split');
  });

  /* reveal on scroll (gated: only hides when IO exists) */
  var rvs = document.querySelectorAll('.rv');
  if ('IntersectionObserver' in window && !reduce.matches) {
    root.classList.add('io');
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: .05 });
    rvs.forEach(function (el) { io.observe(el); });
    // safety: never leave content hidden
    setTimeout(function () { if (document.hidden) revealAll(); }, 4000);
  }

  /* scroll-scrubbed progress (--p) for routes, ampersand, thoranam, muggu */
  var scrubs = Array.prototype.slice.call(document.querySelectorAll('[data-scrub], .thoranam-wrap'));
  var ranges = { souls: [.85, .15], connection: [.95, .45], muggu: [.95, .45] };
  var ticking = false;
  function bar() {
    var b = document.getElementById('bar');
    b.classList.toggle('solid', window.scrollY > 40);
    var bl = document.getElementById('blessing').getBoundingClientRect();
    var col = document.querySelector('.colophon').getBoundingClientRect();
    b.classList.toggle('dark', (bl.top < 60 && bl.bottom > 0) || col.top < 60);
  }
  function update() {
    ticking = false;
    bar();
    if (revealedAll || reduce.matches) return;
    var vh = window.innerHeight;
    scrubs.forEach(function (el) {
      var r = el.getBoundingClientRect();
      var key = el.getAttribute('data-scrub') || 'thoranam';
      var a = (ranges[key] || [.95, .55])[0] * vh, b = (ranges[key] || [.95, .55])[1] * vh;
      // progress: element top passes from a (start) to b (end); souls uses its bottom area
      var ref = key === 'souls' ? r.top + r.height * .45 : r.top;
      var p = (a - ref) / (a - b);
      p = Math.max(0, Math.min(1, p));
      el.style.setProperty('--p', p.toFixed(4));
    });
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  update();
  reduce.addEventListener && reduce.addEventListener('change', function () {
    if (reduce.matches) scrubs.forEach(function (el) { el.style.setProperty('--p', 1); });
    else update();
  });

  /* menu */
  var menu = document.getElementById('menu'), btn = document.getElementById('menuBtn'), close = document.getElementById('menuClose');
  function openMenu() { menu.hidden = false; btn.setAttribute('aria-expanded', 'true'); document.body.style.overflow = 'hidden'; menu.querySelector('a').focus(); }
  function closeMenu(focusBack) { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); document.body.style.overflow = ''; if (focusBack) btn.focus(); }
  btn.addEventListener('click', function () { menu.hidden ? openMenu() : closeMenu(true); });
  close.addEventListener('click', function () { closeMenu(true); });
  menu.addEventListener('click', function (e) { if (e.target.closest('a')) closeMenu(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !menu.hidden) closeMenu(true);
    if (e.key === 'Tab' && !menu.hidden) {
      var f = menu.querySelectorAll('a, button'), first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  /* portfolio carousel: native scroll-snap + buttons + counter */
  var track = document.getElementById('pfTrack'), prev = document.getElementById('pfPrev'), next = document.getElementById('pfNext'), now = document.getElementById('pfNow');
  var items = track.querySelectorAll('.pf-item');
  function current() {
    var x = track.scrollLeft, best = 0, bd = 1e9;
    items.forEach(function (it, i) { var dd = Math.abs((it.offsetLeft - items[0].offsetLeft) - x); if (dd < bd) { bd = dd; best = i; } });
    return best;
  }
  function sync() {
    var c = current();
    now.textContent = ('0' + (c + 1)).slice(-2);
    prev.disabled = track.scrollLeft < 4;
    next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
  }
  function go(d) {
    var c = Math.max(0, Math.min(items.length - 1, current() + d));
    track.scrollTo({ left: items[c].offsetLeft - items[0].offsetLeft, behavior: reduce.matches ? 'auto' : 'smooth' });
  }
  prev.addEventListener('click', function () { go(-1); });
  next.addEventListener('click', function () { go(1); });
  track.addEventListener('scroll', function () { requestAnimationFrame(sync); }, { passive: true });
  track.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
  });
  sync();

  /* magnetic hover — fine pointers only */
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches && !reduce.matches) {
    document.querySelectorAll('[data-magnetic]').forEach(function (el) {
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) / r.width, dy = (e.clientY - (r.top + r.height / 2)) / r.height;
        el.style.transform = 'translate(' + (dx * 8).toFixed(2) + 'px,' + (dy * 6).toFixed(2) + 'px)';
      });
      el.addEventListener('pointerleave', function () { el.style.transform = ''; });
    });
  }

  /* countdown to dinner, 21 Nov 2026 20:00 IST */
  var target = Date.parse('2026-11-21T20:00:00+05:30');
  var cds = { d: document.querySelector('[data-cd="d"]'), h: document.querySelector('[data-cd="h"]'), m: document.querySelector('[data-cd="m"]') };
  function tick() {
    var ms = target - Date.now();
    var note = document.querySelector('.cd-note');
    if (ms <= 0) { cds.d.textContent = '0'; cds.h.textContent = '0'; cds.m.textContent = '0'; note.textContent = 'The celebration has begun'; return; }
    var m = Math.floor(ms / 60000);
    cds.d.textContent = Math.floor(m / 1440);
    cds.h.textContent = ('0' + Math.floor((m % 1440) / 60)).slice(-2);
    cds.m.textContent = ('0' + (m % 60)).slice(-2);
  }
  tick(); setInterval(tick, 30000);

  /* .ics download (UTC times; 8:00–11:00 PM IST, end time is a placeholder) */
  document.getElementById('icsBtn').addEventListener('click', function () {
    var ics = [
      'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//The Atlas of Us//Editorial preview//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'BEGIN:VEVENT', 'UID:akshay-priya-wedding-20261121@atlas-of-us', 'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, ''),
      'DTSTART:20261121T143000Z', 'DTEND:20261121T173000Z',
      'SUMMARY:Wedding of Akshay & Priya',
      'DESCRIPTION:Wedding dinner 8:00 PM IST · Muhurtham 9:55 PM IST',
      'LOCATION:Priyanka Convention\\, Nallajerla\\, Andhra Pradesh\\, India',
      'END:VEVENT', 'END:VCALENDAR'
    ].join('\r\n');
    var blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'akshay-priya-wedding.ics';
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    status('Calendar file prepared: akshay-priya-wedding.ics');
  });

  /* share */
  var statusEl = document.getElementById('shareStatus');
  function status(t) { statusEl.textContent = t; clearTimeout(status._t); status._t = setTimeout(function () { statusEl.textContent = ''; }, 5000); }
  document.getElementById('shareBtn').addEventListener('click', function () {
    var url = location.href.split('#')[0];
    var data = { title: 'Akshay & Priya · 21 November 2026', text: 'The wedding of Akshay & Priya — Saturday, 21 November 2026, Priyanka Convention, Nallajerla.', url: url };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () { status('Link copied'); }, function () { fallback(url); });
    } else fallback(url);
  });
  function fallback(url) {
    var i = document.createElement('input'); i.value = url; i.setAttribute('aria-label', 'Invitation link'); i.className = 'btn btn-ghost';
    statusEl.textContent = ''; statusEl.appendChild(i); i.select();
  }

  /* fully revealed state for automated capture */
  function revealAll() {
    revealedAll = true;
    document.querySelectorAll('img[loading="lazy"]').forEach(function (im) { im.loading = 'eager'; });
    root.classList.add('revealed');
    rvs.forEach(function (el) { el.classList.add('in'); });
    scrubs.forEach(function (el) { el.style.setProperty('--p', 1); });
  }
  window.atlasReveal = revealAll;
})();
