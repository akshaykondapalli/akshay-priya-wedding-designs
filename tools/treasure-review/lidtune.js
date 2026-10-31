const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ ...devices['iPhone 15'] });
  await p.goto('http://127.0.0.1:8765/treasure-review/', { waitUntil: 'networkidle' });
  const configs = JSON.parse(process.argv[2]);
  let i = 0;
  for (const c of configs) {
    for (const ang of c.angles) {
      await p.evaluate(({ c, ang }) => {
        const cs = document.querySelector('.chest-scene'); cs.style.perspective = c.persp + 'px'; cs.style.perspectiveOrigin = c.po;
        const l = document.querySelector('#lid'); l.style.transition = 'none'; l.style.transformOrigin = c.to; l.style.transform = `rotateX(${ang}deg)`;
        document.querySelector('.chest-glow').style.opacity = ang > 0 ? 1 : 0; document.querySelector('.beams').style.opacity = ang > 0 ? .9 : 0; document.querySelector('.beams').style.transform = 'scaleY(1)';
      }, { c, ang });
      await p.waitForTimeout(80);
      const r = await p.locator('.stage').first().boundingBox();
      const s = r.width / 941;
      await p.screenshot({ path: `/tmp/claude-0/-home-claude/2cf5e8b2-6ab2-523a-8d34-c01756c66623/scratchpad/lid-${i++}.png`, clip: { x: r.x + 180 * s, y: r.y + 880 * s, width: 620 * s, height: 480 * s } });
    }
  }
  await b.close();
})();
