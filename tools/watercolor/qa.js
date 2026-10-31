const { chromium } = require('playwright');
const OUT = '/home/claude/qa/watercolor/';
const URL = 'http://localhost:8732/watercolor/index.html';
const chapters = ['arrival','souls','connection','destination','invitation','details','blessing'];
(async () => {
  const browser = await chromium.launch();
  const mode = process.argv[2] || 'all';
  const errors = [];
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('requestfailed', r => errors.push('failed: ' + r.url()));
  page.on('response', r => { if (r.status() >= 400) errors.push(r.status() + ' ' + r.url()); });
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3500);
  await page.screenshot({ path: OUT + 'm-01-arrival-live.png' });
  // live scroll through journey to capture mid-animation states
  for (const [frac, name] of [[0.25,'souls-mid'],[0.62,'connection-bloom']]) {
    await page.evaluate(f => { const j = document.getElementById('journey'); const top = j.getBoundingClientRect().top + scrollY; window.scrollTo(0, top + (j.offsetHeight - innerHeight) * f); }, frac);
    await page.waitForTimeout(3000);
    await page.screenshot({ path: OUT + `m-live-${name}.png` });
  }
  await page.evaluate(() => { const d = document.getElementById('destination'); window.scrollTo(0, d.getBoundingClientRect().top + scrollY - 40); });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: OUT + 'm-live-destination-spreading.png' });
  await page.waitForTimeout(3000);
  // revealed captures per chapter
  await page.evaluate(() => window.atlasReveal());
  for (let i = 0; i < chapters.length; i++) {
    const c = chapters[i];
    await page.evaluate(c => document.querySelector(`[data-chapter="${c}"]`).scrollIntoView({ block: 'start' }), c);
    await page.waitForTimeout(500);
    await page.screenshot({ path: OUT + `m-0${i + 1}-${c}.png` });
  }
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  console.log('overflow390', overflow);
  await ctx.close();
  for (const [w, h, n] of [[412, 915, 'android'], [820, 1180, 'tablet'], [1440, 900, 'desktop'], [360, 740, 'small']]) {
    const c2 = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: n === 'desktop' ? 1 : 2 });
    const p2 = await c2.newPage();
    p2.on('pageerror', e => errors.push(n + ' pageerror: ' + e.message));
    await p2.goto(URL, { waitUntil: 'networkidle' });
    await p2.waitForTimeout(3500);
    await p2.screenshot({ path: OUT + `first-${n}.png` });
    if (n === 'desktop') {
      await p2.evaluate(() => { const j = document.getElementById('journey'); window.scrollTo(0, j.getBoundingClientRect().top + scrollY + (j.offsetHeight - innerHeight) * 0.7); });
      await p2.waitForTimeout(3000);
      await p2.screenshot({ path: OUT + `desktop-journey.png` });
      await p2.evaluate(() => { window.atlasReveal(); document.getElementById('invitation').scrollIntoView(); });
      await p2.waitForTimeout(500);
      await p2.screenshot({ path: OUT + `desktop-invitation.png` });
    }
    console.log('overflow', n, await p2.evaluate(() => document.documentElement.scrollWidth > innerWidth));
    await c2.close();
  }
  // reduced motion
  const c3 = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  const p3 = await c3.newPage();
  p3.on('pageerror', e => errors.push('rm pageerror: ' + e.message));
  await p3.goto(URL, { waitUntil: 'networkidle' });
  await p3.evaluate(() => document.getElementById('souls').scrollIntoView());
  await p3.waitForTimeout(600);
  await p3.screenshot({ path: OUT + 'rm-souls.png' });
  console.log('rm journey height', await p3.evaluate(() => document.getElementById('journey').offsetHeight));
  // no-js
  const c4 = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
  const p4 = await c4.newPage();
  await p4.goto(URL, { waitUntil: 'networkidle' });
  await p4.screenshot({ path: OUT + 'nojs-full.png', fullPage: true });
  console.log('ERRORS', JSON.stringify(errors, null, 1));
  await browser.close();
})();
