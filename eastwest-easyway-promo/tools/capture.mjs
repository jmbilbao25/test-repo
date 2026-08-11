// capture.mjs — the three-piece asset capture from video-shotcraft's
// assets/scripts/capture-template.mjs, ported to the Playwright that is already
// installed here (ponytail rung 5: don't add puppeteer for the same job):
//   1. full-page 2x screenshots            → public/textures/live/<page>-full.png
//   2. per-element cutouts (+4x for heroes) → public/textures/live/<name>.png
//   3. layout.json of page-space bboxes     → src/ew/live-layout.json
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const OUT = path.join(root, 'public/textures/live');
const LAYOUT = path.join(root, 'src/ew/live-layout.json');
const BASE = 'file://' + path.join(root, 'site');
const VIEWPORT = { width: 1920, height: 1080 };
const SETTLE_MS = 700;

const PAGES = [
  {
    name: 'app',
    file: 'index.html',
    boxes: [{ key: 'hero', selector: '#hero' }, { key: 'cards', selector: '.card', all: true }],
    cutouts: [
      { name: 'hero-card', selector: '#hero', hires: 4 },
      { name: 'card', selector: '.card', all: true },
      { name: 'nav', selector: '.topbar' },
      { name: 'float-quick', selector: '.quick .q' },
    ],
    hideForEmptyPlate: '.card',
  },
  {
    name: 'transfers',
    file: 'transfers.html',
    boxes: [{ key: 'rows', selector: '.row', all: true }, { key: 'panel', selector: '#rowspanel' }],
    cutouts: [
      { name: 'float-sum', selector: '.sum .box' },
      { name: 'row', selector: '.row', all: true },
    ],
    hideForEmptyPlate: '.row',
  },
  {
    name: 'bills',
    file: 'bills.html',
    boxes: [{ key: 'billers', selector: '.biller', all: true }, { key: 'panel', selector: '#billpanel' }],
    cutouts: [{ name: 'biller', selector: '.biller', all: true }],
    hideForEmptyPlate: '.biller',
  },
  {
    name: 'cards',
    file: 'cards.html',
    boxes: [
      { key: 'plastic', selector: '#plastic' },
      { key: 'ctls', selector: '.ctl', all: true },
      { key: 'status', selector: '.plastic .meta > div:nth-child(3)' },
    ],
    // the toggles are re-drawn live in the shot (they have to flip), so only their boxes are
    // needed — no cutouts
    cutouts: [{ name: 'plastic', selector: '#plastic', hires: 4 }],
  },
];

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(path.dirname(LAYOUT), { recursive: true });

const browser = await chromium.launch();
const layout = { pageW: VIEWPORT.width };

for (const pg of PAGES) {
  for (const scale of [2, 4]) {
    // 4x pass only exists to re-shoot the hero elements at native resolution (Q2)
    const hires = pg.cutouts.filter((c) => c.hires === scale);
    if (scale === 4 && hires.length === 0) continue;

    const ctx = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: scale });
    const page = await ctx.newPage();
    await page.goto(`${BASE}/${pg.file}`, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(SETTLE_MS);

    if (scale === 4) {
      for (const c of hires) {
        await page.locator(c.selector).first().screenshot({ path: `${OUT}/${c.name}-hires.png` });
        console.log(`  captured ${c.name}-hires.png @4x`);
      }
      await ctx.close();
      continue;
    }

    const entry = { pageH: await page.evaluate(() => document.documentElement.scrollHeight) };
    layout[pg.name] = entry;

    await page.screenshot({ path: `${OUT}/${pg.name}-full.png`, fullPage: true });
    console.log(`captured ${pg.name}-full.png  pageH=${entry.pageH}`);

    const bbox = (loc) =>
      loc.evaluate((e) => {
        const r = e.getBoundingClientRect();
        return { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height };
      });

    entry.boxes = {};
    for (const b of pg.boxes ?? []) {
      const loc = page.locator(b.selector);
      const n = await loc.count();
      if (b.all) {
        const arr = [];
        for (let i = 0; i < n; i++) arr.push(await bbox(loc.nth(i)));
        entry.boxes[b.key] = arr;
      } else {
        entry.boxes[b.key] = n ? await bbox(loc.first()) : null;
      }
      console.log(`  boxes.${b.key}: ${b.all ? entry.boxes[b.key].length : 1}`);
    }

    entry.cutouts = [];
    for (const c of pg.cutouts ?? []) {
      const loc = page.locator(c.selector);
      const n = await loc.count();
      const take = c.all ? n : 1;
      for (let i = 0; i < take; i++) {
        const file = c.all ? `${c.name}${i + 1}.png` : `${c.name}.png`;
        const el = loc.nth(i);
        await el.screenshot({ path: `${OUT}/${file}` });
        entry.cutouts.push({ file, ...(await bbox(el)) });
      }
      console.log(`  cutouts ${c.name}: ${take}`);
    }

    if (pg.hideForEmptyPlate) {
      await page.evaluate((sel) => {
        document.querySelectorAll(sel).forEach((el) => { el.style.visibility = 'hidden'; });
      }, pg.hideForEmptyPlate);
      await page.waitForTimeout(150);
      await page.screenshot({ path: `${OUT}/${pg.name}-empty.png`, fullPage: true });
      console.log(`captured ${pg.name}-empty.png`);
    }

    await ctx.close();
  }
}

fs.writeFileSync(LAYOUT, JSON.stringify(layout, null, 1));
console.log('wrote', LAYOUT);
await browser.close();
