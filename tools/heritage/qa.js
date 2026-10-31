// QA for the Heritage design. Usage: node qa.js [mode]   mode: shots (default) | motion
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = '/home/claude/site', OUT = '/home/claude/qa/heritage', PORT = 8711;
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.webp': 'image/webp', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg' };
const srv = http.createServer((q, r) => {
  let p = decodeURIComponent(q.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end('nf'); return; } r.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
}).listen(PORT);
const URL = `http://localhost:${PORT}/heritage/index.html`;
const chapters = ['arrival', 'souls', 'connection', 'destination', 'invitation', 'details', 'blessing'];

(async () => {
  const mode = process.argv[2] || 'shots';
  const b = await chromium.launch();
  const report = { errors: [], failed: [], checks: {} };
  const watch = (page, tag) => {
    page.on('console', m => { if (m.type() === 'error') report.errors.push(`${tag}: ${m.text()}`); });
    page.on('pageerror', e => report.errors.push(`${tag}: ${e.message}`));
    page.on('requestfailed', r => report.failed.push(`${tag}: ${r.url()}`));
    page.on('response', r => { if (r.status() >= 400) report.failed.push(`${tag}: ${r.status()} ${r.url()}`); });
  };
  if (mode === 'shots') {
    // revealed chapter shots at iPhone size
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const page = await ctx.newPage(); watch(page, 'iphone');
    await page.goto(URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
    await page.screenshot({ path: `${OUT}/m-00-arrival-closed.png` });
    await page.click('#openAtlas'); await page.waitForTimeout(2600);
    await page.screenshot({ path: `${OUT}/m-01-arrival-open.png` });
    await page.evaluate(() => window.atlasReveal());
    for (const [i, c] of chapters.entries()) {
      await page.evaluate(c => document.querySelector(`[data-chapter="${c}"]`).scrollIntoView(), c);
      await page.waitForTimeout(700);
      await page.screenshot({ path: `${OUT}/m-${String(i + 1).padStart(2, '0')}-${c}.png` });
    }
    // overflow check at 360
    await page.setViewportSize({ width: 360, height: 780 });
    report.checks.overflow360 = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    report.checks.chapters = await page.evaluate(() => [...document.querySelectorAll('[data-chapter]')].map(e => e.dataset.chapter).join(','));
    report.checks.backHref = await page.getAttribute('.bar__back', 'href');
    await ctx.close();
    for (const [w, h, tag] of [[412, 915, 'android'], [820, 1180, 'tablet'], [1440, 900, 'desktop']]) {
      const c2 = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
      const p2 = await c2.newPage(); watch(p2, tag);
      await p2.goto(URL, { waitUntil: 'networkidle' }); await p2.waitForTimeout(500);
      await p2.screenshot({ path: `${OUT}/${tag}-first.png` });
      report.checks['overflow_' + tag] = await p2.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (tag === 'desktop') {
        await p2.evaluate(() => window.atlasReveal());
        for (const c of ['destination', 'invitation']) {
          await p2.evaluate(c => document.querySelector(`[data-chapter="${c}"]`).scrollIntoView(), c);
          await p2.waitForTimeout(500);
          await p2.screenshot({ path: `${OUT}/desktop-${c}.png` });
        }
      }
      await c2.close();
    }
  }
  if (mode === 'motion') {
    // scroll-scrub frames through the sticky chapters, as a guest would see them
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const page = await ctx.newPage(); watch(page, 'motion');
    await page.goto(URL, { waitUntil: 'networkidle' });
    await page.click('#openAtlas'); await page.waitForTimeout(2200);
    for (const [c, fracs] of [['souls', [.15, .5, .85]], ['connection', [.2, .5, .9]], ['destination', [.05, .5]]]) {
      for (const f of fracs) {
        await page.evaluate(([c, f]) => { const el = document.querySelector(`[data-chapter="${c}"]`); const top = el.getBoundingClientRect().top + scrollY; window.scrollTo(0, top + (el.offsetHeight - innerHeight) * f); }, [c, f]);
        await page.waitForTimeout(900);
        await page.screenshot({ path: `${OUT}/motion-${c}-${Math.round(f * 100)}.png` });
      }
    }
    // reduced motion run
    const c3 = await b.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    const p3 = await c3.newPage(); watch(p3, 'reduced');
    await p3.goto(URL, { waitUntil: 'networkidle' });
    report.checks.reducedMotionClass = await p3.evaluate(() => document.documentElement.classList.contains('motion'));
    await p3.evaluate(() => document.querySelector('#souls').scrollIntoView()); await p3.waitForTimeout(300);
    await p3.screenshot({ path: `${OUT}/reduced-souls.png` });
    // menu + skip
    await p3.evaluate(() => scrollTo(0, 0));
    await p3.click('.bar__menu'); report.checks.menuOpens = await p3.isVisible('#menu');
    await p3.keyboard.press('Escape'); report.checks.menuClosesOnEsc = !(await p3.isVisible('#menu'));
    // JS disabled
    const c4 = await b.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
    const p4 = await c4.newPage();
    await p4.goto(URL, { waitUntil: 'networkidle' });
    await p4.evaluate(() => 0).catch(() => {});
    await p4.screenshot({ path: `${OUT}/nojs-full.png`, fullPage: true });
  }
  console.log(JSON.stringify(report, null, 2));
  await b.close(); srv.close();
})();
