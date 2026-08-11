// Shot 8 — `data/odometer-digit-roll`
// Reference implementation read before writing:
// demos/data/odometer-digit-roll/OdometerDigitRoll.tsx. Kept from the card: each place is a
// 0–9 strip inside an overflow box driven by a pure frame function, spin 0.85 rows/frame,
// per-place deceleration 7f apart LEFT→RIGHT (stopping right-to-left "reads as counting
// backwards"), 16f Easing.out(cubic) to target + HALF A ROW of overshoot then 6f back to the
// integer (no overshoot halves the mechanical feel), two speed-gated afterimage copies at
// ±half a row and 0.25/0.12 opacity that are dropped the moment a place stops, non-digit
// glyphs never roll, a whole-number deepening pulse with a 1.035 scale on the final lock, and
// ≥45f of true stillness afterwards (R1).
// Beat-locked: the three locks land on b83 / b83.5 / b84, i.e. the eighth-notes into the
// beat, so the "click, click, clunk" is on the music; the value is EastWest's published
// headline rate (up to 8.88% cash reward) and the digits shown are the real value's places.
import React from 'react';
import { AbsoluteFill, Easing, interpolate, interpolateColors, useCurrentFrame } from 'remotion';
import { SHOTS, localBeat } from '../beats';
import { CANVAS, FONT, INK, LIME, MAGENTA, MUTED, PURPLE } from '../brand';

const ROW = 210;
const DW = 118;
const FS = 190;
const SPIN = 0.85;
const DIGITS = [8, 8, 8];
// b82 / b82.5 / b83 — still the eighth-notes into the beat, pulled a full beat earlier than the
// first attempt so that ≥45 frames of true stillness survive before the wipe starts eating the
// frame at b87 (round 2 N9: the spec claimed 45f, the pixels had 38f, and both checks passed)
export const LOCK_BEATS = [82, 82.5, 83] as const;
const LOCKS = LOCK_BEATS.map((b) => localBeat(SHOTS.rewards, b));
const START = LOCKS.map((l) => l - 22); // 16f decel + 6f settle back
const FULL_LOCK = LOCKS[LOCKS.length - 1];

const posAt = (f: number, i: number): number => {
  const d = DIGITS[i];
  const s = START[i];
  const p0 = SPIN * s;
  const T = Math.ceil((p0 + 6 - d) / 10) * 10 + d;
  if (f < s) return SPIN * Math.max(f, 0);
  if (f < s + 16)
    return interpolate(f, [s, s + 16], [p0, T + 0.5], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
    });
  if (f < s + 22)
    return interpolate(f, [s + 16, s + 22], [T + 0.5, T], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
    });
  return T;
};

const Strip: React.FC<{ pos: number; color: string; opacity?: number; dy?: number }> = ({ pos, color, opacity = 1, dy = 0 }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: DW, transform: `translateY(${-(pos % 10) * ROW + dy}px)`, opacity }}>
    {Array.from({ length: 20 }).map((_, k) => (
      <div
        key={k}
        style={{
          width: DW, height: ROW, lineHeight: `${ROW}px`, textAlign: 'center', fontSize: FS,
          fontWeight: 800, fontVariantNumeric: 'tabular-nums', fontFamily: FONT, color,
        }}
      >
        {k % 10}
      </div>
    ))}
  </div>
);

const DigitReel: React.FC<{ frame: number; i: number; color: string }> = ({ frame, i, color }) => {
  const pos = posAt(frame, i);
  const gate = interpolate(Math.abs(pos - posAt(frame - 1, i)), [0.06, 0.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return (
    <div style={{ position: 'relative', width: DW, height: ROW, overflow: 'hidden' }}>
      {gate > 0.001 && (
        <>
          <Strip pos={pos} color={color} opacity={0.25 * gate} dy={ROW * 0.5} />
          <Strip pos={pos} color={color} opacity={0.12 * gate} dy={-ROW * 0.5} />
        </>
      )}
      <Strip pos={pos} color={color} />
    </div>
  );
};

const Glyph: React.FC<{ ch: string; color: string; w?: number }> = ({ ch, color, w }) => (
  <div
    style={{
      width: w, height: ROW, lineHeight: `${ROW}px`, textAlign: 'center', fontSize: FS,
      fontWeight: 800, fontFamily: FONT, color,
    }}
  >
    {ch}
  </div>
);

export const SceneRewards: React.FC = () => {
  const frame = useCurrentFrame();
  const inT = interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  const reelsIn = interpolate(frame, [16, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const inkNow = interpolateColors(frame, [FULL_LOCK, FULL_LOCK + 4, FULL_LOCK + 8], [INK, '#000000', INK]);
  const pulseScale = interpolate(frame, [FULL_LOCK, FULL_LOCK + 4, FULL_LOCK + 8], [1, 1.035, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.quad),
  });
  const labelOp = interpolate(frame, [FULL_LOCK + 3, FULL_LOCK + 21], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad),
  });

  return (
    <AbsoluteFill style={{ background: CANVAS, overflow: 'hidden' }}>
      {/* brand wash so the shot belongs to the same film as the purple title cards */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(1200px 700px at 50% 46%, rgba(84,39,133,0.10), rgba(178,0,111,0.05) 55%, transparent 78%)`,
        }}
      />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 8, background: `linear-gradient(90deg, ${PURPLE}, ${MAGENTA})` }} />

      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: 236, textAlign: 'center',
          fontFamily: FONT, fontSize: 34, fontWeight: 600, letterSpacing: '0.28em',
          color: MAGENTA, opacity: inT, transform: `translateY(${(1 - inT) * 14}px)`,
        }}
      >
        UP TO
      </div>

      <div
        style={{
          position: 'absolute', left: 0, top: 320, width: 1920, display: 'flex', justifyContent: 'center',
          transform: `scale(${pulseScale})`, transformOrigin: '960px 105px', opacity: reelsIn,
        }}
      >
        <DigitReel frame={frame} i={0} color={inkNow} />
        <Glyph ch="." color={inkNow} w={64} />
        <DigitReel frame={frame} i={1} color={inkNow} />
        <DigitReel frame={frame} i={2} color={inkNow} />
        <Glyph ch="%" color={MAGENTA} w={170} />
      </div>

      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: 596, display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: 22, opacity: labelOp,
        }}
      >
        <div style={{ width: 300, height: 6, borderRadius: 3, background: LIME }} />
        <div style={{ fontFamily: FONT, fontSize: 52, fontWeight: 500, color: INK, letterSpacing: '-0.01em' }}>
          cash reward on qualified card spend
        </div>
        <div style={{ fontFamily: FONT, fontSize: 30, fontWeight: 300, color: MUTED }}>
          plus rewards points on everything else
        </div>
      </div>
    </AbsoluteFill>
  );
};
