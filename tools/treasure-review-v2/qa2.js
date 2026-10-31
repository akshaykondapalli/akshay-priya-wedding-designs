// End-to-end QA for treasure-review v2 with real taps. Usage: node qa2.js <url> <outDir> <device>
const { chromium, devices } = require('playwright');
const fs = require('fs');
const [url = 'http://127.0.0.1:8765/treasure-review/', out = '/home/claude/qa/treasure2', devName = 'iPhone 15'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch();
  const dev = devices[devName];
  const ctx = await b.newContext({ ...dev });
  const p = await ctx.newPage();
  const errors = [], failed = [];
  p.on('pageerror', e => errors.push(e.message)); p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  p.on('response', r => { if (r.status() >= 400) failed.push(r.status() + ' ' + r.url()); });
  const tag = devName.replace(/\W/g, '');
  const shot = n => p.screenshot({ path: `${out}/${tag}-${n}.png` });
  const tap = async sel => { const bb = await p.locator(sel).boundingBox(); const x = bb.x + bb.width / 2, y = bb.y + bb.height / 2; if (dev.hasTouch) await p.touchscreen.tap(x, y); else await p.mouse.click(x, y); };
  const st = () => p.evaluate(() => window.__treasure.state);
  const R = {};
  await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
  await shot('1-cover');
  R.overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  await tap('#beginBtn'); await p.waitForTimeout(700); await shot('1b-cover-to-chest');
  await p.waitForTimeout(1300); await shot('2-closed-chest'); R.afterBegin = (await st()).s1;
  await tap('#chestBtn'); await p.waitForTimeout(450); await shot('2b-lock');
  await p.waitForTimeout(800); await shot('2c-lid-opening');
  R.lid = await p.evaluate(() => getComputedStyle(document.querySelector('#lid')).transform);
  await p.waitForTimeout(1500); await shot('3-open-chest'); R.afterOpen = (await st()).s1;
  await p.waitForTimeout(3200); await shot('4-map-before'); R.sceneMap = (await st()).current;
  await tap('#followBtn');
  const samples = []; const t0 = Date.now();
  for (const ms of [800, 2200, 3400, 4600, 6000]) {
    await p.waitForTimeout(Math.max(0, ms - (Date.now() - t0)));
    samples.push(await p.evaluate(() => {
      const g = id => { const el = document.querySelector(id); const m = el.transform.baseVal.consolidate().matrix; const r = el.getBoundingClientRect(); return { x: +m.e.toFixed(1), y: +m.f.toFixed(1), rot: +(Math.atan2(m.b, m.a) * 180 / Math.PI).toFixed(1), op: getComputedStyle(el).opacity, onscreen: r.width > 8 && r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth }; };
      const near = (id, x, y) => { const el = document.querySelector(id), L = el.getTotalLength(); let best = 1e9; for (let d = 0; d <= L; d += 2) { const q = el.getPointAtLength(d); best = Math.min(best, Math.hypot(q.x - x, q.y - y)); } return +best.toFixed(2); };
      const T = g('#acT'), G = g('#acG');
      const visiblePlanes = [...document.querySelectorAll('#journey .aircraft')].filter(a => getComputedStyle(a).opacity > 0.5).length;
      return { T, G, offT: near('#routeT', T.x, T.y), offG: near('#routeG', G.x, G.y), visiblePlanes, p: window.__treasure.state.flight.p.map(v => +v.toFixed(3)) };
    }));
    samples[samples.length - 1].ms = ms;
    if (ms === 3400) await shot('5-mid-flight');
    if (ms === 6000) await shot('6-arriving');
  }
  R.samples = samples;
  await p.waitForTimeout(1200); await shot('6b-arrived-heart');
  await p.waitForTimeout(3500); await shot('7-invitation'); R.sceneEnd = (await st()).current;
  R.cardsOn = await p.evaluate(() => document.querySelector('#cardBar').classList.contains('on'));
  await tap('#cardBar [data-open-details]'); await p.waitForTimeout(700); await shot('8-details');
  R.sheet = await p.evaluate(() => ({ text: document.querySelector('#sheet').innerText.replace(/\s+/g, ' '), gcal: document.querySelector('#gcalLink').href, maps: document.querySelector('#mapsLink').href, music: document.querySelector('#musicBtn').getAttribute('aria-pressed') }));
  await tap('#sheet [data-calendar]'); await p.waitForTimeout(300); await shot('8b-calendar');
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 4000 }).catch(() => null), tap('#icsBtn')]);
  R.ics = dl ? fs.readFileSync(await dl.path(), 'utf8').split('\r\n').filter(l => /DT|SUMMARY|LOCATION/.test(l)) : 'none';
  await tap('#sheetClose'); await p.waitForTimeout(300);
  await tap('#cardBar [data-replay]'); await p.waitForTimeout(800); R.replay = await st();
  await p.evaluate(() => document.querySelector('.skiplink').click()); await p.waitForTimeout(800); R.skip = (await st()).current; R.galleryLinks = await p.evaluate(() => [...document.querySelectorAll('a')].filter(a => /index\.html|five-concepts\/?$|All designs|All five/i.test(a.getAttribute('href') + ' ' + a.textContent)).length); R.reviewText = await p.evaluate(() => (document.body.innerText.match(/review|design concept|coming soon|All designs/i) || [null])[0]);
  R.forbidden = await p.evaluate(() => (document.documentElement.textContent.match(/pellikoduku|lunch|morning|reception|haldi|sangeet|mehendi/i) || [null])[0]);
  R.errors = errors; R.failed = failed;
  fs.writeFileSync(`${out}/${tag}-report.json`, JSON.stringify(R, null, 1));
  console.log(JSON.stringify({ gallery: R.galleryLinks, reviewText: R.reviewText, dev: devName, overflow: R.overflow, afterBegin: R.afterBegin, afterOpen: R.afterOpen, sceneMap: R.sceneMap, sceneEnd: R.sceneEnd, cardsOn: R.cardsOn,
    maxOff: Math.max(...samples.map(s => Math.max(s.offT, s.offG))), planesVisible: samples.map(s => s.visiblePlanes), progress: samples.map(s => s.p), onscreen: samples.map(s => s.T.onscreen && s.G.onscreen),
    replay: R.replay.current + '/' + R.replay.s1, skip: R.skip, forbidden: R.forbidden, music: R.sheet.music, ics: R.ics, errors, failed }));
  await b.close();
})();
