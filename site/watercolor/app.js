/* Living Watercolor — interactions. No dependencies. */
(() => {
  'use strict';
  const root = document.documentElement;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  let motion = !reduce.matches;
  if (motion) root.classList.add('motion');
  let revealedAll = false;

  /* ---------------- menu ---------------- */
  const btn = document.querySelector('.menu-btn');
  const menu = document.getElementById('menu');
  const closeMenu = (focusBtn) => {
    menu.hidden = true; btn.setAttribute('aria-expanded', 'false');
    if (focusBtn) btn.focus();
  };
  btn.addEventListener('click', () => {
    const open = menu.hidden;
    menu.hidden = !open; btn.setAttribute('aria-expanded', String(open));
    if (open) menu.querySelector('a').focus();
  });
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) closeMenu(false); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !menu.hidden) closeMenu(true); });
  document.addEventListener('click', (e) => {
    if (!menu.hidden && !menu.contains(e.target) && e.target !== btn) closeMenu(false);
  });

  /* ---------------- paint-spreading reveal ----------------
     The painting is drawn through a mask whose threshold field = distance from a
     seed point + fractal noise, so the paint creeps outward with an irregular,
     wet front. A thin band at the front is darkened in the paint's own pigment
     (the "wet edge" that forms where a wash dries). */
  function hash(x, y) {
    let h = x * 374761393 + y * 668265263; h = (h ^ (h >>> 13)) * 1274126177;
    return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
  }
  function vnoise(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  function fbm(x, y) { return vnoise(x, y) * .55 + vnoise(x * 2.1, y * 2.1) * .3 + vnoise(x * 4.3, y * 4.3) * .15; }

  const paintings = [...document.querySelectorAll('img[data-paint]')];
  const finish = (img) => {
    img.classList.add('is-painted');
    if (img._canvas) { img._canvas.remove(); img._canvas = null; }
    img._done = true;
  };

  function paint(img) {
    if (img._started) return;
    img._started = true;
    if (!motion || revealedAll) { finish(img); return; }
    const go = () => {
      const fig = img.parentElement;
      const nw = img.naturalWidth || +img.getAttribute('width');
      const nh = img.naturalHeight || +img.getAttribute('height');
      const scale = Math.min(1, 900 / nw);
      const w = Math.round(nw * scale), h = Math.round(nh * scale);
      const cv = document.createElement('canvas');
      cv.width = w; cv.height = h; cv.setAttribute('aria-hidden', 'true');
      fig.appendChild(cv); img._canvas = cv;
      const ctx = cv.getContext('2d');
      const mw = 150, mh = Math.round(150 * h / w);
      const mc = document.createElement('canvas'); mc.width = mw; mc.height = mh;
      const rc = document.createElement('canvas'); rc.width = mw; rc.height = mh;
      const mctx = mc.getContext('2d'), rctx = rc.getContext('2d');
      const mimg = mctx.createImageData(mw, mh), rimg = rctx.createImageData(mw, mh);
      const [sx, sy] = (img.dataset.seed || '0.5,0.5').split(',').map(Number);
      const pig = (img.dataset.pigment || '120,110,150').split(',').map(Number);
      const thr = new Float32Array(mw * mh);
      const asp = mh / mw;
      let maxd = 0;
      for (let y = 0; y < mh; y++) for (let x = 0; x < mw; x++) {
        const dx = x / mw - sx, dy = (y / mh - sy) * asp;
        const d = Math.sqrt(dx * dx + dy * dy); thr[y * mw + x] = d; if (d > maxd) maxd = d;
      }
      const off = Math.random() * 100;
      for (let y = 0; y < mh; y++) for (let x = 0; x < mw; x++) {
        const i = y * mw + x;
        thr[i] = thr[i] / maxd * .74 + fbm(x / 14 + off, y / 14) * .34;
      }
      for (let i = 0; i < mw * mh; i++) { rimg.data[i * 4] = pig[0]; rimg.data[i * 4 + 1] = pig[1]; rimg.data[i * 4 + 2] = pig[2]; }
      const dur = +(img.dataset.dur || 2600);
      const t0 = performance.now();
      const frame = (now) => {
        if (img._done) return;
        let p = Math.min(1, (now - t0) / dur);
        p = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
        const t = -0.06 + p * 1.2, soft = .07;
        for (let i = 0; i < mw * mh; i++) {
          let a = (t - thr[i]) / soft; a = a < 0 ? 0 : a > 1 ? 1 : a;
          mimg.data[i * 4 + 3] = a * 255;
          rimg.data[i * 4 + 3] = a * (1 - a) * 4 * 110;
        }
        mctx.putImageData(mimg, 0, 0); rctx.putImageData(rimg, 0, 0);
        ctx.globalCompositeOperation = 'source-over';
        ctx.clearRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0, w, h);
        ctx.globalCompositeOperation = 'destination-in';
        ctx.drawImage(mc, 0, 0, w, h);
        ctx.globalCompositeOperation = 'source-atop';
        ctx.drawImage(rc, 0, 0, w, h);
        if (p < 1) requestAnimationFrame(frame); else finish(img);
      };
      requestAnimationFrame(frame);
    };
    if (img.complete && img.naturalWidth) go();
    else img.addEventListener('load', go, { once: true });
    img.addEventListener('error', () => finish(img), { once: true });
  }

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { paint(e.target); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.05 });
    paintings.forEach((img) => io.observe(img));
  } else paintings.forEach(finish);

  /* ---------------- the two journeys ---------------- */
  const journey = document.getElementById('journey');
  const pRose = document.getElementById('p-rose');
  const pBlue = document.getElementById('p-blue');
  const bloomC = document.getElementById('bloom-c');
  const bloomG = document.getElementById('bloom-g');
  const Lr = pRose.getTotalLength(), Lb = pBlue.getTotalLength();
  pRose.style.strokeDasharray = Lr; pBlue.style.strokeDasharray = Lb;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const ease = (v) => v * v * (3 - 2 * v);
  function setJourney(p) {
    const a = ease(clamp(p / 0.5)), b = ease(clamp((p - 0.04) / 0.5));
    pRose.style.strokeDashoffset = Lr * (1 - a);
    pBlue.style.strokeDashoffset = Lb * (1 - b);
    const bl = ease(clamp((p - 0.5) / 0.28));
    bloomC.setAttribute("r", (bl * 340).toFixed(1));
    const grow = 1 + 0.25 * ease(clamp((p - 0.8) / 0.2));
    bloomG.setAttribute('transform', `translate(590 860) scale(${grow.toFixed(3)}) translate(-590 -860)`);
  }
  let ticking = false;
  function onScroll() {
    ticking = false;
    if (!motion || revealedAll) return;
    const r = journey.getBoundingClientRect();
    const span = r.height - window.innerHeight;
    setJourney(clamp(-r.top / (span > 0 ? span : 1)));
  }
  if (motion) {
    setJourney(0);
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
  } else setJourney(1);

  reduce.addEventListener?.('change', (e) => {
    motion = !e.matches; root.classList.toggle('motion', motion);
    if (!motion) { setJourney(1); paintings.forEach(finish); }
  });

  /* ---------------- skipping & full reveal ---------------- */
  function revealAll() {
    revealedAll = true;
    paintings.forEach((img) => { img._started = true; finish(img); });
    setJourney(1);
    document.querySelectorAll('.arrival-text>*').forEach((el) => { el.style.animation = 'none'; });
  }
  window.atlasReveal = revealAll;
  document.querySelectorAll('[data-skip], .skip-link').forEach((a) => a.addEventListener('click', revealAll));

  /* ---------------- countdown (Asia/Kolkata) ---------------- */
  const target = Date.parse('2026-11-21T20:00:00+05:30');
  const units = { d: document.querySelector('[data-u="d"]'), h: document.querySelector('[data-u="h"]'), m: document.querySelector('[data-u="m"]') };
  function tick() {
    let s = Math.max(0, Math.floor((target - Date.now()) / 1000));
    const d = Math.floor(s / 86400); s -= d * 86400;
    const h = Math.floor(s / 3600); s -= h * 3600;
    const m = Math.floor(s / 60);
    units.d.textContent = d; units.h.textContent = String(h).padStart(2, '0'); units.m.textContent = String(m).padStart(2, '0');
  }
  tick(); setInterval(tick, 30000);

  /* ---------------- calendar file ---------------- */
  document.getElementById('ics').addEventListener('click', () => {
    const ics = [
      'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//The Atlas of Us//Wedding//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      'UID:akshay-priya-wedding-20261121@atlas-of-us',
      'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, ''),
      'DTSTART:20261121T143000Z', 'DTEND:20261121T173000Z',
      'SUMMARY:Wedding of Akshay & Priya',
      'DESCRIPTION:Wedding dinner 8:00 PM IST · Wedding muhurtham 9:55 PM IST',
      'LOCATION:Priyanka Convention\\, Nallajerla\\, Andhra Pradesh\\, India',
      'END:VEVENT', 'END:VCALENDAR', ''
    ].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url; a.download = 'akshay-priya-wedding.ics';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  });

  /* ---------------- share ---------------- */
  const status = document.getElementById('share-status');
  document.getElementById('share').addEventListener('click', async () => {
    const data = { title: 'Akshay & Priya · Wedding invitation', text: 'Saturday, 21 November 2026 · Priyanka Convention, Nallajerla', url: location.href.split('#')[0] };
    if (navigator.share) {
      try { await navigator.share(data); status.textContent = ''; return; } catch (e) { if (e.name === 'AbortError') return; }
    }
    try { await navigator.clipboard.writeText(data.url); status.textContent = 'Link copied. Paste it wherever you would like to share it.'; }
    catch (e) { status.textContent = 'Copy this link: ' + data.url; }
  });
})();
