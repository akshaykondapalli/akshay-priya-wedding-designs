const { chromium } = require('playwright');
const BASE = 'http://localhost:8704/fusion/index.html';
const chapters = ['arrival', 'souls', 'connection', 'destination', 'invitation', 'details', 'blessing'];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const report = {};
  async function open(w, h, dpr, opts = {}) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dpr, isMobile: w < 800, hasTouch: w < 800, reducedMotion: opts.rm ? 'reduce' : 'no-preference', javaScriptEnabled: !opts.nojs });
    const p = await ctx.newPage();
    const errs = [];
    p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
    p.on('requestfailed', r => errs.push('REQFAIL ' + r.url()));
    p.on('response', r => { if (r.status() >= 400) errs.push('HTTP ' + r.status() + ' ' + r.url()); });
    await p.goto(BASE, { waitUntil: 'networkidle' });
    await p.waitForTimeout(500);
    return { p, ctx, errs };
  }
  // 1) phone chapters via atlasReveal (390x844 @2)
  {
    const { p, ctx, errs } = await open(390, 844, 2);
    await p.screenshot({ path: '/home/claude/qa/fusion/390-first-screen.png' });
    // menu
    await p.evaluate(() => scrollTo(0, 0)); await p.waitForTimeout(300);
    await p.click('[data-menu-btn]'); await p.waitForTimeout(200);
    const menuOpen = await p.evaluate(() => !document.querySelector('[data-menu]').hidden);
    await p.screenshot({ path: '/home/claude/qa/fusion/390-menu.png' });
    await p.keyboard.press('Escape');
    const menuClosed = await p.evaluate(() => document.querySelector('[data-menu]').hidden);
    // skip link jumps to invitation
    await p.click('.arrival__hint a'); await p.waitForTimeout(1600);
    const atInvite = await p.evaluate(() => Math.abs(document.getElementById('invitation').getBoundingClientRect().top) < 5);
    const links = await p.evaluate(() => ({
      back: document.querySelector('.bar__back').getAttribute('href'),
      maps: [...document.querySelectorAll('a')].find(a => a.href.includes('google.com/maps'))?.href,
      cal: [...document.querySelectorAll('a')].find(a => a.href.includes('calendar.google.com'))?.href,
      chapters: [...document.querySelectorAll('[data-chapter]')].map(e => e.dataset.chapter),
      reveal: typeof window.atlasReveal
    }));
    // ics + share
    const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 4000 }).catch(() => null), p.click('[data-ics]')]);
    let icsText = null; if (dl) { const fs = require('fs'); const path = await dl.path(); icsText = fs.readFileSync(path, 'utf8'); }
    await ctx.grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => {});
    await p.evaluate(() => { try { delete navigator.share; } catch (e) {} });
    await p.click('[data-share]'); await p.waitForTimeout(400);
    const shareStatus = await p.textContent('[data-status]');
    await p.goto(BASE, { waitUntil: 'networkidle' }); await p.waitForTimeout(400);
    await p.evaluate(() => window.atlasReveal());
    for (const c of chapters) {
      await p.evaluate(c => { const el = document.querySelector(`[data-chapter="${c}"]`); const top = el.getBoundingClientRect().top + scrollY + (c === 'destination' ? el.offsetHeight - innerHeight : 0); scrollTo(0, top); }, c);
      await p.waitForTimeout(900);
      await p.screenshot({ path: `/home/claude/qa/fusion/390-${c}.png` });
    }
    report.phone = { errs, menuOpen, menuClosed, atInvite, links, icsOK: !!icsText && icsText.includes('DTSTART:20261121T143000Z'), shareStatus };
    await ctx.close();
  }
  // 2) first screens at other sizes + overflow
  for (const [w, h, d, tag] of [[412, 915, 2.6, '412'], [820, 1180, 2, '820'], [1440, 900, 1, '1440'], [360, 740, 2, '360']]) {
    const { p, ctx, errs } = await open(w, h, d);
    await p.screenshot({ path: `/home/claude/qa/fusion/${tag}-first-screen.png` });
    const ov = [];
    await p.evaluate(() => window.atlasReveal());
    for (const c of chapters) {
      await p.evaluate(c => { const el = document.querySelector(`[data-chapter="${c}"]`); scrollTo(0, el.getBoundingClientRect().top + scrollY + (c === 'destination' ? el.offsetHeight - innerHeight : 0)); }, c);
      await p.waitForTimeout(500);
      ov.push(await p.evaluate(() => document.documentElement.scrollWidth - innerWidth));
      if (tag === '1440' || tag === '820') await p.screenshot({ path: `/home/claude/qa/fusion/${tag}-${c}.png` });
    }
    report[tag] = { errs, overflow: Math.max(...ov) };
    await ctx.close();
  }
  // 3) reduced motion + no-JS
  {
    const { p, ctx, errs } = await open(390, 844, 2, { rm: true });
    const h = await p.evaluate(() => document.documentElement.scrollHeight);
    for (const c of ['souls', 'destination']) {
      await p.evaluate(c => document.querySelector(`[data-chapter="${c}"]`).scrollIntoView(), c); await p.waitForTimeout(1600);
      await p.screenshot({ path: `/home/claude/qa/fusion/390-rm-${c}.png` });
    }
    report.reduced = { errs, scrollHeight: h, rm: await p.evaluate(() => document.documentElement.classList.contains('rm')) };
    await ctx.close();
  }
  {
    const { p, ctx, errs } = await open(390, 844, 2, { nojs: true });
    await p.screenshot({ path: '/home/claude/qa/fusion/390-nojs-full.png', fullPage: true });
    report.nojs = { errs, text: (await p.textContent('#invitation')).replace(/\s+/g, ' ').trim() };
    await ctx.close();
  }
  console.log(JSON.stringify(report, null, 1));
  await b.close();
})();
