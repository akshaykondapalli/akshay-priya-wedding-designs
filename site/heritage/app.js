(() => {
  'use strict';
  const root = document.documentElement;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  let revealAll = false;
  const motionOK = () => !reduce.matches && !revealAll;
  const setMotion = () => root.classList.toggle('motion', motionOK());
  setMotion();
  reduce.addEventListener?.('change', () => { setMotion(); update(); });

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

  /* ---------- menu ---------- */
  const menuBtn = $('.bar__menu'), menu = $('#menu');
  const closeMenu = (focusBtn = true) => { menu.hidden = true; menuBtn.setAttribute('aria-expanded', 'false'); if (focusBtn) menuBtn.focus(); };
  menuBtn.addEventListener('click', () => {
    const open = menu.hidden;
    menu.hidden = !open; menuBtn.setAttribute('aria-expanded', String(open));
    if (open) $('a', menu).focus();
  });
  $('.menu__close').addEventListener('click', () => closeMenu());
  $$('a', menu).forEach(a => a.addEventListener('click', () => closeMenu(false)));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !menu.hidden) closeMenu(); });
  menu.addEventListener('keydown', e => {
    if (e.key !== 'Tab') return;
    const f = $$('a,button', menu), first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  /* ---------- I · open the atlas ---------- */
  const arrival = $('#arrival'), openBtn = $('#openAtlas');
  const openAtlas = (instant) => {
    if (instant) arrival.querySelectorAll('.book,.book__cover,.book__page').forEach(el => { el.style.transition = 'none'; });
    arrival.classList.add('is-open');
    if (!instant) setTimeout(() => $('.arrival__next').focus({ preventScroll: true }), 1900);
  };
  openBtn.addEventListener('click', () => openAtlas(!motionOK()));

  /* ---------- skip links land on the invitation and finish the intro ---------- */
  $$('a[href="#invitation"]').forEach(a => a.addEventListener('click', () => {
    arrival.classList.add('is-open');
    setTimeout(() => $('#invitation').focus({ preventScroll: true }), 50);
  }));

  /* ---------- II · routes ---------- */
  const souls = $('#souls');
  const reveals = $$('.reveal', souls);
  const routes = $$('.route', souls);
  const heads = [$('.head--gold', souls), $('.head--red', souls)];
  const lens = reveals.map(p => p.getTotalLength());
  const beats = $$('.beat', souls);

  const conn = $('#connection');
  const zoomChart = $('.chart--zoom', conn);
  const dest = $('#destination');
  const scene = $('.scene', dest);

  const progress = el => {
    const r = el.getBoundingClientRect();
    const span = r.height - window.innerHeight;
    return span <= 0 ? (r.top <= 0 ? 1 : 0) : clamp(-r.top / span);
  };

  function setRoutes(p) {
    reveals.forEach((path, i) => {
      const L = lens[i];
      path.style.strokeDasharray = `${L} ${L}`;
      const k = clamp((p - i * .06) / .72);
      path.style.strokeDashoffset = String(L * (1 - ease(k)));
      const pt = path.getPointAtLength(L * ease(k));
      heads[i].setAttribute('cx', pt.x); heads[i].setAttribute('cy', pt.y);
      heads[i].style.opacity = k > 0.995 ? 0 : 1;
    });
    beats.forEach(b => b.classList.toggle('on', p >= parseFloat(b.dataset.at)));
    souls.classList.toggle('arrived', p > .8);
  }

  function update() {
    if (!motionOK()) {
      reveals.forEach(path => { path.style.strokeDasharray = ''; path.style.strokeDashoffset = ''; });
      beats.forEach(b => b.classList.add('on'));
      conn.classList.add('stamped');
      zoomChart.style.removeProperty('--z');
      conn.style.setProperty('--sw', 0);
      scene.style.removeProperty('--p');
      dest.style.setProperty('--am', 0);
      return;
    }
    setRoutes(progress(souls));
    // III: zoom toward the meeting point, stamp, then the light swells
    const pc = progress(conn);
    zoomChart.style.setProperty('--z', (1 + 1.1 * ease(clamp(pc / .55))).toFixed(4));
    conn.classList.toggle('stamped', pc > .32);
    conn.style.setProperty('--sw', ease(clamp((pc - .72) / .28)).toFixed(3));
    // IV: amber fades out to reveal the mandapam, gentle dolly-in
    const pd = progress(dest);
    dest.style.setProperty('--am', (1 - ease(clamp(pd / .22))).toFixed(3));
    scene.style.setProperty('--p', pd.toFixed(4));
  }
  let ticking = false;
  const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { ticking = false; update(); }); } };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  update();

  /* ---------- countdown (Asia/Kolkata, 8:00 PM IST) ---------- */
  const target = Date.parse('2026-11-21T20:00:00+05:30');
  const cd = $('#countdown');
  function tick() {
    let ms = Math.max(0, target - Date.now());
    const d = Math.floor(ms / 864e5); ms -= d * 864e5;
    const h = Math.floor(ms / 36e5); ms -= h * 36e5;
    const m = Math.floor(ms / 6e4);
    $('[data-u="d"]', cd).textContent = d;
    $('[data-u="h"]', cd).textContent = String(h).padStart(2, '0');
    $('[data-u="m"]', cd).textContent = String(m).padStart(2, '0');
  }
  tick(); setInterval(tick, 15000);

  /* ---------- .ics download (times in UTC; 8:00 PM IST = 14:30 UTC) ---------- */
  $('#icsBtn').addEventListener('click', () => {
    const ics = [
      'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Akshay & Priya//Wedding design preview//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      'UID:akshay-priya-wedding-20261121@atlas-of-us',
      'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, ''),
      'DTSTART:20261121T143000Z',
      'DTEND:20261121T173000Z',
      'SUMMARY:Wedding of Akshay & Priya',
      'DESCRIPTION:Wedding dinner 8:00 PM IST \\n Muhurtham 9:55 PM IST',
      'LOCATION:Priyanka Convention\\, Nallajerla\\, Andhra Pradesh\\, India',
      'END:VEVENT', 'END:VCALENDAR'
    ].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: 'akshay-priya-wedding.ics' });
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  });

  /* ---------- share ---------- */
  const status = $('#shareStatus');
  $('#shareBtn').addEventListener('click', async () => {
    const data = { title: 'Akshay & Priya · 21 November 2026', text: 'The wedding of Akshay & Priya — Saturday, 21 November 2026, Priyanka Convention, Nallajerla.', url: location.href.split('#')[0] };
    if (navigator.share) {
      try { await navigator.share(data); status.textContent = ''; return; } catch (e) { if (e && e.name === 'AbortError') return; }
    }
    try { await navigator.clipboard.writeText(data.url); status.textContent = 'Link copied.'; }
    catch { status.textContent = 'Copy this link: ' + data.url; }
  });

  /* ---------- automated review hook: fully revealed state ---------- */
  window.atlasReveal = () => {
    revealAll = true;
    document.querySelectorAll('img[loading="lazy"]').forEach(i => { i.loading = 'eager'; });
    openAtlas(true);
    setMotion();
    update();
    return true;
  };
})();
