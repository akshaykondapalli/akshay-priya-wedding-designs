const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const T={'.html':'text/html','.css':'text/css','.js':'text/javascript','.webp':'image/webp','.woff2':'font/woff2'};
const srv=http.createServer((q,r)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p.endsWith('/'))p+='index.html';fs.readFile(path.join('/home/claude/site',p),(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'content-type':T[path.extname(p)]||'application/octet-stream'});r.end(d)})}).listen(8712);
(async()=>{const b=await chromium.launch();const p=await (await b.newContext({viewport:{width:1440,height:900}})).newPage();
await p.goto('http://localhost:8712/heritage/',{waitUntil:'networkidle'});await p.evaluate(()=>atlasReveal());
await p.evaluate(()=>document.querySelector('#destination').scrollIntoView());await p.waitForTimeout(1500);
console.log(await p.evaluate(()=>{const s=document.querySelector('.scene');const r=s.getBoundingClientRect();return [r.x,r.y,r.width,r.height, [...s.querySelectorAll('img')].map(i=>i.complete&&i.naturalWidth)]}));
await p.screenshot({path:'/home/claude/qa/heritage/desktop-destination.png'});await b.close();srv.close()})();
