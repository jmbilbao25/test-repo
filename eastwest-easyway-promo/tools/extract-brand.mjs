// extract-brand.mjs — read-only brand token extraction from the public EastWest site.
// Purpose: derive the design spec (palette / type / radius / density) that the promo must reuse.
// Nothing captured here ships in the video; the video renders our own locally-built UI.
import { chromium } from 'playwright';
import fs from 'fs';

const URLS = [
  'https://www.eastwestbanker.com/',
  'https://www.eastwestbanker.com/easyway-app',
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const out = {};

for (const url of URLS) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(2500);
    const data = await page.evaluate(() => {
      const norm = (c) => {
        const m = c && c.match(/rgba?\(([^)]+)\)/);
        if (!m) return null;
        const p = m[1].split(',').map((n) => parseFloat(n));
        if (p.length > 3 && p[3] === 0) return null;
        return '#' + p.slice(0, 3).map((n) => Math.round(n).toString(16).padStart(2, '0')).join('');
      };
      const tally = (obj, k) => { if (!k) return; obj[k] = (obj[k] || 0) + 1; };
      const bg = {}, fg = {}, fonts = {}, sizes = {}, radii = {}, weights = {};
      const els = [...document.querySelectorAll('body *')].slice(0, 4000);
      for (const el of els) {
        const r = el.getBoundingClientRect();
        if (r.width < 4 || r.height < 4) continue;
        const cs = getComputedStyle(el);
        tally(bg, norm(cs.backgroundColor));
        if (el.textContent && el.textContent.trim().length > 1) {
          tally(fg, norm(cs.color));
          tally(fonts, cs.fontFamily);
          tally(sizes, cs.fontSize);
          tally(weights, cs.fontWeight);
        }
        if (cs.borderRadius && cs.borderRadius !== '0px') tally(radii, cs.borderRadius);
        const bi = cs.backgroundImage;
        if (bi && bi.includes('gradient')) tally(bg, 'GRAD:' + bi.slice(0, 120));
      }
      const top = (o, n = 14) => Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, n);
      return {
        title: document.title,
        bg: top(bg), fg: top(fg), fonts: top(fonts, 6),
        sizes: top(sizes), radii: top(radii, 8), weights: top(weights, 8),
        headings: [...document.querySelectorAll('h1,h2,h3')].slice(0, 14).map((h) => h.textContent.trim().replace(/\s+/g, ' ').slice(0, 90)),
      };
    });
    out[url] = data;
    console.log('=== ' + url);
    console.log(JSON.stringify(data, null, 1));
  } catch (e) {
    console.log('FAIL ' + url + ' :: ' + e.message);
  }
}
fs.mkdirSync('brand', { recursive: true });
fs.writeFileSync('brand/tokens-raw.json', JSON.stringify(out, null, 1));
await browser.close();
