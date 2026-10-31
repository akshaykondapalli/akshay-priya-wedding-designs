// Visual regression: render pre-music and post-music builds in identical settled states and capture them.
const { chromium, devices } = require('playwright');
const out = '/home/claude/qa/rel-diff'; require('fs').mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch();
  for (const [tag, url] of [['pre', 'http://127.0.0.1:8765/_pre2/'], ['post', 'http://127.0.0.1:8765/treasure-review/']]) {
    const ctx = await b.newContext({ ...devices['iPhone 15'], reducedMotion: 'reduce' });
    const p = await ctx.newPage();
    await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(600);
    await p.screenshot({ path: `${out}/${tag}-1-cover.png` });
    await p.evaluate(() => window.__treasure.begin()); await p.waitForTimeout(1200);
    await p.screenshot({ path: `${out}/${tag}-2-chest.png` });
    await p.evaluate(() => window.__treasure.openChest()); await p.waitForTimeout(2500);
    await p.screenshot({ path: `${out}/${tag}-3-map.png` });
    await p.evaluate(() => window.__treasure.skip()); await p.waitForTimeout(1500);
    await p.screenshot({ path: `${out}/${tag}-4-invite.png` });
    await p.evaluate(() => document.querySelector('#cardBar [data-open-details]').click()); await p.waitForTimeout(900);
    await p.evaluate(() => { for (const id of ['cdD', 'cdH', 'cdM', 'cdS']) document.getElementById(id).textContent = '00'; });
    await p.screenshot({ path: `${out}/${tag}-5-details.png` });
    await ctx.close();
  }
  await b.close();
})();
