/* The Treasure We Found · review build v2
   Scene 1  cover → chest (registered dissolve) → lock unlocks → lid swings open in 3D → light → frame-3 open chest
   Scene 2  two aircraft fly their own SVG routes (getPointAtLength + tangent rotation); dotted trails appear behind them
   Scene 3  invitation reveal, real action cards, Wedding Details sheet
   Every step waits for its animation to actually finish (Animation.finished / rAF progress), never a guessed timer. */
(function () {
  'use strict';
  // ---------- configuration ----------
  const MUSIC_SRC = '';                                   // add a licensed track later, e.g. 'audio/our-song.mp3'
  const MUHURTHAM = new Date('2026-11-21T21:55:00+05:30');
  const CAL = { start: '20261121T143000Z', end: '20261121T173000Z' }; // 8:00–11:00 PM IST · end time PROVISIONAL
  const TITLE = 'Wedding of Akshay & Priya';
  const DETAILS = 'Wedding dinner 8:00 PM IST · Auspicious muhurtham 9:55 PM IST · End time provisional';
  const VENUE = 'Priyanka Convention, Nallajerla, Andhra Pradesh, India';
  // Routes traced from storyboard frame 6 and anchored to frame 4's own pins (941×1672 stage coordinates)
  const ROUTE_T = 'M141.0 668.0 C144.3 674.6 151.7 697.9 160.8 707.7 C169.9 717.5 182.9 722.2 195.7 726.9 C208.5 731.6 224.4 732.6 237.7 735.7 C251.0 738.8 263.0 741.3 275.6 745.6 C288.2 749.9 301.6 755.5 313.6 761.7 C325.6 767.9 336.5 775.5 347.5 782.9 C358.5 790.3 368.8 797.9 379.4 806.1 C390.0 814.4 400.0 822.6 411.3 832.4 C422.6 842.2 436.1 853.7 447.4 864.9 C458.7 876.1 469.9 888.6 479.3 899.4 C488.8 910.2 495.7 918.4 504.1 929.8 C512.6 941.1 521.5 954.3 530.0 967.5 C538.5 980.7 547.1 995.0 554.9 1009.2 C562.7 1023.5 570.1 1039.1 576.7 1053.0 C583.3 1066.9 588.6 1082.9 594.5 1092.7 C600.4 1102.5 609.1 1108.8 612.0 1112.0';
  const ROUTE_G = 'M565.0 708.0 C569.5 718.4 584.1 753.7 591.9 770.4 C599.7 787.1 606.3 795.0 612.0 808.0 C617.7 821.0 622.2 834.2 626.2 848.1 C630.2 862.0 634.0 877.0 636.2 891.6 C638.4 906.2 639.1 921.0 639.3 935.6 C639.5 950.2 639.1 964.3 637.6 979.1 C636.1 993.9 632.7 1009.4 630.0 1024.2 C627.3 1039.0 624.5 1053.5 621.5 1068.1 C618.5 1082.7 613.6 1104.7 612.0 1112.0';
  const DEST = { x: 612, y: 1112 };
  // Title registration between frames (from feature matching): frame1→frame2 and frame2→frame3
  const M12 = 'matrix(1.02536,0,0,1.02536,-52.01,-205.25)', M12i = 'matrix(.97527,0,0,.97527,50.725,200.17)';
  const M23i = 'matrix(.98405,0,0,.98405,10.357,46.459)', ID = 'matrix(1,0,0,1,0,0)';

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const app = $('#app');
  const scenes = { discover: $('#discover'), journey: $('#journey'), invitation: $('#invitation') };
  let current = 'discover', runId = 0;              // runId cancels stale async steps after skip/replay
  const D = ms => reduce ? Math.min(ms, 200) : ms;
  const anim = (el, kf, opt) => el.animate(kf, Object.assign({ fill: 'forwards', easing: 'cubic-bezier(.4,0,.2,1)' }, opt, { duration: D(opt.duration || 600), delay: reduce ? 0 : (opt.delay || 0) }));
  const done = a => a.finished.catch(() => {});
  const stillRunning = id => id === runId;

  /* ---------- stage fit: one scale for artwork + overlays ---------- */
  function fit() {
    const vw = innerWidth, vh = innerHeight, sw = vw / 941, sh = vh / 1672;
    const s = Math.min(Math.max(sw, sh), Math.min(sw, sh) * 1.03);   // fill the screen, cropping at most ~1.5% per side so edge details stay visible
    $$('.stage').forEach(st => st.style.setProperty('--s', s.toFixed(5)));
  }
  addEventListener('resize', fit); addEventListener('orientationchange', () => setTimeout(fit, 250)); fit();
  const stagePoint = (scene, x, y) => { const r = scene.querySelector('.stage').getBoundingClientRect(); return { x: r.left + x * r.width / 941, y: r.top + y * r.height / 1672 }; };

  /* ---------- music pills (one per frame position, identical behaviour) ---------- */
  const tpl = $('#musicTpl');
  $$('.music-slot').forEach(slot => slot.appendChild(tpl.content.cloneNode(true)));
  const pills = $$('.music-pill');
  let audio = null;
  function setMusicUI(playing) { pills.forEach(p => { p.setAttribute('aria-pressed', String(playing)); p.querySelector('.music-label').textContent = playing ? 'Pause Music' : 'Play Music'; }); }
  if (MUSIC_SRC) {
    pills.forEach(p => { p.removeAttribute('aria-disabled'); p.title = 'Play music'; });
    setMusicUI(false);
    pills.forEach(p => p.addEventListener('click', () => {
      if (!audio) { audio = new Audio(MUSIC_SRC); audio.loop = true; audio.volume = .6; }
      if (audio.paused) audio.play().then(() => setMusicUI(true)).catch(() => {}); else { audio.pause(); setMusicUI(false); }
    }));
    document.addEventListener('visibilitychange', () => { if (document.hidden && audio && !audio.paused) { audio.pause(); setMusicUI(false); } });
  }
  // review build: no track configured → pills stay visibly disabled and never pretend to play

  /* ---------- scenes ---------- */
  function show(name) {
    Object.entries(scenes).forEach(([k, el]) => { const on = k === name; el.classList.toggle('is-active', on); el.inert = !on; el.setAttribute('aria-hidden', String(!on)); });
    current = name; app.dataset.scene = name;
    $('#skipBtn').hidden = name === 'invitation';
    try { history.replaceState(null, '', '#' + (name === 'discover' ? 'treasure' : name)); } catch (_) {}
  }
  const bloom = $('#bloom');
  async function bloomTo(next, pt, id) {
    if (reduce) { show(next); return; }
    bloom.style.setProperty('--bx', pt.x + 'px'); bloom.style.setProperty('--by', pt.y + 'px');
    const grow = bloom.animate([
      { opacity: 0, clipPath: `circle(0px at ${pt.x}px ${pt.y}px)` },
      { opacity: 1, clipPath: `circle(16% at ${pt.x}px ${pt.y}px)`, offset: .35 },
      { opacity: 1, clipPath: `circle(150% at ${pt.x}px ${pt.y}px)` }], { duration: 1150, easing: 'cubic-bezier(.5,0,.3,1)', fill: 'forwards' });
    await done(grow); if (!stillRunning(id)) { grow.cancel(); return; }
    show(next);
    const st = scenes[next].querySelector('.stage');
    st.animate([{ transform: 'translate(-50%,-50%) scale(calc(var(--s) * 1.05))' }, { transform: 'translate(-50%,-50%) scale(var(--s))' }], { duration: 1500, easing: 'cubic-bezier(.2,.7,.2,1)' });
    const fade = bloom.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 950, easing: 'ease-out', fill: 'forwards' });
    await done(fade); grow.cancel(); fade.cancel();
  }

  /* ---------- Scene 1 ---------- */
  const cover = $('#coverLayer'), chestL = $('#chestLayer'), openL = $('#openLayer'), lid = $('#lid'), lock = $('#lock');
  const chestBtn = $('#chestBtn'), beginBtn = $('#beginBtn');
  let s1 = 'cover';
  async function begin() {
    if (s1 !== 'cover') return; s1 = 'moving'; const id = runId;
    beginBtn.disabled = true;
    const a1 = anim(cover, [{ transform: ID, opacity: 1 }, { transform: M12, opacity: 0 }], { duration: 1500 });
    const a2 = anim(chestL, [{ transform: M12i }, { transform: ID }], { duration: 1500 });
    await Promise.all([done(a1), done(a2)]); if (!stillRunning(id)) return;
    cover.style.visibility = 'hidden';
    scenes.discover.classList.add('s1-chest'); s1 = 'chest';
    chestBtn.tabIndex = 0; chestBtn.focus({ preventScroll: true });
    chestBtn.animate([{ boxShadow: '0 0 0 0 #ffe7a000' }, { boxShadow: '0 0 0 30px #ffe7a033' }, { boxShadow: '0 0 0 0 #ffe7a000' }], { duration: 1800, iterations: 2 });
  }
  async function openChest() {
    if (s1 !== 'chest') return; s1 = 'opening'; const id = runId;
    chestBtn.setAttribute('aria-label', 'Opening the treasure');
    // 1 · the lock responds
    const j = lock.animate([{ transform: 'rotate(0)' }, { transform: 'rotate(-8deg)', offset: .2 }, { transform: 'rotate(7deg)', offset: .45 }, { transform: 'rotate(-4deg)', offset: .7 }, { transform: 'rotate(0)' }], { duration: D(560), easing: 'ease-in-out' });
    anim($('#keyglint'), [{ opacity: 0, transform: 'scale(.4)' }, { opacity: 1, transform: 'scale(1.2)', offset: .5 }, { opacity: .6, transform: 'scale(1)' }], { duration: 700 });
    await done(j); if (!stillRunning(id)) return;
    anim(lock, [{ transform: 'translateY(0)' }, { transform: 'translateY(6px) rotate(-3deg)' }], { duration: 300, easing: 'cubic-bezier(.3,1.6,.5,1)' });
    // 2 · the lid swings up on its back hinge, light pours out
    anim($('#chestBase'), [{ opacity: 0 }, { opacity: 1 }], { duration: 260 });
    anim($('.chest-glow'), [{ opacity: 0, transform: 'scale(.6)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 1200 });
    anim($('.beams'), [{ opacity: 0, transform: 'scaleY(.25)' }, { opacity: .95, transform: 'scaleY(1)' }], { duration: 1500, easing: 'cubic-bezier(.2,.7,.2,1)' });
    const l = anim(lid, [{ transform: 'rotateX(0deg)' }, { transform: 'rotateX(128deg)' }], { duration: 1700, easing: 'cubic-bezier(.45,.05,.2,1)' });
    // 3 · as the lid passes vertical, a burst of light reveals the painted open chest (frame 3)
    const fl = anim($('#flash'), [{ opacity: 0 }, { opacity: 1 }], { duration: 420, delay: 1150, easing: 'ease-in' });
    await done(fl); if (!stillRunning(id)) return;
    lid.style.visibility = 'hidden'; lock.style.visibility = 'hidden'; $('#chestClosed').style.opacity = 0;
    openL.style.opacity = 1;
    anim(openL, [{ transform: M23i }, { transform: ID }], { duration: 1400, easing: 'cubic-bezier(.2,.7,.2,1)' });
    const out = anim($('#flash'), [{ opacity: 1 }, { opacity: 0 }], { duration: 750, easing: 'ease-out' });
    await done(out); await done(l); if (!stillRunning(id)) return;
    s1 = 'open';
    // 4 · a short breath on the open treasure, then its light becomes the map
    const breathe = anim($('.chest-glow'), [{ opacity: 1, transform: 'scale(1)' }, { opacity: 1, transform: 'scale(1.08)' }], { duration: 900, easing: 'ease-in-out' });
    await done(breathe); if (!stillRunning(id)) return;
    await bloomTo('journey', stagePoint(scenes.discover, 472, 1150), id);
    if (stillRunning(id)) $('#followBtn').focus({ preventScroll: true });
  }
  function resetScene1() {
    s1 = 'cover';
    [cover, chestL, openL, lid, lock, $('#chestBase'), $('#chestClosed'), $('.chest-glow'), $('.beams'), $('#flash'), $('#keyglint'), chestBtn].forEach(el => el.getAnimations().forEach(a => a.cancel()));
    cover.style.visibility = ''; lid.style.visibility = ''; lock.style.visibility = ''; openL.style.opacity = ''; $('#chestClosed').style.opacity = '';
    scenes.discover.classList.remove('s1-chest'); chestBtn.tabIndex = -1; beginBtn.disabled = false;
    chestBtn.setAttribute('aria-label', 'Tap to open the treasure');
  }
  beginBtn.addEventListener('click', begin);
  chestBtn.addEventListener('click', openChest);

  /* ---------- Scene 2 · flights ---------- */
  const svgNS = 'http://www.w3.org/2000/svg';
  const flightSvg = $('#flight'), defs = flightSvg.querySelector('defs');
  const routes = [
    { d: ROUTE_T, path: $('#routeT'), glow: $('#glowT'), ac: $('#acT'), start: 0, dur: 6400 },
    { d: ROUTE_G, path: $('#routeG'), glow: $('#glowG'), ac: $('#acG'), start: 450, dur: 5950 }   // both land at 6.4 s
  ];
  routes.forEach((r, i) => {
    r.path.setAttribute('d', r.d); r.glow.setAttribute('d', r.d);
    r.L = r.path.getTotalLength();
    // progressive trail: a mask stroke that grows along the route behind the aircraft
    const mask = document.createElementNS(svgNS, 'mask'); mask.id = 'trail' + i; mask.setAttribute('maskUnits', 'userSpaceOnUse');
    mask.setAttribute('x', 0); mask.setAttribute('y', 0); mask.setAttribute('width', 941); mask.setAttribute('height', 1672);
    const mp = document.createElementNS(svgNS, 'path'); mp.setAttribute('d', r.d);
    mp.setAttribute('fill', 'none'); mp.setAttribute('stroke', '#fff'); mp.setAttribute('stroke-width', '34'); mp.setAttribute('stroke-linecap', 'round');
    mp.style.strokeDasharray = r.L + ' ' + (r.L + 10);
    mask.appendChild(mp); defs.appendChild(mask); r.mask = mp;
    r.path.setAttribute('mask', 'url(#trail' + i + ')'); r.glow.setAttribute('mask', 'url(#trail' + i + ')');
  });
  const dest = $('#dest'); dest.setAttribute('transform', `translate(${DEST.x} ${DEST.y})`);
  const followBtn = $('#followBtn'), status = $('#flightStatus');
  const easeIO = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const flight = { running: false, raf: 0, p: [0, 0] };
  function place(r, p) {
    const d = Math.max(0, Math.min(r.L, p * r.L));
    const pt = r.path.getPointAtLength(d);
    const a = r.path.getPointAtLength(Math.max(0, d - 3)), b = r.path.getPointAtLength(Math.min(r.L, d + 3));
    const ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
    const k = .9 + .2 * Math.sin(Math.PI * p);
    r.ac.setAttribute('transform', `translate(${pt.x.toFixed(2)} ${pt.y.toFixed(2)}) rotate(${ang.toFixed(2)}) scale(${k.toFixed(3)})`);
    r.mask.style.strokeDashoffset = (r.L * (1 - p)).toFixed(2);
  }
  function setProgress(p0, p1) { flight.p = [p0, p1]; place(routes[0], p0); place(routes[1], p1); }
  function resetFlight() {
    cancelAnimationFrame(flight.raf); flight.running = false;
    routes.forEach(r => { r.ac.getAnimations().forEach(a => a.cancel()); r.ac.style.opacity = '0'; });
    [dest.querySelector('.dest-glow'), dest.querySelector('.heart-pin'), ...dest.querySelectorAll('.dest-ring'), $('#wave')].forEach(el => el.getAnimations().forEach(a => a.cancel()));
    followBtn.getAnimations().forEach(a => a.cancel()); followBtn.style.visibility = ''; followBtn.disabled = false;
    status.textContent = ''; setProgress(0, 0);
  }
  function fly() {
    if (flight.running) return; const id = runId;
    resetFlight(); flight.running = true; followBtn.disabled = true;
    status.textContent = 'Two aircraft are flying toward the wedding destination.';
    anim(followBtn, [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(20px)' }], { duration: 450 }).finished.then(() => { followBtn.style.visibility = 'hidden'; }).catch(() => {});
    routes.forEach(r => { r.ac.style.opacity = '1'; anim(r.ac, [{ opacity: 0 }, { opacity: 1 }], { duration: 350 }); });
    const t0 = performance.now(), END = 6400;
    const step = now => {
      if (!stillRunning(id)) return;
      const t = now - t0;
      const p = routes.map(r => easeIO(Math.min(1, Math.max(0, (t - r.start) / r.dur))));
      setProgress(p[0], p[1]);
      if (p[0] < 1 || p[1] < 1) { flight.raf = requestAnimationFrame(step); return; }
      arrive(id);                                  // both aircraft have reached the destination
    };
    flight.raf = requestAnimationFrame(step);
  }
  async function arrive(id) {
    flight.running = false;
    status.textContent = 'Both aircraft have arrived. Every road led here.';
    routes.forEach(r => anim(r.ac, [{ opacity: 1 }, { opacity: 0 }], { duration: 700, delay: 250 }));
    anim(dest.querySelector('.dest-glow'), [{ opacity: 0, transform: 'scale(.3)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 900, easing: 'cubic-bezier(.2,.8,.2,1)' });
    dest.querySelectorAll('.dest-ring').forEach((rg, i) => anim(rg, [{ opacity: .9, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(3.4)' }], { duration: 1500, delay: i * 450, fill: 'none' }));
    const pin = anim(dest.querySelector('.heart-pin'), [{ opacity: 0, transform: 'scale(.4) translateY(10px)' }, { opacity: 1, transform: 'scale(1.12)', offset: .7 }, { opacity: 1, transform: 'scale(1)' }], { duration: 800, easing: 'cubic-bezier(.2,1.2,.4,1)' });
    const wave = anim($('#wave'), [{ opacity: 0, transform: 'translateY(60px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 1300, easing: 'cubic-bezier(.2,.7,.2,1)' });
    await Promise.all([done(pin), done(wave)]); if (!stillRunning(id)) return;
    await bloomTo('invitation', stagePoint(scenes.journey, DEST.x, DEST.y), id);
    if (stillRunning(id)) revealInvite();
  }
  followBtn.addEventListener('click', fly);
  setProgress(0, 0);

  /* ---------- Scene 3 ---------- */
  const cardBar = $('#cardBar');
  function revealInvite() { cardBar.classList.remove('on'); void cardBar.offsetWidth; requestAnimationFrame(() => cardBar.classList.add('on')); }

  /* ---------- skip / replay ---------- */
  function hardReset() { runId++; resetScene1(); resetFlight(); closeSheet(); closeCal(); cardBar.classList.remove('on'); bloom.getAnimations().forEach(a => a.cancel()); bloom.style.opacity = 0; }
  function skip(e) { if (e) e.preventDefault(); hardReset(); show('invitation'); revealInvite(); }
  function replayStory() { hardReset(); show('discover'); scenes.discover.animate([{ opacity: 0 }, { opacity: 1 }], { duration: D(500) }); beginBtn.focus({ preventScroll: true }); }
  $$('[data-skip]').forEach(b => b.addEventListener('click', skip));
  $$('[data-replay]').forEach(b => b.addEventListener('click', replayStory));

  /* ---------- details sheet ---------- */
  const sheet = $('#sheet'); let lastFocus = null;
  function openSheet() { lastFocus = document.activeElement; closeCal(); sheet.hidden = false; sheet.classList.remove('in'); void sheet.offsetWidth; sheet.classList.add('in'); $('#sheetClose').focus({ preventScroll: true }); tick(); }
  function closeSheet() { if (sheet.hidden) return; sheet.hidden = true; if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true }); }
  $$('[data-open-details]').forEach(b => b.addEventListener('click', openSheet));
  $('#sheetClose').addEventListener('click', closeSheet);

  /* calendar chooser */
  const calPop = $('#calPop');
  function openCal() { calPop.hidden = false; $('#gcalLink').focus({ preventScroll: true }); }
  function closeCal() { calPop.hidden = true; }
  $$('[data-calendar]').forEach(b => b.addEventListener('click', openCal));
  $('#calClose').addEventListener('click', closeCal);
  $('#gcalLink').href = 'https://calendar.google.com/calendar/render?action=TEMPLATE&text=' + encodeURIComponent(TITLE) + '&dates=' + CAL.start + '/' + CAL.end + '&ctz=Asia/Kolkata&details=' + encodeURIComponent(DETAILS) + '&location=' + encodeURIComponent(VENUE);
  $('#gcalLink').addEventListener('click', () => setTimeout(closeCal, 300));
  $('#icsBtn').addEventListener('click', () => {
    const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Akshay & Priya//Wedding review//EN', 'CALSCALE:GREGORIAN', 'BEGIN:VEVENT', 'UID:akshay-priya-wedding-20261121@review',
      'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, ''), 'DTSTART:' + CAL.start, 'DTEND:' + CAL.end, 'SUMMARY:' + TITLE,
      'DESCRIPTION:' + DETAILS.replace(/,/g, '\\,'), 'LOCATION:' + VENUE.replace(/,/g, '\\,'), 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: 'akshay-priya-wedding.ics' });
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 4000); closeCal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { if (!calPop.hidden) closeCal(); else closeSheet(); }
    if (e.key === 'Tab' && !sheet.hidden && calPop.hidden) {
      const f = [...sheet.querySelectorAll('a,button')].filter(x => x.offsetParent !== null); if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });

  /* countdown to the muhurtham */
  const pad = n => String(n).padStart(2, '0');
  function tick() {
    let ms = MUHURTHAM - Date.now();
    if (ms <= 0) { ['cdD', 'cdH', 'cdM', 'cdS'].forEach(id => $('#' + id).textContent = '00'); return; }
    const d = Math.floor(ms / 864e5); ms -= d * 864e5; const h = Math.floor(ms / 36e5); ms -= h * 36e5; const m = Math.floor(ms / 6e4); ms -= m * 6e4;
    $('#cdD').textContent = d; $('#cdH').textContent = pad(h); $('#cdM').textContent = pad(m); $('#cdS').textContent = pad(Math.floor(ms / 1000));
  }
  tick(); setInterval(tick, 1000);

  /* share */
  async function share() {
    const note = $('#note'), url = location.href.split('#')[0];
    const data = { title: 'Akshay & Priya · The Treasure We Found', text: 'Saturday, 21 November 2026 · Priyanka Convention, Nallajerla', url };
    try { if (navigator.share) { await navigator.share(data); return; } } catch (e) { if (e && e.name === 'AbortError') return; }
    try { await navigator.clipboard.writeText(url); note.textContent = 'Link copied.'; } catch (_) { note.textContent = 'Copy this link: ' + url; }
    status.textContent = note.textContent;
  }
  $$('[data-share]').forEach(b => b.addEventListener('click', share));

  /* ---------- deep links + preload ---------- */
  const h = location.hash.replace('#', '');
  if (h === 'invitation') { show('invitation'); revealInvite(); } else if (h === 'journey') show('journey'); else show('discover');
  addEventListener('load', () => ['img/s2-map.webp', 'img/s3-invite.webp', 'img/s1-open.webp'].forEach(src => { const i = new Image(); i.src = src; }));

  window.__treasure = { begin, openChest, fly, skip, replayStory, setProgress,
    get state() { return { current, s1, flight: { running: flight.running, p: flight.p.slice(), L: routes.map(r => r.L) } }; } };
})();
