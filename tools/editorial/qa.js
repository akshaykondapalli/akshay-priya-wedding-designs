// QA: screenshots per chapter + viewport set, console errors, overflow, reduced-motion, actions
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = '/home/claude/site', OUT = '/home/claude/qa/editorial', PORT = 8733;
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.webp': 'image/webp', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg' };
const srv = http.createServer((q, s) => {
  let p = decodeURIComponent(q.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  fs.readFile(f, (e, b) => { if (e) { s.writeHead(404); s.end('nf'); return; } s.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); s.end(b); });
}).listen(PORT);
const only = process.argv[2] || 'all';
(async () => {
  const b = await chromium.launch();
  const report = [];
  const url = `http://localhost:${PORT}/editorial/index.html`;
  async function page(vp, opts = {}) {
    const ctx = await b.newContext({ viewport: vp, deviceScaleFactor: opts.dpr || 1, reducedMotion: opts.rm ? 'reduce' : 'no-preference', hasTouch: !!opts.touch, isMobile: !!opts.touch });
    const p = await ctx.newPage(); const errs = [];
    p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    p.on('pageerror', e => errs.push('pageerror ' + e.message));
    p.on('requestfailed', r => errs.push('failed ' + r.url()));
    p.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('/index.html') ) errs.push(r.status() + ' ' + r.url()); });
    await p.goto(url, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    return { p, ctx, errs };
  }
  if (only === 'all' || only === 'mobile') {
    const { p, ctx, errs } = await page({ width: 390, height: 844 }, { dpr: 2, touch: true });
    await p.waitForTimeout(2600);
    await p.screenshot({ path: `${OUT}/m-00-first-screen.png` });
    await p.evaluate(() => window.atlasReveal());
    const chs = ['arrival', 'souls', 'connection', 'destination', 'invitation', 'details', 'blessing'];
    let i = 1;
    for (const c of chs) {
      await p.evaluate(c => { const el = document.querySelector(`[data-chapter="${c}"]`); window.scrollTo(0, el.getBoundingClientRect().top + scrollY); }, c);
      await p.waitForTimeout(500);
      await p.screenshot({ path: `${OUT}/m-${String(i).padStart(2, '0')}-${c}.png` });
      // extra frames for tall chapters
      const h = await p.evaluate(c => document.querySelector(`[data-chapter="${c}"]`).offsetHeight, c);
      for (let k = 1; k * 844 < h - 200 && k < 4; k++) {
        await p.evaluate(() => window.scrollBy(0, 760)); await p.waitForTimeout(300);
        await p.screenshot({ path: `${OUT}/m-${String(i).padStart(2, '0')}-${c}-${k}.png` });
      }
      i++;
    }
    await p.screenshot({ path: `${OUT}/m-full.png`, fullPage: true });
    report.push(['mobile 390 errors', errs]);
    await ctx.close();
  }
  if (only === 'all' || only === 'views') {
    for (const [n, vp] of [['android-412', { width: 412, height: 915 }], ['tablet-820', { width: 820, height: 1180 }], ['desktop-1440', { width: 1440, height: 900 }]]) {
      const { p, ctx, errs } = await page(vp, { touch: n !== 'desktop-1440' });
      await p.waitForTimeout(2600);
      await p.screenshot({ path: `${OUT}/v-${n}.png` });
      if (n === 'desktop-1440') { await p.evaluate(() => window.atlasReveal()); await p.screenshot({ path: `${OUT}/v-desktop-full.png`, fullPage: true }); }
      report.push([n + ' errors', errs]);
      await ctx.close();
    }
  }
  if (only === 'all' || only === 'checks') {
    // overflow at 360
    { const { p, ctx, errs } = await page({ width: 360, height: 740 }, { touch: true });
      const o = await p.evaluate(() => { window.atlasReveal(); const w = document.documentElement.clientWidth; const bad = []; document.querySelectorAll('body *').forEach(e => { const r = e.getBoundingClientRect(); if (r.right > w + 1 && getComputedStyle(e).position !== 'fixed' && !e.closest('.pf-track')) bad.push(e.tagName + '.' + e.className); }); return { sw: document.documentElement.scrollWidth, w, bad: bad.slice(0, 8) }; });
      report.push(['overflow@360', o, errs]); await ctx.close(); }
    // reduced motion
    { const { p, ctx, errs } = await page({ width: 390, height: 844 }, { rm: true, touch: true });
      const r = await p.evaluate(() => ({ io: document.documentElement.classList.contains('io'), p: getComputedStyle(document.querySelector('.amp-l')).transform }));
      await p.screenshot({ path: `${OUT}/rm-first.png` });
      await p.evaluate(() => document.getElementById('connection').scrollIntoView()); await p.waitForTimeout(200);
      await p.screenshot({ path: `${OUT}/rm-connection.png` });
      report.push(['reduced-motion', r, errs]); await ctx.close(); }
    // actions
    { const { p, ctx, errs } = await page({ width: 390, height: 844 }, { touch: true });
      await p.evaluate(() => { navigator.share = undefined; });
      const res = {};
      res.back = await p.getAttribute('.bar-back', 'href');
      res.skip = await p.getAttribute('.cover-cta a[href="#invitation"]', 'href');
      await p.click('#menuBtn'); res.menuOpen = await p.isVisible('#menu');
      await p.keyboard.press('Escape'); res.menuClosedByEsc = await p.isHidden('#menu');
      res.maps = await p.getAttribute('a[href*="google.com/maps"]', 'href');
      res.gcal = await p.getAttribute('#gcal', 'href');
      await ctx.grantPermissions(['clipboard-read', 'clipboard-write']);
      await p.click('#shareBtn'); await p.waitForTimeout(300); res.share = await p.textContent('#shareStatus');
      const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 4000 }).catch(() => null), p.click('#icsBtn')]);
      if (dl) { const fp = await dl.path(); res.ics = fs.readFileSync(fp, 'utf8').split('\r\n').filter(l => /DTSTART|DTEND|SUMMARY/.test(l)); }
      await p.click('#pfNext'); await p.waitForTimeout(800); res.carousel = await p.textContent('#pfNow');
      res.chapters = await p.$$eval('[data-chapter]', els => els.map(e => e.dataset.chapter));
      res.text = await p.evaluate(() => document.body.innerText.match(/(Saturday, ?\s*21 November 2026|8:00|9:55|Priyanka Convention|Nallajerla)/g));
      report.push(['actions', res, errs]); await ctx.close(); }
  }
  console.log(JSON.stringify(report, null, 1));
  await b.close(); srv.close();
})();
