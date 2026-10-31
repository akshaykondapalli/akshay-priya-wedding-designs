// Checks the floating music button on every scene at many viewports: on-screen, inside safe area,
// tappable (topmost), and not overlapping story controls or wedding text blocks. Usage: node fabcheck.js <url> <outdir>
const { chromium } = require('playwright');
const fs = require('fs');
const [url, out] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
const VP = [[375, 667], [390, 844], [393, 852], [430, 932], [360, 780], [412, 915], [320, 640], [768, 1024]];
(async () => {
  const b = await chromium.launch(); const rows = [];
  for (const [w, h] of VP) for (const orient of ['p', 'l']) {
    const W = orient === 'p' ? w : h, H = orient === 'p' ? h : w;
    const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 2, isMobile: W < 700 || H < 700, hasTouch: true, reducedMotion: process.env.RM || 'no-preference' });
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(400);
    const check = async (state) => {
      await p.waitForTimeout(450);
      const r = await p.evaluate(() => {
        const f = document.getElementById('musicBtn') || document.querySelector('.music-fab');
        const fr = f.getBoundingClientRect(); const cx = fr.left + fr.width / 2, cy = fr.top + fr.height / 2;
        const top = document.elementFromPoint(cx, cy); const tappable = !!top && f.contains(top);
        const sel = ['#beginBtn', '#followBtn', '#cardBar', '#sheet', '#calPop', '.scene.is-active .story-btn'];
        const hits = [];
        for (const s of sel) for (const el of document.querySelectorAll(s)) { const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < .05 || el.closest('.scene:not(.is-active)')) continue; const o = el.getBoundingClientRect(); if (fr.left < o.right && fr.right > o.left && fr.top < o.bottom && fr.bottom > o.top) hits.push(s); }
        return { fab: [Math.round(fr.left), Math.round(fr.top), Math.round(fr.width), Math.round(fr.height)], onscreen: fr.left >= 0 && fr.top >= 0 && fr.right <= innerWidth && fr.bottom <= innerHeight, tappable, hits: [...new Set(hits)], compact: f.classList.contains('compact'), ovf: document.documentElement.scrollWidth - innerWidth };
      });
      rows.push({ vp: `${W}x${H}`, state, ...r });
      await p.screenshot({ path: `${out}/${W}x${H}-${state}.jpg`, type: 'jpeg', quality: 70 });
    };
    await check('cover');
    await p.evaluate(() => window.__treasure.begin()); await p.waitForTimeout(2000); await check('chest');
    await p.evaluate(() => window.__treasure.openChest()); await p.waitForTimeout(6000); await check('map');
    await p.evaluate(() => document.getElementById('followBtn').click()); await p.waitForTimeout(12500); await check('invite');
    await p.evaluate(() => document.querySelector('#cardBar [data-open-details]').click()); await p.waitForTimeout(300); await check('details');
    await p.evaluate(() => document.querySelector('#sheet [data-calendar]').click()); await check('calendar');
    if (errs.length) rows.push({ vp: `${W}x${H}`, state: 'ERR', errs });
    await ctx.close();
  }
  await b.close();
  fs.writeFileSync(out + '/fab.json', JSON.stringify(rows, null, 1));
  const bad = rows.filter(r => r.state === 'ERR' || !r.onscreen || !r.tappable || r.hits.length || r.ovf > 0);
  console.log('checked', rows.length, 'states; problems:', bad.length); bad.forEach(r => console.log(JSON.stringify(r)));
})();
