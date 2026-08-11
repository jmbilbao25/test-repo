// Shot 9 — `transition/color-block-step-wipe` (variant A)
// Reference implementation read before writing:
// demos/transition/color-block-step-wipe/ColorBlockStepWipe.tsx. Kept from the card: the
// stepVal threshold table IS the grammar — zero interpolation anywhere, width and height jump
// on DIFFERENT thresholds so the block reads as growing rather than scaling, unequal jump
// gaps (equal gaps read as a dropped-frame GIF), and the badge fakes its overshoot with three
// hard steps 0.55 → 1.12 → 1 (a spring here would look like it came from another film).
// Adapted: 4 jumps on UNEQUAL 6/8/6f gaps (equal gaps are the card's dropped-frame-GIF
// failure), each jump also hard-cutting the block's colour up the brand ramp purple → magenta,
// and the finished magenta field is left standing as the stage the outro fades up from (the
// card's "takeover" use). The shot runs 3 beats (44f) and starts a beat BEFORE the shot it eats,
// which keeps playing underneath for the whole growth — a takeover has to eat something.
// The block grows from the LEFT EDGE, not from the centre: centred, its first two steps read as
// a redaction bar laid across the 8.88% headline (round 2, f1265–f1277).
// STEPS/BADGE_STEPS are exported because the SFX table pins its hits to them — the two used to
// be maintained by hand and drifted apart the moment the shot was re-timed (round 2, N3).
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { FONT, LIME, MAGENTA, PURPLE, PURPLE_DEEP } from '../brand';

/** frame thresholds of the four hard jumps, and of the badge's three-step pop + two-step exit */
export const STEPS = [2, 8, 16, 22] as const;
export const BADGE_STEPS = [24, 30, 36] as const;
export const BADGE_OUT = [41, 43] as const;

const stepVal = (frame: number, steps: Array<[number, number]>): number => {
  let v = steps[0][1];
  for (const [f, val] of steps) if (frame >= f) v = val;
  return v;
};
const stepStr = (frame: number, steps: Array<[number, string]>): string => {
  let v = steps[0][1];
  for (const [f, val] of steps) if (frame >= f) v = val;
  return v;
};

export const StepWipe: React.FC = () => {
  const frame = useCurrentFrame();
  const w = stepVal(frame, [[0, 0], [STEPS[0], 300], [STEPS[1], 900], [STEPS[2], 1440], [STEPS[3], 1920]]);
  const h = stepVal(frame, [[0, 0], [STEPS[0], 96], [STEPS[1], 96], [STEPS[2], 360], [STEPS[3], 1080]]);
  // every step is a brand token: deep purple → purple → magenta → magenta
  const color = stepStr(frame, [[0, PURPLE_DEEP], [STEPS[0], PURPLE], [STEPS[1], PURPLE], [STEPS[2], MAGENTA], [STEPS[3], MAGENTA]]);
  // the badge steps out the same way it stepped in, so it exits instead of vanishing on the cut
  const badge = stepVal(frame, [
    [0, 0], [BADGE_STEPS[0], 0.55], [BADGE_STEPS[1], 1.12], [BADGE_STEPS[2], 1],
    [BADGE_OUT[0], 0.6], [BADGE_OUT[1], 0],
  ]);

  return (
    <AbsoluteFill style={{ background: 'transparent', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ position: 'absolute', left: 0, top: 540 - h / 2, width: w, height: h, background: color }} />
      {badge > 0 ? (
        <div
          style={{
            width: 190, height: 190, borderRadius: '50%', background: LIME,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transform: `scale(${badge})`,
            boxShadow: '0 10px 30px rgba(24,6,48,0.35)',
          }}
        >
          <span style={{ fontFamily: FONT, fontSize: 74, fontWeight: 700, color: PURPLE_DEEP, letterSpacing: '-0.03em' }}>EW</span>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
