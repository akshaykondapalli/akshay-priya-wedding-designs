// Captures one 390x844 phone screenshot per chapter per design for the comparison page,
// plus a QA sweep (console errors, failed requests, overflow, forbidden words).
// Usage: node capture-previews.js <baseURL> <outDir> [designs...]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const base = process.argv[2] || 'http://127.0.0.1:8765/';
const out = process.argv[3] || '/home/claude/site/previews';
const designs = process.argv.slice(4);
const CH = (process.env.CHAPTERS || 'arrival,souls,connection,destination,invitation,details,blessing').split(',');
const FORBIDDEN = /pellikoduku|lunch|morning|reception|haldi|sangeet|mehendi/i;
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const report = {};
  for (const d of designs) {
    const r = report[d] = { errors: [], failed: [], missingChapters: [], overflow360: null, forbidden: null, facts: {} };
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error') r.errors.push(m.text()); });
    page.on('pageerror', e => r.errors.push('pageerror: ' + e.message));
    page.on('requestfailed', q => r.failed.push(q.url() + ' ' + (q.failure() || {}).errorText));
    page.on('response', s => { if (s.status() >= 400) r.failed.push(s.status() + ' ' + s.url()); });
    await page.goto(base + d + '/index.html', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1800);
    await page.screenshot({ path: path.join(out, `${d}-arrival.png`) });
    const txt = await page.evaluate(() => document.body.innerText);
    const m = txt.match(FORBIDDEN); r.forbidden = m ? m[0] : null;
    for (const f of ['Akshay', 'Priya', '21 November 2026', '8:00 PM', '9:55 PM', 'Priyanka Convention', 'Nallajerla']) r.facts[f] = txt.replace(/\s+/g,' ').toLowerCase().includes(f.replace(':00 PM',':00').replace(':55 PM',':55').toLowerCase());
    r.facts.Saturday = /saturday/i.test(txt);
    await page.evaluate(() => window.atlasReveal && window.atlasReveal());
    await page.waitForTimeout(900);
    for (const c of CH.slice(1)) {
      const ok = await page.evaluate(c => {
        const el = document.querySelector(`[data-chapter="${c}"]`); if (!el) return false;
        if (window.atlasGo) { window.atlasGo(c); return true; }
        const top = el.getBoundingClientRect().top + scrollY;
        // for tall pinned sections, capture near the end of the section
        const h = el.offsetHeight, vh = innerHeight;
        const y = h > vh * 1.6 ? top + h - vh : top;
        window.scrollTo({ top: y, behavior: 'instant' }); return true;
      }, c);
      if (!ok) { r.missingChapters.push(c); continue; }
      await page.waitForTimeout(1600);
      await page.screenshot({ path: path.join(out, `${d}-${c}.png`) });
    }
    await ctx.close();
    const c2 = await browser.newContext({ viewport: { width: 360, height: 740 } });
    const p2 = await c2.newPage();
    await p2.goto(base + d + '/index.html', { waitUntil: 'networkidle' });
    await p2.evaluate(() => window.atlasReveal && window.atlasReveal());
    r.overflow360 = await p2.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    await c2.close();
  }
  await browser.close();
  fs.writeFileSync((process.env.REPORT || '/home/claude/qa/capture-report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
})();
