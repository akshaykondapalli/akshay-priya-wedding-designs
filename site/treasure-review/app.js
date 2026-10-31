/* The Treasure We Found · review build
   Scene 1: real chest-opening interaction (lock jiggle → lid swings open in 3D → light → golden bloom)
   Scene 2: two aircraft fly along SVG routes using getPointAtLength(), oriented by the path tangent
   Scene 3: the approved invitation artwork, shown unaltered, plus a real Wedding Details panel */
(function () {
  'use strict';

  /* ---------- configuration ---------- */
  // Music: leave empty until a licensed track is supplied, e.g. 'audio/our-song.mp3' (a file inside this folder).
  const MUSIC_SRC = '';
  const MUHURTHAM = new Date('2026-11-21T21:55:00+05:30');
  // Calendar: 8:00 PM IST start. The 11:00 PM IST end is PROVISIONAL until the family confirms it.
  const CAL = { start: '20261121T143000Z', end: '20261121T173000Z' };
  const TITLE = 'Wedding of Akshay & Priya';
  const DETAILS = 'Wedding dinner 8:00 PM IST · Auspicious muhurtham 9:55 PM IST · End time provisional';
  const VENUE = 'Priyanka Convention, Nallajerla, Andhra Pradesh, India';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const app = $('#app');
  const scenes = { discover: $('#discover'), journey: $('#journey'), invitation: $('#invitation') };
  let current = 'discover';
  const timers = new Set();
  const later = (fn, ms) => { const id = setTimeout(() => { timers.delete(id); fn(); }, ms); timers.add(id); return id; };
  const clearTimers = () => { timers.forEach(clearTimeout); timers.clear(); };

  /* ---------- stage fitting: one scale for artwork + overlays ---------- */
  function fit() {
    const vw = innerWidth, vh = innerHeight;
    $$('.stage').forEach(st => {
      const sw = vw / 941, sh = vh / 1672;
      let s;
      if (st.dataset.fit === 'contain') s = Math.min(sw, sh);
      else s = Math.min(Math.max(sw, sh), Math.min(sw, sh) * 1.18); // cover, but never crop more than ~8% per side on either axis
      st.style.setProperty('--s', s.toFixed(5));
    });
  }
  addEventListener('resize', fit);
  addEventListener('orientationchange', () => setTimeout(fit, 250));
  fit();

  function stagePoint(sceneEl, x, y) {
    const st = sceneEl.querySelector('.stage');
    const r = st.getBoundingClientRect();
    return { x: r.left + x * r.width / 941, y: r.top + y * r.height / 1672 };
  }

  /* ---------- scene switching ---------- */
  function show(name) {
    Object.entries(scenes).forEach(([k, el]) => {
      const on = k === name;
      el.classList.toggle('is-active', on);
      el.setAttribute('aria-hidden', on ? 'false' : 'true');
      el.inert = !on;
    });
    current = name; app.dataset.scene = name;
    try { history.replaceState(null, '', '#' + (name === 'discover' ? 'treasure' : name)); } catch (_) {}
    $('#skipBtn').hidden = name === 'invitation';
    if (name === 'invitation') loadInvite();
  }

  const bloom = $('#bloom');
  function bloomTo(next, pt, after) {
    if (reduce) { show(next); if (after) after(); return; }
    bloom.style.setProperty('--bx', pt.x + 'px'); bloom.style.setProperty('--by', pt.y + 'px');
    const grow = bloom.animate([
      { opacity: 0, clipPath: `circle(0px at ${pt.x}px ${pt.y}px)` },
      { opacity: 1, clipPath: `circle(18% at ${pt.x}px ${pt.y}px)`, offset: .35 },
      { opacity: 1, clipPath: `circle(150% at ${pt.x}px ${pt.y}px)` }
    ], { duration: 1100, easing: 'cubic-bezier(.5,0,.3,1)', fill: 'forwards' });
    grow.onfinish = () => {
      show(next);
      const st = scenes[next].querySelector('.stage');
      st.animate([{ transform: 'translate(-50%,-50%) scale(calc(var(--s) * 1.06))' }, { transform: 'translate(-50%,-50%) scale(var(--s))' }], { duration: 1600, easing: 'cubic-bezier(.2,.7,.2,1)' });
      const fade = bloom.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 1000, easing: 'ease-out', fill: 'forwards' });
      fade.onfinish = () => { grow.cancel(); fade.cancel(); bloom.style.opacity = 0; if (after) after(); };
    };
  }
  function fadeTo(next, after) {
    const el = scenes[next];
    show(next);
    if (!reduce) el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 500, easing: 'ease-out' });
    if (after) after();
  }

  /* ---------- Scene 1 · treasure chest ---------- */
  const chestBtn = $('#chestBtn'), lock = $('#lock'), glint = document.querySelector('.keyhole-glint');
  let chestState = 'closed';
  function openChest() {
    if (chestState !== 'closed') return;
    chestState = 'opening';
    chestBtn.setAttribute('aria-label', 'Opening the treasure');
    lock.classList.add('jiggle');
    later(() => { lock.classList.remove('jiggle'); lock.classList.add('unlocked'); glint.classList.add('on'); }, reduce ? 0 : 560);
    later(() => { scenes.discover.classList.add('is-opening'); }, reduce ? 50 : 820);
    later(() => {
      chestState = 'open';
      bloomTo('journey', stagePoint(scenes.discover, 490, 1240), () => $('#followBtn').focus({ preventScroll: true }));
    }, reduce ? 700 : 2500);
  }
  function resetChest() {
    chestState = 'closed';
    scenes.discover.classList.remove('is-opening');
    lock.classList.remove('jiggle', 'unlocked'); glint.classList.remove('on');
    chestBtn.setAttribute('aria-label', 'Tap to open the treasure');
  }
  chestBtn.addEventListener('click', openChest);

  /* ---------- Scene 2 · flights ---------- */
  const P = window.__ROUTES__;
  const routeT = $('#routeT'), routeG = $('#routeG');
  [['#routeT', '#glowT', '#trailT', P.toronto], ['#routeG', '#glowG', '#trailG', P.germany]].forEach(([a, b, c, d]) => {
    $(a).setAttribute('d', d); $(b).setAttribute('d', d); $(c).setAttribute('d', d);
  });
  const LT = routeT.getTotalLength(), LG = routeG.getTotalLength();
  const trailT = $('#trailT'), trailG = $('#trailG');
  [[trailT, LT], [trailG, LG]].forEach(([el, L]) => { el.style.strokeDasharray = L + ' ' + L; el.style.strokeDashoffset = L; });
  const acT = $('#acT'), acG = $('#acG'), dest = $('#dest'), emblem = $('#emblem');
  const followBtn = $('#followBtn'), status = $('#flightStatus');
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; // easeInOutCubic
  const flight = { running: false, raf: 0, pT: 0, pG: 0 };

  function place(ac, path, L, p) {
    const d = Math.max(0, Math.min(L, p * L));
    const pt = path.getPointAtLength(d);
    const a = path.getPointAtLength(Math.max(0, d - 3)), b = path.getPointAtLength(Math.min(L, d + 3));
    const ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
    const k = 0.92 + 0.22 * Math.sin(Math.PI * p);       // gentle "altitude" swell mid-flight
    ac.setAttribute('transform', `translate(${pt.x.toFixed(2)} ${pt.y.toFixed(2)}) rotate(${ang.toFixed(2)}) scale(${k.toFixed(3)})`);
    const sh = ac.querySelector('.ac-shadow');
    if (sh) sh.setAttribute('cy', (10 + 16 * Math.sin(Math.PI * p)).toFixed(1));
    return pt;
  }
  function setProgress(pT, pG) {
    flight.pT = pT; flight.pG = pG;
    place(acT, routeT, LT, pT); place(acG, routeG, LG, pG);
    trailT.style.strokeDashoffset = LT * (1 - pT);
    trailG.style.strokeDashoffset = LG * (1 - pG);
  }
  function resetFlight() {
    cancelAnimationFrame(flight.raf); flight.running = false;
    dest.classList.remove('arrived'); emblem.classList.remove('on');
    acT.style.opacity = acG.style.opacity = '';
    followBtn.removeAttribute('aria-busy'); followBtn.querySelector('span').textContent = 'Follow the Route'; status.classList.remove('on'); status.textContent = '';
    setProgress(0, 0);
  }
  function fly() {
    if (flight.running) return;
    resetFlight();
    flight.running = true; followBtn.setAttribute('aria-busy', 'true'); followBtn.querySelector('span').textContent = 'Following the route';
    status.textContent = 'Two journeys take flight…'; status.classList.add('on');
    const DUR = 6600, START_G = 500;                     // both aircraft land together at 6.6 s
    const t0 = performance.now();
    const step = now => {
      const t = now - t0;
      const pT = ease(Math.min(1, t / DUR));
      const pG = ease(Math.min(1, Math.max(0, (t - START_G) / (DUR - START_G))));
      setProgress(pT, pG);
      if (t < DUR) { flight.raf = requestAnimationFrame(step); return; }
      arrive();
    };
    flight.raf = requestAnimationFrame(step);
  }
  function arrive() {
    flight.running = false;
    dest.classList.add('arrived');
    status.textContent = 'Every road led here.'; followBtn.querySelector('span').textContent = 'Every road led here';
    [acT, acG].forEach(a => a.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 900, delay: 500, fill: 'forwards', easing: 'ease-in' }));
    later(() => emblem.classList.add('on'), 450);
    later(() => bloomTo('invitation', stagePoint(scenes.journey, 692, 1012), () => status.classList.remove('on')), 2300);
  }
  followBtn.addEventListener('click', fly);
  setProgress(0, 0);

  /* ---------- Scene 3 · invitation ---------- */
  const inviteArt = $('#inviteArt');
  function loadInvite() { if (!inviteArt.getAttribute('src')) inviteArt.src = inviteArt.dataset.src; }
  addEventListener('load', () => setTimeout(loadInvite, 600));

  /* ---------- navigation controls ---------- */
  function skip(e) { if (e) e.preventDefault(); clearTimers(); cancelAnimationFrame(flight.raf); flight.running = false; fadeTo('invitation'); }
  $$('[data-skip]').forEach(b => b.addEventListener('click', skip));
  function replayStory() { closeSheet(); clearTimers(); resetFlight(); resetChest(); fadeTo('discover', () => chestBtn.focus({ preventScroll: true })); }
  function replayFlight() { closeSheet(); clearTimers(); resetFlight(); fadeTo('journey', () => later(fly, reduce ? 0 : 450)); }
  $$('[data-replay]').forEach(b => b.addEventListener('click', replayStory));
  $$('[data-replay-flight]').forEach(b => b.addEventListener('click', replayFlight));

  /* ---------- details sheet ---------- */
  const sheet = $('#sheet'), scrim = $('#scrim');
  let lastFocus = null;
  function openSheet() {
    lastFocus = document.activeElement;
    sheet.hidden = false; scrim.hidden = false;
    $('#sheetClose').focus({ preventScroll: true });
    tick();
  }
  function closeSheet() {
    if (sheet.hidden) return;
    sheet.hidden = true; scrim.hidden = true;
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  $$('[data-open-details]').forEach(b => b.addEventListener('click', openSheet));
  $('#sheetClose').addEventListener('click', closeSheet);
  scrim.addEventListener('click', closeSheet);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeSheet();
    if (e.key === 'Tab' && !sheet.hidden) {
      const f = [...sheet.querySelectorAll('a,button')].filter(x => !x.hidden && x.offsetParent !== null);
      if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });

  /* countdown to the muhurtham */
  const pad = n => String(n).padStart(2, '0');
  function tick() {
    let ms = MUHURTHAM - Date.now();
    if (ms <= 0) { ['cdD', 'cdH', 'cdM', 'cdS'].forEach(id => $('#' + id).textContent = '00'); $('#cdLabel').textContent = 'The muhurtham has begun · India Standard Time'; return; }
    const d = Math.floor(ms / 864e5); ms -= d * 864e5;
    const h = Math.floor(ms / 36e5); ms -= h * 36e5;
    const m = Math.floor(ms / 6e4); ms -= m * 6e4;
    $('#cdD').textContent = d; $('#cdH').textContent = pad(h); $('#cdM').textContent = pad(m); $('#cdS').textContent = pad(Math.floor(ms / 1000));
  }
  tick(); setInterval(tick, 1000);

  /* calendar */
  $('#gcalLink').href = 'https://calendar.google.com/calendar/render?action=TEMPLATE'
    + '&text=' + encodeURIComponent(TITLE)
    + '&dates=' + CAL.start + '/' + CAL.end
    + '&ctz=Asia/Kolkata'
    + '&details=' + encodeURIComponent(DETAILS)
    + '&location=' + encodeURIComponent(VENUE);
  $('#icsBtn').addEventListener('click', () => {
    const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Akshay & Priya//Wedding review//EN', 'CALSCALE:GREGORIAN', 'BEGIN:VEVENT',
      'UID:akshay-priya-wedding-20261121@review', 'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, ''),
      'DTSTART:' + CAL.start, 'DTEND:' + CAL.end, 'SUMMARY:' + TITLE,
      'DESCRIPTION:' + DETAILS.replace(/,/g, '\\,'), 'LOCATION:' + VENUE.replace(/,/g, '\\,'), 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: 'akshay-priya-wedding.ics' });
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 4000);
  });

  /* share */
  const shareURL = () => location.href.split('#')[0];
  async function share() {
    const note = $('#shareNote');
    const data = { title: 'Akshay & Priya · The Treasure We Found', text: 'Saturday, 21 November 2026 · Priyanka Convention, Nallajerla', url: shareURL() };
    try { if (navigator.share) { await navigator.share(data); return; } } catch (e) { if (e && e.name === 'AbortError') return; }
    try { await navigator.clipboard.writeText(data.url); note.textContent = 'Link copied.'; }
    catch (_) { note.textContent = 'Copy this link: ' + data.url; }
    if (sheet.hidden) { status.textContent = note.textContent; }
  }
  $$('[data-share]').forEach(b => b.addEventListener('click', share));

  /* ---------- music module (off by default; no track configured in review builds) ---------- */
  const musicBtn = $('#musicBtn'), musicLabel = $('#musicLabel'), muteBtn = $('#muteBtn');
  let audio = null;
  if (MUSIC_SRC) {
    musicBtn.removeAttribute('aria-disabled'); musicBtn.title = 'Play music';
    musicBtn.setAttribute('aria-pressed', 'false'); musicLabel.textContent = 'Play music';
    musicBtn.addEventListener('click', () => {
      if (!audio) { audio = new Audio(MUSIC_SRC); audio.loop = true; audio.preload = 'auto'; audio.volume = .6; muteBtn.hidden = false; }
      if (audio.paused) { audio.play().then(() => { musicLabel.textContent = 'Pause music'; musicBtn.setAttribute('aria-pressed', 'true'); }).catch(() => {}); }
      else { audio.pause(); musicLabel.textContent = 'Play music'; musicBtn.setAttribute('aria-pressed', 'false'); }
    });
    muteBtn.addEventListener('click', () => { if (!audio) return; audio.muted = !audio.muted; muteBtn.setAttribute('aria-pressed', String(audio.muted)); muteBtn.textContent = audio.muted ? 'Unmute' : 'Mute'; });
    document.addEventListener('visibilitychange', () => { if (document.hidden && audio && !audio.paused) { audio.pause(); musicLabel.textContent = 'Play music'; musicBtn.setAttribute('aria-pressed', 'false'); } });
  } else {
    musicBtn.addEventListener('click', () => { musicBtn.title = 'Music coming soon: the soundtrack has not been added yet'; });
  }

  /* ---------- deep links for review ---------- */
  const h = location.hash.replace('#', '');
  if (h === 'invitation') show('invitation');
  else if (h === 'journey') show('journey');
  else show('discover');

  /* hooks for automated QA */
  window.__treasure = { openChest, fly, skip, replayStory, replayFlight, get state() { return { current, chestState, flight: { ...flight, LT, LG } }; }, setProgress };
})();
