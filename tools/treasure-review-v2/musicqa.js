// Music QA: real taps on the Play Music button; verifies the actual MP3 plays, pauses, resumes,
// persists through all three scenes and Replay Story, and that no "Coming Soon" text remains.
const { chromium, devices } = require('playwright');
const [url, devName] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=user-gesture-required'] });
  const dev = devices[devName]; const ctx = await b.newContext({ ...dev }); const p = await ctx.newPage();
  const errs = [], failed = []; let mp3Status = null;
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('response', r => { if (r.url().includes('wedding-music.mp3')) mp3Status = r.status(); if (r.status() >= 400) failed.push(r.status() + ' ' + r.url()); });
  const tap = async sel => {
    let x, y;
    if (sel === 'PILL') {
      const pt = await p.evaluate(() => { for (const b of document.querySelectorAll('#musicBtn')) { const r = b.getBoundingClientRect(); const cx = r.left + r.width / 2, cy = r.top + r.height / 2; const hit = document.elementFromPoint(cx, cy); if (hit && b.contains(hit)) return [cx, cy]; } return null; });
      if (!pt) throw new Error('no tappable music button visible'); [x, y] = pt;
    } else { const bb = await p.locator(sel).first().boundingBox(); x = bb.x + bb.width / 2; y = bb.y + bb.height / 2; } dev.hasTouch ? await p.touchscreen.tap(x, y) : await p.mouse.click(x, y); };
  const A = () => p.evaluate(() => { const a = document.getElementById('bgm'); const vis = [...document.querySelectorAll('#musicBtn')].find(b => { const r = b.getBoundingClientRect(); const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return h && b.contains(h); }); return { paused: a.paused, t: +a.currentTime.toFixed(2), vol: a.volume, loop: a.loop, dur: +a.duration.toFixed(1), src: a.currentSrc.split('/').pop(), label: vis && vis.innerText.trim(), scene: window.__treasure.state.current, audios: document.querySelectorAll('audio').length }; });
  const R = {};
  await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
  R.beforeTap = await A();
  R.comingSoon = await p.evaluate(() => /coming soon/i.test(document.body.innerText));
  await tap('PILL'); await p.waitForTimeout(2500); R.afterPlay = await A();
  await tap('PILL'); await p.waitForTimeout(800); R.afterPause = await A();
  await p.waitForTimeout(1000); R.stillPaused = await A();
  await tap('PILL'); await p.waitForTimeout(1200); R.afterResume = await A();
  await tap('#beginBtn'); await p.waitForTimeout(2200); await tap('#chestBtn'); await p.waitForTimeout(6500); R.inJourney = await A();
  await tap('#followBtn'); await p.waitForTimeout(12000); R.inInvitation = await A();
  await tap('#cardBar [data-open-details]'); await p.waitForTimeout(800); R.withDetails = await A();
  await tap('#sheet [data-replay]'); await p.waitForTimeout(1000); R.afterReplay = await A();
  R.mp3Status = mp3Status; R.errors = errs; R.failed = failed;
  console.log(JSON.stringify(R));
  await b.close();
})();
