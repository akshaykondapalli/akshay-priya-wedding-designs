// node shots.js <tag> <w> <h> <dpr> [reduce]
const { chromium } = require('playwright');
(async () => {
  const [tag, W, H, DPR, rm] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const ctx = await b.newContext({ viewport: { width: +W, height: +H }, deviceScaleFactor: +DPR, reducedMotion: rm ? 'reduce' : 'no-preference', isMobile: +W < 800, hasTouch: +W < 800 });
  const p = await ctx.newPage();
  const errs = [];
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
  p.on('requestfailed', r => errs.push('REQFAIL ' + r.url()));
  p.on('response', r => { if (r.status() >= 400) errs.push('HTTP ' + r.status() + ' ' + r.url()); });
  await p.goto('http://localhost:8704/fusion/index.html', { waitUntil: 'networkidle' });
  await p.waitForTimeout(600);
  const out = `/home/claude/qa/fusion/${tag}`;
  const pos = JSON.parse(process.env.POS || '[]');
  for (const [name, sel, frac] of pos) {
    await p.evaluate(([sel, frac]) => {
      const el = document.querySelector(sel);
      const top = el.offsetTop + (el.offsetHeight - innerHeight) * frac;
      window.scrollTo(0, Math.max(0, top));
    }, [sel, frac]);
    await p.waitForTimeout(700);
    await p.screenshot({ path: `${out}-${name}.png` });
  }
  const ov = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  console.log(JSON.stringify({ errs, overflowX: ov, hasGL: await p.evaluate(() => document.documentElement.classList.contains('has-gl')) }));
  await b.close();
})();
