// usage: node render.js in.svg out.png W H [transparent]
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [inp, out, W, H, tr] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +W, height: +H }, deviceScaleFactor: 1 });
  const svg = fs.readFileSync(inp, 'utf8');
  await p.setContent(`<html><body style="margin:0;background:${tr ? 'transparent' : '#000'}">${svg}</body></html>`);
  await p.waitForTimeout(200);
  await p.screenshot({ path: out, omitBackground: !!tr, clip: { x: 0, y: 0, width: +W, height: +H } });
  await b.close();
})();
