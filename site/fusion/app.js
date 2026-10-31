/* The Atlas of Us — 04 Cinematic + Watercolor Fusion */
(() => {
  'use strict';
  const doc = document.documentElement;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const seg = (p, a, b) => clamp((p - a) / (b - a));
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const easeOut = t => 1 - Math.pow(1 - t, 3);
  const mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  let reduce = mqReduce.matches;
  let revealed = false;            // set by window.atlasReveal()
  const status = $('[data-status]');
  const say = msg => { if (status) { status.textContent = msg; clearTimeout(say.t); say.t = setTimeout(() => status.textContent = '', 5000); } };

  if (reduce) doc.classList.add('rm'); else doc.classList.add('motion');

  /* ---------------- menu ---------------- */
  const menu = $('[data-menu]'), menuBtn = $('[data-menu-btn]');
  const openMenu = open => {
    menu.hidden = !open;
    menuBtn.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) (menu.querySelector('a') || menu).focus(); else menuBtn.focus();
  };
  menuBtn.addEventListener('click', () => openMenu(menu.hidden));
  $('[data-menu-close]').addEventListener('click', () => openMenu(false));
  menu.addEventListener('click', e => { if (e.target.closest('a')) { menu.hidden = true; menuBtn.setAttribute('aria-expanded', 'false'); document.body.style.overflow = ''; } });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !menu.hidden) openMenu(false);
    if (e.key === 'Tab' && !menu.hidden) {
      const f = $$('a,button', menu); const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  // show the skip link while the intro is on screen
  const skip = $('[data-skip]');

  // smooth in-page jumps (instant under reduced motion)
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;
    const id = a.getAttribute('href').slice(1);
    const t = document.getElementById(id);
    if (!t) return;
    e.preventDefault();
    let top = t.getBoundingClientRect().top + scrollY;
    if (a.hasAttribute('data-open-atlas')) top = $('#arrival').offsetTop + $('#arrival').offsetHeight * 0.55 - innerHeight * 0.55;
    if (id === 'destination' && !reduce) top = t.offsetTop + t.offsetHeight - innerHeight; // land on the finished scene
    window.scrollTo({ top, behavior: reduce ? 'auto' : 'smooth' });
    history.replaceState(null, '', '#' + id);
    if (!t.hasAttribute('tabindex')) t.setAttribute('tabindex', '-1');
    t.focus({ preventScroll: true });
  });

  /* ---------------- I · atlas ---------------- */
  const arrival = $('#arrival'), book = $('[data-book]'), cover = $('[data-cover]');
  const desk = $('.arrival__desk'), arrMap = $('.arrival__map'), arrCopy = $('[data-arrival-copy]');

  let bookBox = null;
  function measureBook() {
    const t = book.style.transform; book.style.transform = 'none';
    bookBox = { left: book.offsetLeft, top: book.offsetTop, w: book.offsetWidth, h: book.offsetHeight };
    book.style.transform = t;
  }
  function updateSkip() {
    const a = arrival.getBoundingClientRect(), d = dest.getBoundingClientRect();
    const intro = -a.top > (arrival.offsetHeight - innerHeight) * 0.18 && d.bottom > innerHeight * 1.05;
    skip.classList.toggle('is-shown', intro && !reduce && menu.hidden);
  }
  function updateArrival() {
    const r = arrival.getBoundingClientRect();
    if (r.bottom < 0 || r.top > innerHeight) return;
    if (!bookBox) measureBook();
    const total = arrival.offsetHeight - innerHeight;
    let p = reduce ? 0 : clamp(-r.top / Math.max(total, 1));
    if (revealed && p < 0.42) p = 0.42;
    const vw = innerWidth, vh = innerHeight;
    const { left: l0, top: t0, w: bw, h: bh } = bookBox;
    const cyc = t0 + bh / 2;
    // A · the cover swings open (0.02 → 0.38) while the camera pulls back to frame the spread
    const a = ease(seg(p, 0.02, 0.38));
    cover.style.transform = `rotateY(${-178 * a}deg)`;
    cover.style.setProperty('--sheen', String(0.5 + a));
    const fit = Math.min(1, (vw * 0.94) / (bw * 2), (vh * 0.72) / bh);
    const sO = 1 + (fit - 1) * a;
    const xO = l0 + (vw / 2 - l0) * a;          // spine travels to the centre
    const yO = cyc - (bh / 2) * sO;
    // C · dive into the right-hand page (0.5 → 0.96)
    const d = ease(seg(p, 0.5, 0.96));
    const sC = Math.max(vw / bw, vh / bh) * 1.06;
    const s = Math.exp(Math.log(sO) + (Math.log(sC) - Math.log(sO)) * d);
    // keep the page centre on a straight line toward the viewport centre
    const pcx0 = xO + (bw / 2) * sO, pcy0 = yO + (bh / 2) * sO;
    const pcx = pcx0 + (vw / 2 - pcx0) * d, pcy = pcy0 + (vh / 2 - pcy0) * d;
    const X = pcx - (bw / 2) * s, Y = pcy - (bh / 2) * s;
    book.style.transform = `translate3d(${(X - l0).toFixed(2)}px, ${(Y - t0).toFixed(2)}px, 0) scale(${s.toFixed(4)})`;
    desk.style.transform = `scale(${(1 + 0.05 * a + 0.6 * d).toFixed(4)})`;
    desk.style.filter = d > 0 ? `blur(${(d * 6).toFixed(1)}px) brightness(${(1 - d * 0.4).toFixed(2)})` : '';
    arrMap.style.opacity = String(seg(p, 0.84, 0.97));
    arrCopy.style.opacity = String(1 - seg(p, 0.05, 0.18));
    arrCopy.style.visibility = p > 0.18 ? 'hidden' : '';
  }

  /* ---------------- II–III · routes ---------------- */
  const mapwrap = $('[data-mapwrap]');
  const routes = { one: $('[data-route="one"]'), two: $('[data-route="two"]') };
  const lens = {};
  const stopsG = $('[data-stops]');
  const meet = $('[data-meet]');
  const joined = $('[data-joined]'), joinedBase = $('[data-joined-base]');
  const SVGNS = 'http://www.w3.org/2000/svg';
  const stops = [];
  for (const k of ['one', 'two']) {
    const path = routes[k];
    const L = path.getTotalLength();
    lens[k] = L;
    path.style.strokeDasharray = k === 'one' ? '1 15' : `${L} ${L}`;
    // waypoints (unlabelled) along each route
    [0.3, 0.55, 0.8].forEach(t => {
      const pt = path.getPointAtLength(L * t);
      const c = document.createElementNS(SVGNS, 'circle');
      c.setAttribute('cx', pt.x.toFixed(1)); c.setAttribute('cy', pt.y.toFixed(1)); c.setAttribute('r', '9');
      c.setAttribute('class', 'stop stop--' + k); c.style.opacity = '0';
      stopsG.appendChild(c); stops.push({ el: c, k, t });
    });
  }
  // woven joined route: two strands braided along the base curve
  const JL = joinedBase.getTotalLength();
  const weave = (phase, color) => {
    const n = 120; let d = '';
    for (let i = 0; i <= n; i++) {
      const l = JL * i / n;
      const p = joinedBase.getPointAtLength(l), q = joinedBase.getPointAtLength(Math.min(JL, l + 1));
      const tx = q.x - p.x, ty = q.y - p.y, m = Math.hypot(tx, ty) || 1;
      const off = 9 * Math.sin(i / n * Math.PI * 9 + phase);
      d += (i ? 'L' : 'M') + (p.x - ty / m * off).toFixed(1) + ' ' + (p.y + tx / m * off).toFixed(1);
    }
    const el = document.createElementNS(SVGNS, 'path');
    el.setAttribute('d', d); el.setAttribute('class', 'weave'); el.setAttribute('stroke', color);
    joined.appendChild(el);
    const L = el.getTotalLength();
    el.style.strokeDasharray = `${L} ${L}`; el.style.strokeDashoffset = String(L);
    return { el, L };
  };
  const strands = [weave(0, '#b88a35'), weave(Math.PI, '#c0596a')];
  joinedBase.style.strokeDasharray = `${JL} ${JL}`;
  const glow = $('.meet__glow', meet), ring = $('.meet__ring', meet), star = $('.meet__star', meet);

  function drawRoutes(p) {
    // p 0..1 across Two Souls + Connection
    const draw = easeOut(seg(p, 0.0, 0.55));
    // route one is dotted: reveal by masking with a growing dash on a wrapper -> use dashoffset on a solid copy
    routes.two.style.strokeDashoffset = String(lens.two * (1 - draw));
    oneMask(draw);
    stops.forEach(s => { s.el.style.opacity = draw >= s.t ? '1' : '0'; });
    const m = seg(p, 0.52, 0.68);
    glow.style.opacity = String(m);
    glow.setAttribute('r', String(80 + 60 * easeOut(m)));
    ring.style.opacity = star.style.opacity = String(m);
    const j = easeOut(seg(p, 0.62, 0.98));
    strands.forEach(s => { s.el.style.strokeDashoffset = String(s.L * (1 - j)); });
    joinedBase.style.strokeDashoffset = String(JL * (1 - j));
  }
  const halo1 = $('.route--one .route__halo'), halo2 = $('.route--two .route__halo');
  halo1.style.strokeDasharray = `${lens.one} ${lens.one}`;
  halo2.style.strokeDasharray = `${lens.two} ${lens.two}`;
  let lastOne = -1;
  function oneMask(draw) {
    const D = lens.one * draw;
    const n = Math.floor(D / 16);
    if (n !== lastOne) {
      lastOne = n;
      routes.one.style.strokeDasharray = n > 0 ? '1 15 '.repeat(n) + `0 ${lens.one + 20}` : `0 ${lens.one + 20}`;
    }
    halo1.style.strokeDashoffset = String(lens.one - D);
    halo2.style.strokeDashoffset = String(lens.two * (1 - draw));
  }

  function updateMap() {
    const r = mapwrap.getBoundingClientRect();
    if (r.bottom < 0 || r.top > innerHeight) return;
    const total = mapwrap.offsetHeight - innerHeight;
    let p = reduce ? 1 : clamp((-r.top + innerHeight * 0.15) / Math.max(total, 1));
    if (revealed) {
      const st = $('#souls').getBoundingClientRect().top, ct = $('#connection').getBoundingClientRect().top;
      if (ct <= 2) p = Math.max(p, 1); else if (st <= 2) p = Math.max(p, 0.45);
    }
    drawRoutes(p);
  }

  /* ---------------- IV · destination (WebGL) ---------------- */
  const dest = $('#destination'), canvas = $('[data-dest-canvas]');
  const destCopy = $('.dest__copy');
  const fbReal = $('.dest__real'), fbWater = $('.dest__water');
  let gl = null, prog = null, uni = {}, lamps = [], texReady = 0, destP = 0, needDraw = true;
  const big = Math.max(screen.width, screen.height) * Math.min(devicePixelRatio || 1, 2) > 1300;
  const src = n => `img/${n}${big ? '' : '-1100'}.webp`;

  const VS = `attribute vec2 p;varying vec2 v;void main(){v=p*.5+.5;gl_Position=vec4(p,0.,1.);}`;
  const FS = `precision highp float;
varying vec2 v;
uniform sampler2D uMap,uWater,uReal;
uniform vec2 uRes;uniform float uP1,uP2,uZoom,uTime,uIgn,uCy;
uniform vec4 uL[31];
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float s=0.,a=.5;for(int i=0;i<4;i++){s+=a*n(p);p*=2.03;a*=.5;}return s;}
void main(){
 vec2 fc=v*uRes;
 float m=max(uRes.x,uRes.y);
 vec2 uv=vec2(.5,uCy)+(fc-uRes*.5)/m/uZoom*vec2(1.,-1.);
 uv=clamp(uv,0.,1.);
 vec3 cm=texture2D(uMap,uv).rgb, cw=texture2D(uWater,uv).rgb, cr=texture2D(uReal,uv).rgb;
 // stage 1: the painted map dissolves into the painted courtyard, blooming outward from where the roads met
 float f1=fbm(uv*5.5)*.55+distance(uv,vec2(.5,.6))*.9;
 float t1=uP1*1.35-.12;
 float m1=smoothstep(t1+.035,t1-.035,f1);
 float e1=smoothstep(.0,.5,m1)*smoothstep(1.,.5,m1);
 vec3 c=mix(cm,cw,m1);
 c*=1.-e1*.22;                         // pigment pooling at the wet edge
 // lamps ignite on the painting, one group at a time
 vec3 glow=vec3(0.);
 for(int i=0;i<31;i++){
  vec4 L=uL[i];
  if(L.w<=0.)continue;
  vec2 d=(uv-L.xy);d.y*=1.;float r2=dot(d,d);
  float s=L.z;
  float fl=.88+.12*sin(uTime*7.+float(i)*1.7)*sin(uTime*3.1+float(i));
  glow+=L.w*fl*(vec3(1.,.86,.6)*exp(-r2/(2.*s*s*.12))*.9+vec3(1.,.6,.25)*exp(-r2/(2.*s*s*2.2))*.22);
 }
 // stage 2: realism floods in from the mandapam, a warm light-front leads the edge
 float f2=fbm(uv*4.+7.3)*.5+distance(uv*vec2(1.,1.25),vec2(.5,.58*1.25))*.85;
 float t2=uP2*1.4-.15;
 float m2=smoothstep(t2+.05,t2-.05,f2);
 float e2=smoothstep(.0,.5,m2)*smoothstep(1.,.5,m2);
 c=mix(c,cr,m2);
 c+=glow*(1.-m2)*uIgn;
 c+=e2*vec3(1.,.72,.4)*.28;
 gl_FragColor=vec4(c,1.);
}`;

  function initGL() {
    if (reduce) return false;
    try {
      gl = canvas.getContext('webgl', { antialias: false, alpha: false, premultipliedAlpha: false, powerPreference: 'high-performance' });
    } catch (e) { gl = null; }
    if (!gl) return false;
    const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
    try {
      prog = gl.createProgram();
      gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error('link');
    } catch (e) { gl = null; return false; }
    gl.useProgram(prog);
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    ['uMap', 'uWater', 'uReal', 'uRes', 'uP1', 'uP2', 'uZoom', 'uTime', 'uIgn', 'uL', 'uCy'].forEach(k => uni[k] = gl.getUniformLocation(prog, k));
    [['map', 0, 'uMap'], ['scene-water', 1, 'uWater'], ['scene-real', 2, 'uReal']].forEach(([name, unit, u]) => {
      const img = new Image();
      img.decoding = 'async';
      img.onload = () => {
        const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.uniform1i(uni[u], unit);
        texReady++;
        if (texReady === 3) { doc.classList.add('has-gl'); needDraw = true; }
      };
      img.onerror = () => { gl = null; doc.classList.remove('has-gl'); };
      img.src = src(name);
    });
    canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); gl = null; doc.classList.remove('has-gl'); });
    return true;
  }

  fetch('img/lamps.json').then(r => r.json()).then(j => { lamps = j; needDraw = true; }).catch(() => { lamps = []; });

  function sizeCanvas() {
    if (!gl) return;
    const dpr = Math.min(devicePixelRatio || 1, 1.5);
    const w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; gl.viewport(0, 0, w, h); needDraw = true; }
  }

  function destProgress() {
    const r = dest.getBoundingClientRect();
    const total = dest.offsetHeight - innerHeight;
    let p = clamp(-r.top / Math.max(total, 1));
    if (revealed) p = 1;
    return p;
  }

  function stagesFor(p) {
    return {
      p1: ease(seg(p, 0.02, 0.36)),
      ign: seg(p, 0.30, 0.40),
      p2: ease(seg(p, 0.52, 0.94)),
      zoom: 1 + 0.07 * ease(seg(p, 0.0, 1.0)),
      lampP: seg(p, 0.34, 0.62)
    };
  }

  function drawDest(time) {
    if (!gl || texReady < 3) return;
    sizeCanvas();
    const st = stagesFor(destP);
    const arr = new Float32Array(31 * 4);
    const groups = 9;
    lamps.slice(0, 31).forEach((l, i) => {
      const on = clamp((st.lampP * (groups + 1) - l.g) / 1.0);
      arr[i * 4] = l.x; arr[i * 4 + 1] = l.y; arr[i * 4 + 2] = Math.max(l.s, 0.006); arr[i * 4 + 3] = easeOut(on);
    });
    gl.uniform4fv(uni.uL, arr);
    gl.uniform2f(uni.uRes, canvas.width, canvas.height);
    gl.uniform1f(uni.uP1, st.p1); gl.uniform1f(uni.uP2, st.p2);
    gl.uniform1f(uni.uZoom, st.zoom); gl.uniform1f(uni.uTime, time / 1000); gl.uniform1f(uni.uIgn, st.ign);
    gl.uniform1f(uni.uCy, canvas.width < canvas.height ? 0.5 : 0.41);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  function updateDest() {
    destP = destProgress();
    const st = stagesFor(destP);
    destCopy.classList.toggle('is-early', destP < 0.6 && !reduce && !revealed);
    if (!gl && !reduce) {
      // no WebGL: scroll-linked crossfade between the two paintings
      fbWater.style.opacity = String(1 - st.p2);
      fbReal.style.opacity = String(st.p2);
      if (destP < 0.3) { fbWater.style.opacity = '1'; }
    }
  }

  /* ---------------- loop ---------------- */
  let ticking = false;
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }
  function frame(t) {
    ticking = false;
    updateArrival(); updateMap(); updateDest(); updateSkip();
    const r = dest.getBoundingClientRect();
    const destVisible = r.top < innerHeight && r.bottom > 0;
    if (destVisible) drawDest(t || performance.now());
    // keep the lamp flames flickering (≈24 fps) while they are lit and on screen
    if (!reduce && gl && destVisible && stagesFor(destP).ign > 0) {
      clearTimeout(frame.t);
      frame.t = setTimeout(() => { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }, 42);
    }
  }

  if (!reduce) initGL();
  if (reduce) {
    // reduced motion: gentle cross-fade from painting to the lit courtyard when it comes into view
    fbReal.classList.add('is-faded');
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { fbReal.classList.remove('is-faded'); io.disconnect(); } }), { threshold: 0.5 });
    io.observe(dest);
  }
  mqReduce.addEventListener?.('change', () => location.reload());
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', () => { needDraw = true; bookBox = null; onScroll(); });
  onScroll();

  window.atlasReveal = () => {
    revealed = true;
    if (reduce) fbReal.classList.remove('is-faded');
    destCopy.classList.remove('is-early');
    onScroll();
    return true;
  };

  /* ---------------- details: countdown, calendar file, share ---------------- */
  const target = Date.parse('2026-11-21T20:00:00+05:30');
  const cd = { d: $('[data-cd="d"]'), h: $('[data-cd="h"]'), m: $('[data-cd="m"]') };
  function tick() {
    let ms = target - Date.now();
    const box = $('[data-countdown]');
    if (ms <= 0) { box.querySelector('.countdown__label').textContent = 'The celebration has begun'; cd.d.textContent = cd.h.textContent = cd.m.textContent = '0'; return; }
    const d = Math.floor(ms / 864e5); ms -= d * 864e5;
    const h = Math.floor(ms / 36e5); ms -= h * 36e5;
    const m = Math.floor(ms / 6e4);
    cd.d.textContent = String(d); cd.h.textContent = String(h).padStart(2, '0'); cd.m.textContent = String(m).padStart(2, '0');
  }
  tick(); setInterval(tick, 30000);

  $('[data-ics]').addEventListener('click', () => {
    const ics = [
      'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//The Atlas of Us//Wedding//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      'UID:akshay-priya-wedding-20261121@atlas-of-us',
      'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, ''),
      'DTSTART:20261121T143000Z', 'DTEND:20261121T173000Z',
      'SUMMARY:Wedding of Akshay & Priya',
      'DESCRIPTION:Wedding dinner 8:00 PM IST · Muhurtham 9:55 PM IST',
      'LOCATION:Priyanka Convention\\, Nallajerla\\, Andhra Pradesh\\, India',
      'END:VEVENT', 'END:VCALENDAR'
    ].join('\r\n');
    try {
      const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }));
      const a = document.createElement('a'); a.href = url; a.download = 'akshay-priya-wedding.ics';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 4000);
      say('Calendar file prepared. If nothing downloaded, use “Add to Google Calendar”.');
    } catch (e) { say('This browser blocked the download. Use “Add to Google Calendar” instead.'); }
  });

  $('[data-share]').addEventListener('click', async () => {
    const url = location.href.split('#')[0];
    const data = { title: 'Akshay & Priya · Wedding invitation', text: 'Wedding of Akshay & Priya — Saturday, 21 November 2026, Priyanka Convention, Nallajerla.', url };
    if (navigator.share) {
      try { await navigator.share(data); return; } catch (e) { if (e && e.name === 'AbortError') return; }
    }
    try { await navigator.clipboard.writeText(url); say('Link copied.'); }
    catch (e) { window.prompt ? say('Copy this link: ' + url) : say(url); }
  });
})();
