// QA for treasure-review: real taps, state screenshots, aircraft path accuracy, overflow, errors.
// Usage: node qa.js <baseURL> <outDir> [deviceName]
const { chromium, devices } = require('playwright');
const fs = require('fs');
const base = process.argv[2] || 'http://127.0.0.1:8765/treasure-review/';
const out = process.argv[3] || '/home/claude/qa/treasure';
const devName = process.argv[4] || 'iPhone 15';
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices[devName] });
  const p = await ctx.newPage();
  const errors = [], failed = [];
  p.on('pageerror', e => errors.push(e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  p.on('response', r => { if (r.status() >= 400) failed.push(r.status() + ' ' + r.url()); });
  p.on('requestfailed', r => failed.push('FAIL ' + r.url()));
  const tag = devName.replace(/\W/g, '');
  const tap = (x, y) => devices[devName].hasTouch ? p.touchscreen.tap(x, y) : p.mouse.click(x, y);
  const shot = n => p.screenshot({ path: `${out}/${tag}-${n}.png` });
  const R = {};
  await p.goto(base, { waitUntil: 'networkidle' });
  await p.waitForTimeout(600);
  await shot('01-opening');
  R.overflow1 = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  // real tap on the chest
  const box = await p.locator('#chestBtn').boundingBox();
  await tap(box.x + box.width / 2, box.y + box.height * 0.3);
  await p.waitForTimeout(400); await shot('02-lock-jiggle');
  await p.waitForTimeout(1300); await shot('03-lid-opening');
  R.lidTransform = await p.evaluate(() => getComputedStyle(document.querySelector('#lid')).transform);
  await p.waitForTimeout(700); await shot('04-light-bloom');
  await p.waitForTimeout(2600); await shot('05-map');
  R.sceneAfterChest = await p.evaluate(() => window.__treasure.state.current);
  // route geometry vs painted pins
  R.routeEnds = await p.evaluate(() => {
    const f = id => { const el = document.querySelector(id), L = el.getTotalLength(); const a = el.getPointAtLength(0), z = el.getPointAtLength(L); return { L: +L.toFixed(1), start: [+a.x.toFixed(1), +a.y.toFixed(1)], end: [+z.x.toFixed(1), +z.y.toFixed(1)] }; };
    return { toronto: f('#routeT'), germany: f('#routeG') };
  });
  // tap Follow the Route and sample aircraft positions over time
  const fb = await p.locator('#followBtn').boundingBox();
  await tap(fb.x + fb.width / 2, fb.y + fb.height / 2);
  const samples = [];
  const t0 = Date.now();
  for (const ms of [700, 2000, 3300, 4600, 5900]) {
    await p.waitForTimeout(ms - (Date.now() - t0));
    const s = await p.evaluate(() => {
      const g = id => { const m = document.querySelector(id).transform.baseVal.consolidate().matrix; return [+m.e.toFixed(1), +m.f.toFixed(1), +(Math.atan2(m.b, m.a) * 180 / Math.PI).toFixed(1)]; };
      // distance from aircraft centre to nearest point on its route
      const near = (id, x, y) => { const el = document.querySelector(id), L = el.getTotalLength(); let best = 1e9; for (let d = 0; d <= L; d += 2) { const q = el.getPointAtLength(d); best = Math.min(best, Math.hypot(q.x - x, q.y - y)); } return +best.toFixed(2); };
      const T = g('#acT'), G = g('#acG');
      return { T, G, offT: near('#routeT', T[0], T[1]), offG: near('#routeG', G[0], G[1]), st: window.__treasure.state.flight };
    });
    samples.push({ ms, ...s, opT: await p.evaluate(() => getComputedStyle(document.querySelector('#acT')).opacity), pT: +s.st.pT.toFixed(3), pG: +s.st.pG.toFixed(3) });
    delete samples[samples.length - 1].st;
    if (ms === 3300) await shot('06-flights-mid');
    if (ms === 2000) await shot('06a-flights-early');
    if (ms === 5900) await shot('06b-flights-late');
  }
  R.samples = samples;
  await p.waitForTimeout(1300); await shot('07-arrival-emblem');
  await p.waitForTimeout(3600); await shot('08-invitation');
  R.sceneEnd = await p.evaluate(() => window.__treasure.state.current);
  R.inviteLoaded = await p.evaluate(() => { const i = document.querySelector('#inviteArt'); return { complete: i.complete, w: i.naturalWidth, h: i.naturalHeight, src: i.currentSrc.split('/').pop() }; });
  R.overflow3 = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  // details panel
  await p.locator('.invite-bar [data-open-details]').click();
  await p.waitForTimeout(500); await shot('09-details');
  R.details = await p.evaluate(() => ({ text: document.querySelector('#sheet').innerText, gcal: document.querySelector('#gcalLink').href, maps: document.querySelector('#mapsLink').href, cd: ['cdD', 'cdH', 'cdM'].map(i => document.querySelector('#' + i).textContent), music: document.querySelector('#musicBtn').innerText, musicDisabled: document.querySelector('#musicBtn').getAttribute('aria-disabled') }));
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 4000 }).catch(() => null), p.click('#icsBtn')]);
  R.ics = dl ? fs.readFileSync(await dl.path(), 'utf8') : 'no download';
  await p.keyboard.press('Escape');
  // replay flights from details
  await p.locator('.invite-bar [data-open-details]').click(); await p.waitForTimeout(300);
  await p.click('[data-replay-flight]'); await p.waitForTimeout(3500);
  R.replayFlightScene = await p.evaluate(() => ({ s: window.__treasure.state.current, pT: window.__treasure.state.flight.pT, opT: getComputedStyle(document.querySelector('#acT')).opacity, opG: getComputedStyle(document.querySelector('#acG')).opacity }));
  await shot('10-replay-flight');
  // skip
  await p.click('#skipBtn'); await p.waitForTimeout(600);
  R.skipScene = await p.evaluate(() => window.__treasure.state.current);
  // replay story
  await p.locator('.invite-bar [data-replay]').click(); await p.waitForTimeout(700);
  R.replayStory = await p.evaluate(() => ({ s: window.__treasure.state.current, chest: window.__treasure.state.chestState }));
  R.forbidden = await p.evaluate(() => (document.documentElement.textContent.match(/pellikoduku|lunch|morning|reception|haldi|sangeet|mehendi/i) || [null])[0]);
  R.errors = errors; R.failed = failed;
  fs.writeFileSync(`${out}/${tag}-report.json`, JSON.stringify(R, null, 1));
  console.log(JSON.stringify(R, null, 1).slice(0, 4000));
  await b.close();
})();
