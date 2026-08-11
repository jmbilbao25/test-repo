// Shot 10 — `outro/outro-group-photo-launch`
// Reference implementation read before writing:
// template/src/aifl/live/SceneOutroLive.tsx. Kept from the card: 9 elements — one delegate
// per feature shown in the film (Q8's checklist) — fly in from all four sides on 3f cues with
// 12f flights on bezier(0.34,1.4,0.44,1) (the note in the template's own source: the older
// bezier "never crossed 1", so it never really overshot), in-flight rot×2 → settled rot inside
// ±5°, scale ×1.12→1, a ghost lagging 8% of the path at blur(8px), a 6f landing glow, the
// whole cast stepping BACK (−12% opacity, −8% saturation) as the wordmark takes the stage, a
// crane that lands the photo layer (rotateX 4°→0, scale 1.06→1) and then breathes in +0.035,
// the launch-atmosphere trio (one 2–14f light sweep, a stage light behind the wordmark at
// 0→0.5→0.25, index-derived dust), the wordmark letterpress, a rule that grows and shoots
// ±190px extension lines, one letter-spacing breath, and a full second of sign-off hold (R1).
//
// Review fixes (independent final review, 2026-08-11):
//  - the crane's breathing push now STOPS at STAMP+40 and the transform is locked for the
//    last ~100 frames, so the closing brand moment is genuinely still (R1's central case);
//  - the stage is the deep-purple/magenta field the step wipe hands over, not a near-white
//    page: light UI cards and lime dust now read against it and the outro is the film's
//    brightest-energy frame instead of its calmest (Q8);
//  - the wordmark's accent is lime in BOTH lockups (it used to switch token mid-film);
//  - the rewards feature gets its own delegate in the group photo (it had none);
//  - the sign-off line no longer repeats the opening kicker, and the source line is 34px.
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { PageCam, CamKey } from '../lib/PageCam';
import { SHOTS } from '../beats';
import { FONT, LIME, MAGENTA, PURPLE_DEEP } from '../brand';
import layout from '../live-layout.json';

const PAGE_H = layout.app.pageH;
const LETTERS = 'EastWest'.split('');
const FLY_EASE = Easing.bezier(0.34, 1.4, 0.44, 1);
const CRANE_EASE = Easing.bezier(0.3, 0, 0.2, 1);
const STAMP = 43; // localBeat(SHOTS.outro, 93) — the film's biggest kick
const FREEZE = STAMP + 40; // camera locks here; everything after is a true hold

type FlyEl = {
  key: string; file: string; w: number; h: number; cx: number; cy: number;
  scale: number; rot: number; dx: number; dy: number; radius: number; cue: number;
};

// render order = cue order, so later arrivals stack on top. One delegate per feature:
// nav (the app), hero card (balance), send-money card (transfers), plastic (card control),
// card-lock card (security), transfer row (InstaPay/PESONet), biller row (bills),
// rewards card (8.88%), and the transfer summary tile (24/7 limits).
const ELS: FlyEl[] = [
  { key: 'nav', file: 'nav.png', w: 1920, h: 72, cx: 960, cy: 78, scale: 0.62, rot: 0, dx: 0, dy: -140, radius: 8, cue: 4 },
  { key: 'hero', file: 'hero-card.png', w: 720, h: 300, cx: 244, cy: 316, scale: 0.62, rot: -5, dx: -560, dy: 0, radius: 24, cue: 7 },
  { key: 'card3', file: 'card3.png', w: 464, h: 240, cx: 1610, cy: 300, scale: 0.7, rot: 4, dx: 540, dy: 0, radius: 24, cue: 10 },
  { key: 'plastic', file: 'plastic.png', w: 560, h: 344, cx: 1580, cy: 610, scale: 0.6, rot: 2.5, dx: 400, dy: -160, radius: 24, cue: 13 },
  { key: 'card10', file: 'card10.png', w: 464, h: 240, cx: 300, cy: 730, scale: 0.62, rot: 3, dx: -430, dy: 300, radius: 24, cue: 16 },
  { key: 'row1', file: 'row1.png', w: 1370, h: 84, cx: 1330, cy: 900, scale: 0.6, rot: -3, dx: 470, dy: 260, radius: 16, cue: 19 },
  { key: 'biller1', file: 'biller1.png', w: 1370, h: 78, cx: 600, cy: 950, scale: 0.58, rot: 2, dx: 0, dy: 330, radius: 16, cue: 22 },
  { key: 'card11', file: 'card11.png', w: 464, h: 240, cx: 700, cy: 196, scale: 0.5, rot: -1.5, dx: 0, dy: -260, radius: 24, cue: 25 },
  { key: 'sum', file: 'float-sum.png', w: 464, h: 166, cx: 250, cy: 540, scale: 0.7, rot: -2, dx: -420, dy: 0, radius: 24, cue: 28 },
];

const DUST = Array.from({ length: 22 }, (_, i) => ({
  x: (i * 439 + 137) % 1920,
  y0: (i * 613 + 271) % 1080,
  rise: 0.3 + (i % 5) * 0.11,
  swayAmp: 9 + (i % 4) * 5,
  swayFreq: 0.022 + (i % 3) * 0.008,
  phase: (i * 0.83) % (Math.PI * 2),
  size: 2.5 + (i % 3) * 0.7,
  opacity: 0.3 + ((i * 7) % 5) * 0.1,
}));

const CAM: CamKey[] = [{ frame: 0, cx: 960, cy: 760, zoom: 0.75 }];

export const SceneOutro: React.FC = () => {
  const frame = useCurrentFrame();
  const duration = SHOTS.outro.duration; // 188

  // front-loaded so the page is already texture by the time the magenta field lifts (N13)
  const blur = interpolate(frame, [0, 10], [0, 14], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.4, 1),
  });
  // the step wipe's magenta field is still standing: the stage fades up out of it
  const fieldOut = interpolate(frame, [0, 18], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const rule = interpolate(frame, [STAMP + 15, STAMP + 27], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.3, 0, 0.2, 1),
  });
  const tag = interpolate(frame, [STAMP + 25, STAMP + 37], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const legal = interpolate(frame, [STAMP + 53, STAMP + 67], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const fadeOut = interpolate(frame, [duration - 12, duration], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const recede = interpolate(frame, [STAMP - 1, STAMP + 7], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const craneT = interpolate(frame, [0, 40], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: CRANE_EASE,
  });
  // R1: the push stops well before the end, so the sign-off is a real hold, not a slow drift
  const pushT = interpolate(frame, [40, FREEZE], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const camScale = 1.06 - 0.06 * craneT + 0.035 * pushT;
  const camTilt = 4 * (1 - craneT);

  const sweepX = interpolate(frame, [2, 14], [-700, 2020], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.6, 1),
  });
  const sweepOpacity = interpolate(frame, [2, 5, 11, 14], [0, 0.16, 0.16, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const stageLight = interpolate(frame, [STAMP - 1, STAMP + 7, STAMP + 15], [0, 0.62, 0.34], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const vignette = interpolate(frame, [STAMP - 1, STAMP + 11], [0, 0.35], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const ruleExt = interpolate(frame, [STAMP + 15, STAMP + 23], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.3, 0, 0.2, 1),
  });
  const ruleExtFade = interpolate(frame, [STAMP + 23, STAMP + 29], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const wordSpacing = interpolate(frame, [STAMP + 19, STAMP + 23], [-0.03, -0.02], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.3, 0, 0.2, 1),
  });

  return (
    <AbsoluteFill style={{ background: PURPLE_DEEP }}>
      {/* the magenta block the wipe left standing, handing the stage over */}
      <AbsoluteFill style={{ background: MAGENTA, opacity: fieldOut }} />

      <AbsoluteFill style={{ opacity: fadeOut }}>
        <AbsoluteFill
          style={{ transform: `perspective(1400px) rotateX(${camTilt}deg) scale(${camScale})`, transformOrigin: '50% 45%' }}
        >
          <AbsoluteFill style={{ opacity: 1 - fieldOut }}>
            <PageCam src="textures/live/app-full.png" pageH={PAGE_H} keys={CAM} blur={blur} saturate={0.9} />
            {/* deep-purple stage scrim: light UI cards and lime dust read against it */}
            <AbsoluteFill
              style={{
                background:
                  'radial-gradient(1300px 820px at 50% 48%, rgba(42,15,71,0.55), rgba(42,15,71,0.8) 58%, rgba(24,6,48,0.93))',
                pointerEvents: 'none',
              }}
            />
          </AbsoluteFill>

          <AbsoluteFill style={{ pointerEvents: 'none' }}>
            {ELS.map((el) => {
              if (frame < el.cue) return null;
              const t = interpolate(frame, [el.cue, el.cue + 12], [0, 1], {
                extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: FLY_EASE,
              });
              const linT = interpolate(frame, [el.cue, el.cue + 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
              const opacity = interpolate(frame, [el.cue, el.cue + 3], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
              const x = el.dx * (1 - t);
              const y = el.dy * (1 - t);
              const rot = el.rot * (2 - t);
              const scale = el.scale * (1.12 - 0.12 * t);
              const air = Math.max(0, 1 - t);
              const shadow =
                air > 0.01
                  ? `0 ${10 + 26 * air}px ${24 + 46 * air}px rgba(12,3,24,${0.3 + 0.14 * air}), 0 2px 6px rgba(12,3,24,.2)`
                  : '0 12px 28px rgba(12,3,24,.34), 0 2px 6px rgba(12,3,24,.2)';
              const glow = interpolate(frame, [el.cue + 12, el.cue + 18], [0.4, 0], {
                extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
              });
              const glowR = el.w * el.scale * 0.5;
              const common: React.CSSProperties = {
                position: 'absolute',
                left: el.cx - el.w / 2,
                top: el.cy - el.h / 2,
                width: el.w,
                height: el.h,
                borderRadius: el.radius,
                overflow: 'hidden',
                transformOrigin: 'center center',
              };
              return (
                <div key={el.key}>
                  {linT > 0.05 && linT < 0.95 ? (
                    <div
                      style={{
                        ...common,
                        transform: `translate(${x + el.dx * 0.08}px, ${y + el.dy * 0.08}px) rotate(${rot}deg) scale(${scale})`,
                        opacity: 0.2 * Math.max(0, 1 - linT),
                        filter: 'blur(8px)',
                      }}
                    >
                      <Img src={staticFile(`textures/live/${el.file}`)} style={{ position: 'absolute', inset: 0, width: el.w, height: el.h, display: 'block' }} />
                    </div>
                  ) : null}
                  <div
                    style={{
                      ...common,
                      transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scale(${scale})`,
                      boxShadow: shadow,
                      opacity: opacity * (1 - 0.12 * recede),
                      filter: `saturate(${1 - 0.08 * recede})`,
                    }}
                  >
                    <Img src={staticFile(`textures/live/${el.file}`)} style={{ position: 'absolute', inset: 0, width: el.w, height: el.h, display: 'block' }} />
                  </div>
                  {frame >= el.cue + 12 && frame < el.cue + 18 ? (
                    <div
                      style={{
                        position: 'absolute', left: el.cx - glowR, top: el.cy - glowR, width: glowR * 2, height: glowR * 2,
                        borderRadius: '50%',
                        background: 'radial-gradient(circle, rgba(213,224,77,0.55), rgba(213,224,77,0) 70%)',
                        opacity: glow,
                      }}
                    />
                  ) : null}
                </div>
              );
            })}
          </AbsoluteFill>
        </AbsoluteFill>

        {/* lime dust drifting up the dark stage */}
        <AbsoluteFill style={{ pointerEvents: 'none' }}>
          {DUST.map((d, i) => (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: d.x + Math.sin(frame * d.swayFreq + d.phase) * d.swayAmp,
                top: (((d.y0 - frame * d.rise) % 1080) + 1080) % 1080,
                width: d.size, height: d.size, borderRadius: '50%', background: LIME, opacity: d.opacity,
              }}
            />
          ))}
        </AbsoluteFill>

        {sweepOpacity > 0 ? (
          <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'overlay' }}>
            <div
              style={{
                position: 'absolute', top: 0, bottom: 0, left: sweepX - 300, width: 600,
                background: 'linear-gradient(90deg, rgba(255,252,240,0), rgba(255,252,240,1) 50%, rgba(255,252,240,0))',
                opacity: sweepOpacity,
              }}
            />
          </AbsoluteFill>
        ) : null}

        {stageLight > 0 ? (
          <AbsoluteFill
            style={{
              pointerEvents: 'none',
              background: 'radial-gradient(760px 400px at 960px 500px, rgba(255,253,245,0.5), rgba(255,240,255,0.16) 55%, rgba(255,240,255,0) 76%)',
              opacity: stageLight,
            }}
          />
        ) : null}

        {vignette > 0 ? (
          <AbsoluteFill
            style={{
              pointerEvents: 'none',
              background: 'radial-gradient(1400px 900px at 50% 50%, rgba(16,4,32,0) 52%, rgba(16,4,32,0.85) 100%)',
              opacity: vignette,
            }}
          />
        ) : null}

        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', pointerEvents: 'none' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: FONT, fontSize: 150, fontWeight: 700, letterSpacing: `${wordSpacing}em`, display: 'flex', lineHeight: 1 }}>
              {LETTERS.map((ch, i) => {
                const delay = Math.round(STAMP + i * 1.8);
                const t = interpolate(frame, [delay, delay + 8], [0, 1], {
                  extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.2, 0.75, 0.3, 1),
                });
                return (
                  <span
                    key={i}
                    style={{
                      opacity: t,
                      color: i < 4 ? '#ffffff' : LIME, // same accent token as the opening lockup
                      transform: `translateY(${(1 - t) * 28}px) scale(${1.35 - 0.35 * t})`,
                      filter: `blur(${(1 - t) * 8}px)`,
                      display: 'inline-block',
                      whiteSpace: 'pre',
                      textShadow: '0 12px 40px rgba(12,3,24,0.45)',
                    }}
                  >
                    {ch}
                  </span>
                );
              })}
            </div>
            <div style={{ position: 'relative', height: 6, width: 300, margin: '34px auto 0' }}>
              <div style={{ position: 'absolute', inset: 0, borderRadius: 3, background: `linear-gradient(90deg, ${LIME}, ${MAGENTA})`, transform: `scaleX(${rule})` }} />
              {ruleExt > 0 && ruleExtFade > 0 ? (
                <>
                  <div style={{ position: 'absolute', top: 2.5, height: 1, right: '100%', width: 190 * ruleExt, background: LIME, opacity: ruleExtFade }} />
                  <div style={{ position: 'absolute', top: 2.5, height: 1, left: '100%', width: 190 * ruleExt, background: LIME, opacity: ruleExtFade }} />
                </>
              ) : null}
            </div>
            <div
              style={{
                fontFamily: FONT, fontSize: 44, fontWeight: 500, color: '#ffffff',
                marginTop: 34, opacity: tag, letterSpacing: '-0.01em',
              }}
            >
              No queues. No forms. No branch hours.
            </div>
            <div
              style={{
                fontFamily: FONT, fontSize: 36, fontWeight: 500, color: LIME,
                marginTop: 30, opacity: legal, letterSpacing: '0.02em',
              }}
            >
              See every feature in EasyWay · eastwestbanker.com/easyway-app
            </div>
            <div
              style={{
                fontFamily: FONT, fontSize: 26, fontWeight: 300, color: 'rgba(255,255,255,0.78)',
                marginTop: 14, opacity: legal,
              }}
            >
              Unofficial concept film · not affiliated with EastWest Banking Corporation
            </div>
          </div>
        </AbsoluteFill>

      </AbsoluteFill>
    </AbsoluteFill>
  );
};
