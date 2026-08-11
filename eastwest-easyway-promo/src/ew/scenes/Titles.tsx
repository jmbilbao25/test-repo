// Shots 2 and 5 — the two title cards.
//
// TitleSweep = `typography/gradient-word-sweep`, reference implementation read before
// writing: demos/typography/gradient-word-sweep/GradientWordSweep.tsx. Kept verbatim in
// structure and timing: 12f enter, 18f fill (FILL_START 12 → FILL_END 30 — "fast, a slower
// sweep reads as a progress bar"), 34%-wide wavefront trail that is brightest at the head
// and fades to steady over 10f, four glow layers at 0.55/0.62/0.72 (the demo's judged
// ceiling — 0.75+ was rejected as too strong), sparse magenta lightning with 6/2.4/1.4 and
// 4.5/1.9/1.1 stroke triples on a mulberry32 seed, rest of the line pure white and still.
// Re-skinned: the charge gradient and the bolts are lime→magenta→purple.
//
// TitleMarker = `typography/marker-underline-title`: the line lands first, then 6f later a
// 10f marker stroke draws left→right under the keyword, tapered at both ends, rough-edged,
// tilting slightly up, sitting ~0.1em under the baseline.
import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from 'remotion';
import { mulberry32 } from '../lib/rand';
import { CANVAS, FONT, INK, LIME, MAGENTA, MUTED, PURPLE, PURPLE_DEEP } from '../brand';

// every stop is a brand token (or a tint of one) — no borrowed demo colours
const GRAD = `linear-gradient(92deg, ${LIME} 0%, ${MAGENTA} 58%, ${PURPLE} 100%)`;
const FILL_START = 12;
const FILL_END = 30;
const LIGHT_START = FILL_END + 3;
const BOLT_W = 520;

const rand = mulberry32(20260811);
const FLICKER: number[] = Array.from({ length: 200 }, () => rand());

type Bolt = { d: string; long: boolean };
const makeLongBolt = (r: () => number): Bolt => {
  const x0 = 24 + r() * 170;
  const x1 = x0 + 130 + r() * 240;
  const yBase = 38 + r() * 42;
  const n = 7 + Math.floor(r() * 4);
  let d = `M ${x0.toFixed(1)} ${(yBase + 26 + r() * 20).toFixed(1)}`;
  for (let i = 1; i <= n; i++) {
    const x = x0 + ((x1 - x0) * i) / n + (r() - 0.5) * 22;
    const arch = Math.sin((i / n) * Math.PI) * -22;
    const y = yBase + arch + (r() - 0.5) * 30 + (i === n ? 30 + r() * 18 : 0);
    d += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  return { d, long: true };
};
const makeShortBolt = (r: () => number): Bolt => {
  const x = 50 + r() * (BOLT_W - 120);
  const y0 = 72 + r() * 24;
  const y1 = y0 + 55 + r() * 45;
  const n = 4 + Math.floor(r() * 3);
  let d = `M ${x.toFixed(1)} ${y0.toFixed(1)}`;
  for (let i = 1; i <= n; i++) {
    const y = y0 + ((y1 - y0) * i) / n;
    d += ` L ${(x + (r() - 0.5) * 30).toFixed(1)} ${y.toFixed(1)}`;
  }
  return { d, long: false };
};
const BOLTS: Bolt[] = Array.from({ length: 16 }, (_, i) => (i % 3 === 0 ? makeShortBolt(rand) : makeLongBolt(rand)));
// The card's density ceiling is ≤2 bolts on screen with >8f between strikes. Build the
// schedule with an enforced 9f minimum gap instead of scattering 30 random events (which
// measured 4 concurrent bolts in review).
const FLASHES = (() => {
  const out: { at: number; life: number; bolt: number }[] = [];
  let t = LIGHT_START + 2;
  while (t < LIGHT_START + 62 && out.length < 8) {
    out.push({ at: Math.round(t), life: 2 + Math.floor(rand() * 3), bolt: Math.floor(rand() * BOLTS.length) });
    t += 9 + rand() * 7;
  }
  return out;
})();

export const TitleSweep: React.FC<{ before: string; keyword: string; after: string; sub: string }> = ({
  before,
  keyword,
  after,
  sub,
}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  const p = interpolate(frame, [FILL_START, FILL_END], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad),
  });
  const pPct = p * 100;
  const filling = frame >= FILL_START && frame <= FILL_END + 4;
  const headFade = interpolate(frame, [FILL_END, FILL_END + 6], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const trailFade = interpolate(frame, [FILL_END, FILL_END + 10], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const TRAIL = 34;
  const trailMask =
    `linear-gradient(90deg, transparent 0%, transparent ${Math.max(0, pPct - TRAIL)}%, ` +
    `rgba(0,0,0,0.9) ${Math.max(0, pPct - 3)}%, rgba(0,0,0,0.9) ${Math.min(100, pPct + 1)}%, ` +
    `transparent ${Math.min(100, pPct + 6)}%)`;
  const noise = FLICKER[Math.min(frame, FLICKER.length - 1)];
  const active = FLASHES.filter((f) => frame >= f.at && frame < f.at + f.life);
  const glowLvl =
    interpolate(frame, [FILL_START, FILL_END], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) *
      (0.82 + 0.18 * noise) +
    (active.length > 0 ? 0.35 : 0);

  const softMask = (soft: number): React.CSSProperties =>
    p >= 1
      ? {}
      : {
          WebkitMaskImage: `linear-gradient(90deg, #000 0%, #000 ${Math.max(0, pPct - soft)}%, transparent ${Math.min(100, pPct + soft * 0.6)}%)`,
          maskImage: `linear-gradient(90deg, #000 0%, #000 ${Math.max(0, pPct - soft)}%, transparent ${Math.min(100, pPct + soft * 0.6)}%)`,
        };

  const lineStyle: React.CSSProperties = {
    fontFamily: FONT,
    fontWeight: 600,
    fontSize: 92,
    letterSpacing: '-0.025em',
    lineHeight: 1.2,
    color: '#ffffff',
    whiteSpace: 'nowrap',
  };
  const gradText: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    backgroundImage: GRAD,
    WebkitBackgroundClip: 'text',
    backgroundClip: 'text',
    color: 'transparent',
  };

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(1300px 760px at 50% 46%, ${PURPLE} 0%, ${PURPLE_DEEP} 58%, #180630 100%)`,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <div
        style={{
          position: 'absolute', left: 550, top: 400, width: 820, height: 300, borderRadius: '50%',
          background: `radial-gradient(closest-side, rgba(213,224,77,0.45), rgba(178,0,111,0.26) 55%, transparent 78%)`,
          filter: 'blur(38px)',
          opacity: 0.5 * glowLvl,
        }}
      />
      <div style={{ textAlign: 'center', opacity: enter, transform: `translateY(${(1 - enter) * 36}px)` }}>
        <div style={lineStyle}>
          {before}
          <span style={{ position: 'relative', display: 'inline-block' }}>
            <span>{keyword}</span>
            <span aria-hidden style={{ ...gradText, ...softMask(14), filter: 'blur(46px) saturate(1.6)', opacity: 0.55 * glowLvl, transform: 'scale(1.05)' }}>{keyword}</span>
            <span aria-hidden style={{ ...gradText, ...softMask(10), filter: 'blur(18px) saturate(1.4) brightness(1.15)', opacity: 0.62 * glowLvl }}>{keyword}</span>
            <span aria-hidden style={{ ...gradText, ...softMask(7), filter: 'blur(6px) brightness(1.25)', opacity: 0.72 * Math.min(1, glowLvl + 0.1) }}>{keyword}</span>
            <span aria-hidden style={{ ...gradText, clipPath: `inset(-25% ${100 - pPct}% -25% 0)` }}>{keyword}</span>
            {trailFade > 0.01 && (
              <span
                aria-hidden
                style={{
                  ...gradText,
                  WebkitMaskImage: trailMask,
                  maskImage: trailMask,
                  filter: 'blur(9px) saturate(1.7) brightness(1.7)',
                  opacity: 0.95 * trailFade,
                }}
              >
                {keyword}
              </span>
            )}
            {filling && p < 1 && (
              <span
                aria-hidden
                style={{
                  position: 'absolute', inset: 0, color: '#fff',
                  clipPath: `inset(-25% ${Math.max(0, 100 - pPct)}% -25% ${Math.max(0, pPct - 10)}%)`,
                  filter: 'blur(3px)',
                  opacity: 0.9 * headFade,
                  textShadow: '0 0 22px rgba(255,255,255,0.9), 0 0 55px rgba(228,120,190,0.8)',
                }}
              >
                {keyword}
              </span>
            )}
            <svg
              aria-hidden
              viewBox={`0 0 ${BOLT_W} 240`}
              style={{ position: 'absolute', left: -25, top: -62, width: BOLT_W, height: 240, overflow: 'visible', pointerEvents: 'none' }}
            >
              {active.map((f, i) => {
                const b = BOLTS[f.bolt];
                const decay = 1 - (frame - f.at) / f.life;
                return (
                  <g key={`${f.at}-${i}`} opacity={Math.min(1, 1.1 * decay)}>
                    <path d={b.d} fill="none" stroke="rgba(178,0,111,0.62)" strokeWidth={b.long ? 6 : 4.5} strokeLinejoin="miter" style={{ filter: 'blur(6px)' }} />
                    <path d={b.d} fill="none" stroke="rgba(228,120,190,0.9)" strokeWidth={b.long ? 2.4 : 1.9} strokeLinejoin="miter" style={{ filter: 'blur(1.5px)' }} />
                    <path d={b.d} fill="none" stroke="#ffe4f4" strokeWidth={b.long ? 1.4 : 1.1} strokeLinejoin="miter" />
                  </g>
                );
              })}
            </svg>
          </span>
          {after}
        </div>
        <div style={{ fontFamily: FONT, fontSize: 44, fontWeight: 300, color: 'rgba(255,255,255,0.8)', marginTop: 30, letterSpacing: '-0.01em' }}>
          {sub}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------

/** Rough, thickness-varying marker stroke, drawn left→right. Tapered ends (0.6x of the
 * middle), noisy edges, a slight left-low/right-high tilt so it follows the type. */
const markerPath = (w: number, h: number, seed: number): string => {
  const r = mulberry32(seed);
  const n = 22;
  const top: string[] = [];
  const bottom: string[] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const taper = 0.6 + 0.4 * Math.sin(Math.PI * Math.min(1, Math.max(0, t))) * 1.0;
    const thick = h * Math.min(1, taper);
    const midY = h / 2 - t * h * 0.22 + (r() - 0.5) * h * 0.1; // rises to the right
    top.push(`${(t * w).toFixed(1)} ${(midY - thick / 2 + (r() - 0.5) * 2.4).toFixed(1)}`);
    bottom.push(`${((1 - t) * w).toFixed(1)} ${(h / 2 - (1 - t) * h * 0.22 + thick / 2 + (r() - 0.5) * 2.4).toFixed(1)}`);
  }
  return `M ${top.join(' L ')} L ${bottom.join(' L ')} Z`;
};

export const TitleMarker: React.FC<{ before: string; keyword: string; after: string; sub: string }> = ({
  before,
  keyword,
  after,
  sub,
}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  // the line lands at 14; the stroke starts 6f later and takes 10f (card: 8–12f)
  const draw = interpolate(frame, [20, 30], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.2, 0.85, 0.35, 1),
  });
  const subIn = interpolate(frame, [32, 44], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const MW = keyword.length * 43 + 20;
  const MH = 24;

  return (
    <AbsoluteFill style={{ background: CANVAS, justifyContent: 'center', alignItems: 'center' }}>
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: 0, height: 8,
          background: `linear-gradient(90deg, ${PURPLE}, ${MAGENTA})`,
        }}
      />
      <div style={{ textAlign: 'center', opacity: enter, transform: `translateY(${(1 - enter) * 26}px)` }}>
        <div style={{ fontFamily: FONT, fontSize: 92, fontWeight: 600, color: INK, letterSpacing: '-0.025em', lineHeight: 1.2, whiteSpace: 'nowrap' }}>
          {before}
          <span style={{ position: 'relative', display: 'inline-block' }}>
            <svg
              width={MW}
              height={MH}
              viewBox={`0 0 ${MW} ${MH}`}
              style={{
                position: 'absolute', left: -10, bottom: 6, width: MW, height: MH,
                clipPath: `inset(0 ${(1 - draw) * 100}% 0 0)`,
                pointerEvents: 'none',
              }}
            >
              <path d={markerPath(MW, MH, 424242)} fill={LIME} opacity={0.95} />
            </svg>
            <span style={{ position: 'relative' }}>{keyword}</span>
          </span>
          {after}
        </div>
        <div style={{ fontFamily: FONT, fontSize: 44, fontWeight: 300, color: MUTED, marginTop: 28, opacity: subIn, letterSpacing: '-0.01em' }}>
          {sub}
        </div>
      </div>
    </AbsoluteFill>
  );
};
