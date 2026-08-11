// No frame of the film may be an almost-empty canvas. Round 2 found 7 such frames where a
// transition grew over a shot that had already ended, so this is now a standing check.
// A frame is "empty" if its 160x90 greyscale std is tiny (nothing on screen) while it is bright
// (the page canvas) — i.e. flat light nothing. Real frames always carry structure.
import { execFileSync } from 'child_process';
import ffmpeg from 'ffmpeg-static';

const MP4 = process.argv[2] ?? 'out/eastwest-easyway-promo.mp4';
const W = 160, H = 90, SIZE = W * H;
const raw = execFileSync(ffmpeg, ['-hide_banner', '-loglevel', 'error', '-i', MP4,
  '-vf', `scale=${W}:${H},format=gray`, '-f', 'rawvideo', '-'], { maxBuffer: 1 << 30 });
const n = Math.floor(raw.length / SIZE);
const bad = [];
for (let f = 0; f < n; f++) {
  let sum = 0;
  for (let i = 0; i < SIZE; i++) sum += raw[f * SIZE + i];
  const mean = sum / SIZE;
  let v = 0;
  for (let i = 0; i < SIZE; i++) v += (raw[f * SIZE + i] - mean) ** 2;
  const std = Math.sqrt(v / SIZE);
  if (std < 8 && mean > 225) bad.push({ f, mean: +mean.toFixed(1), std: +std.toFixed(2) });
}
console.log(`${n} frames scanned`);
if (bad.length === 0) console.log('PASS  no near-empty frame in the film');
else console.log('FAIL  near-empty frames:', bad.map((b) => `f${b.f} (mean ${b.mean}, std ${b.std})`).join(', '));
process.exit(bad.length === 0 ? 0 : 1);
