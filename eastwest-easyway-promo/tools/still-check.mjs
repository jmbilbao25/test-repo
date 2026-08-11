// Prove the declared holds are actually STILL in the delivered pixels, not just in the cue
// arithmetic (the arithmetic check happily certified two holds the film did not have — found
// by the independent review). Decodes each hold window at 160x90 greyscale and reports the
// worst per-frame mean absolute difference inside it.
// Run: npm run check:still
import { execFileSync } from 'child_process';
import ffmpeg from 'ffmpeg-static';
import { readFileSync } from 'fs';

const MP4 = process.argv[2] ?? 'out/eastwest-easyway-promo.mp4';
const W = 160, H = 90, FPS = 30;

// The windows are DERIVED from the same beat grid and shot table the film is built from, and
// each carries the budget the design spec promises. If a hold shrinks — e.g. because a
// transition starts eating the frame earlier — this fails instead of quietly testing less.
const src = readFileSync(new URL('../src/ew/beats.ts', import.meta.url), 'utf8');
const BEAT0 = Number(/export const BEAT0 = ([\d.]+)/.exec(src)[1]);
const BEAT_INT = Number(/export const BEAT_INT = ([\d.]+)/.exec(src)[1]);
const beatF = (n) => Math.round((BEAT0 + n * BEAT_INT) * FPS);
const SHOT = Object.fromEntries(
  [...src.matchAll(/(\w+): shot\((\d+), (\d+)\)/g)].map(([, n, a, b]) => [n, { from: beatF(+a), to: beatF(+b) }]),
);
const LOCK_BEATS = JSON.parse(
  '[' + /export const LOCK_BEATS = \[([^\]]+)\]/.exec(
    readFileSync(new URL('../src/ew/scenes/SceneRewards.tsx', import.meta.url), 'utf8'),
  )[1] + ']',
);
const ODO_LOCK = beatF(LOCK_BEATS[LOCK_BEATS.length - 1]) + 8; // + the deepening pulse
const STAMP = beatF(93);

const HOLDS = [
  // the kicker finishes typing at f46 (28 + 25 chars x 0.7f) and the dissolve starts at f76
  { name: 'shot 1 · wordmark lockup hold', from: 46, to: 75, budget: 30, limit: 0.6 },
  { name: 'shot 3 · full-board rest', from: SHOT.deck.from + 104, to: SHOT.deck.from + 121, budget: 15, limit: 0.6 },
  // stillness runs from the odometer's final lock pulse until the wipe's first step lands
  { name: 'shot 8 · after the odometer locks', from: ODO_LOCK, to: SHOT.wipe.from + 1, budget: 45, limit: 0.6 },
  { name: 'shot 10 · sign-off hold', from: STAMP + 88, to: SHOT.outro.to - 21, budget: 30, limit: 1.2 },
];

let fails = 0;
for (const h of HOLDS) {
  const raw = execFileSync(ffmpeg, [
    '-hide_banner', '-loglevel', 'error', '-i', MP4,
    '-vf', `select=between(n\\,${h.from}\\,${h.to}),scale=${W}:${H},format=gray`,
    '-vsync', '0', '-f', 'rawvideo', '-',
  ], { maxBuffer: 1 << 28 });
  const size = W * H;
  const n = Math.floor(raw.length / size);
  let worst = 0, worstAt = -1;
  for (let f = 1; f < n; f++) {
    let sum = 0;
    for (let i = 0; i < size; i++) sum += Math.abs(raw[f * size + i] - raw[(f - 1) * size + i]);
    const mad = sum / size;
    if (mad > worst) { worst = mad; worstAt = h.from + f; }
  }
  const long = n >= h.budget;
  const pass = worst <= h.limit && long;
  if (!pass) fails++;
  console.log(
    `${pass ? 'PASS' : 'FAIL'}  ${h.name}: f${h.from}-f${h.to} = ${n} frames ` +
      `(budget ${h.budget}f${long ? '' : ' — TOO SHORT'}), worst frame-to-frame diff ` +
      `${worst.toFixed(3)} (limit ${h.limit}) at f${worstAt}`,
  );
}
console.log(fails === 0 ? '\nevery declared hold is still in the rendered pixels' : `\n${fails} hold(s) are not actually still`);
process.exit(fails === 0 ? 0 : 1);
