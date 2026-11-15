// Drive Chrome over the DevTools protocol: real-time playback, state checks, screenshots, console errors.
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
const [,, url, outDir, profile] = process.argv;
const chrome = spawn('google-chrome', ['--headless=new', '--no-first-run', '--no-default-browser-check', `--user-data-dir=${profile}`,
  '--remote-debugging-port=9333', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws, id = 0; const pending = new Map(); const errors = [];
for (let i = 0; i < 40; i++) { try { const t = await (await fetch('http://127.0.0.1:9333/json')).json(); const p = t.find(x => x.type === 'page'); if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); break; } } catch {} await sleep(250); }
await new Promise(r => ws.onopen = r);
ws.onmessage = e => { const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') errors.push('EXCEPTION ' + m.params.exceptionDetails.exception?.description);
  if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(m.params.type)) errors.push(m.params.type + ' ' + m.params.args.map(a => a.value ?? a.description).join(' '));
  if (m.method === 'Log.entryAdded' && ['error', 'warning'].includes(m.params.entry.level)) errors.push('log ' + m.params.entry.text + ' ' + (m.params.entry.url || '')); };
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result?.result?.value;
const shot = async (name, full = true) => { const m = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: full }); writeFileSync(`${outDir}/${name}.png`, Buffer.from(m.result.data, 'base64')); };
const state = `({ year: document.getElementById('yr').textContent, now: (document.querySelector('.chip.now b')||{}).textContent,
  unlocked: document.querySelectorAll('#stages .bd:not(.off)').length, locked: document.querySelectorAll('#stages .bd.off').length,
  titles: [...document.querySelectorAll('#stages .titles')].map(e => e.textContent).join(' || '),
  play: document.getElementById('play').textContent, live: document.getElementById('run').className, htmlClass: document.documentElement.className,
  insp: document.getElementById('insp').innerText.replace(/\\s+/g,' ').slice(0,90), overflowX: document.documentElement.scrollWidth > innerWidth })`;
await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1366, height: 900, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url }); await sleep(1500);
const out = { start: await ev(state) };
await sleep(7000); out.mid = await ev(state);
await sleep(9500); out.end = await ev(state);
await shot('desktop-light');
// every role boundary: the "now" chip must match the newest title listed in the stages
await ev(`(() => { const r = document.getElementById('range'); r.value = 0; r.dispatchEvent(new Event('input')); })()`); await sleep(150);
out.boundaries = [];
for (let i = 0; i < 11; i++) {
  out.boundaries.push(await ev(`(() => { const st = [...document.querySelectorAll('#stages .st')].filter(s => s.querySelector('.titles'));
    const last = st.length ? st[st.length - 1].querySelector('.titles').textContent.split(', ').pop() : '';
    return document.getElementById('yr').textContent + ' now=' + document.querySelector('.chip.now b').textContent + ' | newest listed=' + last; })()`));
  await ev(`document.getElementById('next').click()`); await sleep(120);
}
// every badge label must sit below its icon
out.labelsBesideIcon = await ev(`[...document.querySelectorAll('#stages .bd')].filter(b => { const svg = b.querySelector('svg').getBoundingClientRect();
  const t = [...b.childNodes].find(n => n.nodeType === 3 && n.textContent.trim()); if (!t) return false; const rg = document.createRange(); rg.selectNodeContents(t);
  return rg.getClientRects()[0].top < svg.bottom - 1; }).map(b => b.dataset.id)`);
await ev(`(() => { const r = document.getElementById('range'); r.value = 1000; r.dispatchEvent(new Event('input')); })()`); await sleep(150);
await ev(`document.getElementById('theme').click()`); await sleep(400);
out.themeAfterClick = await ev(`({ theme: document.documentElement.dataset.theme, pressed: document.getElementById('theme').getAttribute('aria-pressed'), bg: getComputedStyle(document.body).backgroundColor })`);
await shot('desktop-dark');
await ev(`document.querySelector('#stages .bd[data-id="k8s"]').dispatchEvent(new PointerEvent('pointerdown', {bubbles:true}))`); await sleep(200);
out.afterBadgeClick = await ev(`({ insp: document.getElementById('insp').innerText.replace(/\\s+/g,' ').slice(0,90), announce: document.getElementById('announce').textContent.slice(0,60) })`);
await ev(`document.getElementById('prev').click()`); await sleep(200); out.afterPrev = await ev(state);
await ev(`document.getElementById('play').click()`); await sleep(1500); out.afterPlay = await ev(state);
await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
await ev(`localStorage.removeItem('theme'); location.reload()`); await sleep(18000);
out.mobileEnd = await ev(state); await shot('mobile-light');
out.errors = errors;
console.log(JSON.stringify(out, null, 1));
ws.close(); chrome.kill();
