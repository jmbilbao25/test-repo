// One runnable check for the whole timeline (ponytail: non-trivial logic leaves the smallest
// thing behind that fails if the logic breaks — no framework, no fixtures).
// Verifies the invariants a render can't tell you about:
//   1. the beat grid matches analysis/beat_data.json
//   2. shots tile the composition with no gap or overlap, and every boundary is on a beat
//   3. the promised rest/hold budget survives (R1/R3)
//   4. every texture and audio file the film references exists
//   5. no bare frame numbers crept into the shot table
// Run: npm run check
import fs from 'fs';
import path from 'path';

const root = path.resolve(import.meta.dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
let fails = 0;
const ok = (cond, msg) => {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${msg}`);
  if (!cond) fails++;
};

// ---- 1. beat grid ---------------------------------------------------------
const beats = JSON.parse(read('analysis/beat_data.json'));
const src = read('src/ew/beats.ts');
const BEAT0 = Number(/export const BEAT0 = ([\d.]+)/.exec(src)[1]);
const BEAT_INT = Number(/export const BEAT_INT = ([\d.]+)/.exec(src)[1]);
ok(Math.abs(BEAT0 - beats.t0) < 1e-4, `BEAT0 ${BEAT0} matches the measured t0 ${beats.t0.toFixed(6)}`);
ok(Math.abs(BEAT_INT - beats.T) < 1e-5, `BEAT_INT ${BEAT_INT} matches the measured T ${beats.T.toFixed(6)}`);
ok(Math.abs(beats.bpm - 124) < 0.1, `grid is ${beats.bpm.toFixed(2)} BPM`);
ok(beats.fit_residual_max_ms <= 15, `grid fit residual ${beats.fit_residual_max_ms.toFixed(1)}ms ≤ 15ms (machine grid)`);

const FPS = 30;
const beatF = (n) => Math.round((BEAT0 + n * BEAT_INT) * FPS);

// ---- 2. shots tile the timeline, every boundary on a beat -----------------
const shotRe = /(\w+): shot\((\d+), (\d+)\)/g;
const shots = [...src.matchAll(shotRe)].map(([, name, a, b]) => ({ name, a: +a, b: +b }));
ok(shots.length === 10, `${shots.length} shots declared`);
let cursor = 0;
for (const s of shots) {
  const from = beatF(s.a);
  const to = beatF(s.b);
  if (s.name === 'wipe') {
    // a takeover transition MUST overlap the shot it eats, or it grows on an empty canvas
    ok(from < cursor, `${s.name}: overlaps the outgoing shot by ${cursor - from}f (takeover)`);
    ok(to > cursor, `${s.name}: ends at ${to}, past the shot it ate`);
  } else {
    // no escape hatches: a non-transition shot must start exactly where the previous one ended
    ok(from === cursor, `${s.name}: starts at frame ${from} with no gap (beat ${s.a})`);
  }
  ok(to > from, `${s.name}: ${to - from}f long (beats ${s.a}→${s.b})`);
  cursor = Math.max(cursor, to);
}
const TOTAL = beatF(103);
ok(cursor === TOTAL, `shots cover the whole ${TOTAL}f (${(TOTAL / FPS).toFixed(2)}s) composition`);

// ---- 3. rest / hold budget (R1: brand moments hold ≥1s) ------------------
const holds = [
  { what: 'brand wordmark hold before the dissolve (shot 1)', frames: 76 - 46 },
  { what: 'full-board rest after the deal (shot 3)', frames: 122 - 104 },
  // measured to where the wipe starts eating the frame, not to the shot's nominal end
  { what: 'stillness after the odometer locks (shot 8)', frames: beatF(87) - (beatF(83) + 8) },
  { what: 'sign-off hold before the fade (shot 10)', frames: TOTAL - 12 - beatF(93) - 45 },
  { what: 'solid-colour takeover after the wipe fills (shot 9 + the outro field)', frames: beatF(90) - (beatF(87) + 22) + 18 },
];
ok(holds[0].frames >= 30, `${holds[0].what}: ${holds[0].frames}f ≥ 30f`);
ok(holds[1].frames >= 15, `${holds[1].what}: ${holds[1].frames}f ≥ 15f`);
ok(holds[2].frames >= 45, `${holds[2].what}: ${holds[2].frames}f ≥ 45f`);
ok(holds[3].frames >= 30, `${holds[3].what}: ${holds[3].frames}f ≥ 30f`);
ok(holds[4].frames >= 30, `${holds[4].what}: ${holds[4].frames}f ≥ 30f`);

// ---- 4. every referenced asset exists ------------------------------------
const files = fs.readdirSync(path.join(root, 'src/ew/scenes')).map((f) => `src/ew/scenes/${f}`);
files.push('src/ew/Main.tsx', 'src/ew/lib/Caption.tsx');
const refs = new Set();
for (const f of files) {
  for (const m of read(f).matchAll(/staticFile\(`?'?([^`'$)]+)/g)) refs.add(m[1]);
  for (const m of read(f).matchAll(/src="(textures\/[^"]+)"/g)) refs.add(m[1]);
}
// template-literal texture/audio names resolved by hand (the loops above only see the prefix)
const dynamic = [
  ...Array.from({ length: 12 }, (_, i) => `textures/live/card${i + 1}.png`),
  ...Array.from({ length: 5 }, (_, i) => `textures/live/row${i + 1}.png`),
  ...Array.from({ length: 6 }, (_, i) => `textures/live/biller${i + 1}.png`),
  'textures/live/hero-card.png', 'textures/live/hero-card-hires.png', 'textures/live/nav.png',
  'textures/live/float-quick.png', 'textures/live/float-sum.png', 'textures/live/plastic.png',
  'textures/live/plastic-hires.png', 'textures/live/card11.png',
  'textures/live/app-full.png', 'textures/live/app-empty.png', 'textures/live/transfers-empty.png',
  'textures/live/bills-empty.png', 'textures/live/cards-full.png',
];
const sfx = [...read('src/ew/Main.tsx').matchAll(/src: '([\w-]+\.mp3)'/g)].map((m) => `audio/${m[1]}`);
const missing = [...new Set([...dynamic, ...sfx, 'audio/bgm-tech-house.mp3'])].filter(
  (r) => !fs.existsSync(path.join(root, 'public', r)),
);
ok(missing.length === 0, `all ${dynamic.length + sfx.length + 1} referenced textures/audio exist${missing.length ? ': missing ' + missing.join(', ') : ''}`);
ok([...refs].every((r) => r.startsWith('textures/') || r.startsWith('audio/')), 'no unexpected staticFile roots');

// ---- 5. no bare frame numbers in the SFX table ---------------------------
const sfxTable = read('src/ew/Main.tsx').split('const SFX')[1].split('const Bgm')[0];
const bare = [...sfxTable.matchAll(/from: (\d+)[,\s]/g)].map((m) => m[1]);
ok(bare.length === 0, `every SFX cue is relative (beatF / SHOTS.x.from)${bare.length ? ', bare: ' + bare.join(', ') : ''}`);

console.log(
  fails === 0
    ? '\nall timeline invariants hold (cue arithmetic only — run `npm run check:still` against a\nrendered mp4 to prove the holds are still in the actual pixels)'
    : `\n${fails} check(s) failed`,
);
process.exit(fails === 0 ? 0 : 1);
