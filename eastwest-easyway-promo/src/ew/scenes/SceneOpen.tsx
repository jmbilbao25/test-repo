// Shot 1 — brand open + `opening/spotlight-hero-card`
// Reference implementation read before writing: template/src/aifl/live/SceneOpen.tsx.
// Kept from the card (parameters that are the tuned truth): 4 roving spotlight waypoints
// then lock with a +6% pool pulse, pool 620→420→360, vignette .16→.34→.42, 16f push-in to a
// rotY-dominant LEFT-side view (rotY 34 / rotX 8 / persp 1200), rise 10f on
// bezier(0.2,1.25,0.3,1) → 54f hover with a 4px sin bob on a 40f period → 18f reseat with a
// 0.997 press, two perimeter beam laps (fast+bright, then slow+weak), altitude-driven
// two-layer shadow, 4x hero texture crossfading in over the 2x page.
// Re-skinned to EastWest: lime beam/slot instead of amber, purple stage for the lockup,
// and the camera is pinned truly static after touchdown (R1 — no 2.6→2.58 tail drift).
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { PageCam, CamKey } from '../lib/PageCam';
import { SHOTS } from '../beats';
import { CANVAS, FONT, LIME, LINE, MAGENTA, PURPLE, PURPLE_DEEP } from '../brand';
import layout from '../live-layout.json';

const PAGE_H = layout.app.pageH;
const CARD = layout.app.boxes.hero;
const MCX = CARD.x + CARD.w / 2; // 960 — page centre, so the push-in stays framed
const MCY = CARD.y + CARD.h / 2; // 444
const RADIUS = 24;

const WORDMARK = 'EastWest';
const KICKER = 'EASYWAY · DIGITAL BANKING';

const CAM_KEYS: CamKey[] = [
  { frame: 82, cx: 960, cy: 640, zoom: 0.78, rotX: 0, rotY: 0, rotZ: 0, persp: 1200 },
  { frame: 114, cx: 960, cy: 640, zoom: 0.78, rotX: 0, rotY: 0, rotZ: 0, persp: 1200 },
  { frame: 130, cx: MCX - 30, cy: MCY + 26, zoom: 1.9, rotX: 8, rotY: 34, rotZ: 2, persp: 1200 },
  { frame: 232, cx: MCX - 30, cy: MCY + 26, zoom: 1.9, rotX: 8, rotY: 34, rotZ: 2, persp: 1200 },
];
const PUSH_EASE = Easing.bezier(0.35, 0, 0.2, 1);
const POP_EASE = Easing.bezier(0.2, 1.25, 0.3, 1);
const RESEAT_EASE = Easing.bezier(0.4, 0, 0.3, 1.05);
const BEAM_CORE = 'rgba(255,255,250,0.98)';

export const SceneOpen: React.FC = () => {
  const frame = useCurrentFrame();

  // --- brand lockup: glyph letterpress (10 + i*3), kicker typewriter, 1s rest, dissolve ---
  const perChar = 0.7;
  const kickStart = 28;
  const kickChars = Math.floor(Math.max(0, frame - kickStart) / perChar);
  const kickDone = kickStart + KICKER.length * perChar;
  // the caret is solid while typing and then gone: a blinking caret would break the
  // wordmark's 30-frame hold every other frame (R1)
  const cursorOn = frame >= kickStart && frame < kickDone;
  const brandOut = interpolate(frame, [76, 83], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.4, 0, 0.5, 1),
  });
  const brandOpacity = 1 - brandOut;

  // starts before the lockup has fully dissolved so no single frame is an empty canvas
  const macroIn = interpolate(frame, [78, 88], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.3, 0, 0.2, 1),
  });

  // --- roving spotlight (screen space). The hero card sits at (50%, 36%) in the
  // straight-on view (cy 640, zoom .78), which is where the light locks. ---
  const spotEase = Easing.bezier(0.4, 0, 0.3, 1);
  const spotX = interpolate(frame, [86, 90, 98, 104, 110, 130], [24, 24, 72, 40, 50, 50], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: spotEase,
  });
  const spotY = interpolate(frame, [86, 90, 98, 104, 110, 130], [64, 64, 52, 24, 36, 44], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: spotEase,
  });
  const spotOn = interpolate(frame, [84, 92], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const poolBase = interpolate(frame, [104, 114, 130], [620, 420, 360], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.3, 1),
  });
  const poolPulse = interpolate(frame, [114, 118, 123], [0, 0.06, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const poolRx = poolBase * (1 + poolPulse);
  const poolRy = poolBase * 0.8 * (1 + poolPulse);
  const vignette = interpolate(frame, [104, 114, 130], [0.16, 0.34, 0.42], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const dofStrength = interpolate(frame, [114, 130, 140, 150], [0, 9, 9, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // --- hero card action arc: lock(114) → touchdown(212) ≈ 98f ≈ 3.3s (R3) ---
  const rise = interpolate(frame, [130, 140], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: POP_EASE,
  });
  const reseat = interpolate(frame, [194, 212], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: RESEAT_EASE,
  });
  const lift = rise * (1 - reseat);
  const bob = Math.sin(((frame - 140) / 40) * Math.PI * 2) * 4 * lift;
  const z = 110 * lift + bob;
  const landed = frame >= 212;
  const press = interpolate(frame, [208, 211, 212], [1, 0.997, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const shadow = `0 ${8 * lift}px ${10 + 12 * lift}px rgba(42,15,71,${0.18 * lift}), 0 ${46 * lift}px ${90 * lift}px rgba(42,15,71,${0.22 * lift})`;

  const slotVis = Math.min(1, rise * 2) * (1 - reseat);
  const landPulse = interpolate(frame, [208, 212, 216], [0, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const slotEdge = Math.min(1, 0.4 * (1 - reseat)) + landPulse * 0.6;

  const beam1Prog = interpolate(frame, [142, 156], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.linear,
  });
  const beam1On = frame >= 141 && frame <= 157;
  const beam2Prog = interpolate(frame, [162, 182], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.4, 1),
  });
  const beam2On = frame >= 161 && frame <= 183;
  const beamTrail = interpolate(frame, [182, 194], [0.35, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const bw = CARD.w + 6;
  const bh = CARD.h + 6;

  const hiresIn = interpolate(frame, [114, 120], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ backgroundColor: CANVAS }}>
      {frame >= 76 ? (
        <AbsoluteFill style={{ opacity: macroIn }}>
          <PageCam
            src="textures/live/app-full.png"
            pageH={PAGE_H}
            keys={CAM_KEYS}
            ease={PUSH_EASE}
            dof={{ focusY: 240, strength: dofStrength }}
          >
            {/* rim light along the near (bottom) edge of the tilted plane */}
            <div
              style={{
                position: 'absolute', left: 0, right: 0, bottom: 0, height: 8,
                background: 'rgba(255,255,255,0.85)', filter: 'blur(6px)',
                opacity: 0.6 * Math.min(1, lift + Math.max(0, (frame - 114) / 16)),
                pointerEvents: 'none',
              }}
            />

            <div style={{ transformStyle: 'preserve-3d' }}>
              {/* vacated slot: page-coloured patch + breathing lime outline while airborne */}
              {slotVis > 0.02 ? (
                <div
                  style={{
                    position: 'absolute', left: CARD.x - 2, top: CARD.y - 2,
                    width: CARD.w + 4, height: CARD.h + 4, background: CANVAS,
                    borderRadius: RADIUS,
                    boxShadow: `inset 0 0 26px rgba(178,0,111,${0.1 * slotEdge})`,
                    opacity: slotVis,
                  }}
                >
                  <div
                    style={{
                      position: 'absolute', inset: 0, borderRadius: RADIUS,
                      border: `1.5px solid ${LIME}`, opacity: slotEdge, pointerEvents: 'none',
                    }}
                  />
                </div>
              ) : null}

              {/* the levitating hero card */}
              <div
                style={{
                  position: 'absolute', left: CARD.x, top: CARD.y, width: CARD.w, height: CARD.h,
                  transform: `translateZ(${z}px) scale(${press})`,
                  transformOrigin: 'center center',
                  transformStyle: 'preserve-3d',
                }}
              >
                <div
                  style={{
                    position: 'absolute', inset: 0, borderRadius: RADIUS, overflow: 'hidden',
                    boxShadow: landed ? '0 18px 40px rgba(84,39,133,0.22)' : shadow,
                  }}
                >
                  <Img
                    src={staticFile('textures/live/hero-card.png')}
                    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', display: 'block' }}
                  />
                  {/* 4x element capture laid out at CSS size: PageCam applies the push-in as a
                      layout-scale CSS `zoom`, so this rasterizes at its enlarged device size and
                      samples DOWN from the 2880px source — sharp glyphs under perspective (Q2). */}
                  <Img
                    src={staticFile('textures/live/hero-card-hires.png')}
                    style={{
                      position: 'absolute', inset: 0, width: '100%', height: '100%',
                      display: 'block', opacity: hiresIn,
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute', inset: 0,
                      background: 'linear-gradient(160deg, rgba(255,255,255,0.34), transparent 42%)',
                      opacity: lift, pointerEvents: 'none',
                    }}
                  />
                </div>
                <div
                  style={{
                    position: 'absolute', inset: 0, borderRadius: RADIUS,
                    boxShadow: `inset 0 0 0 1px rgba(255,255,255,${0.7 * lift})`, pointerEvents: 'none',
                  }}
                />

                {/* perimeter beam: lap 1 fast + bright, lap 2 slow + weaker (one sustained scan) */}
                {(beam1On || beam2On) && lift > 0.4 ? (
                  <svg
                    width={bw}
                    height={bh}
                    viewBox={`0 0 ${bw} ${bh}`}
                    style={{
                      position: 'absolute', left: -3, top: -3, overflow: 'visible', pointerEvents: 'none',
                      opacity: beam1On ? 1 : 0.62,
                      filter: `drop-shadow(0 0 6px ${LIME}) drop-shadow(0 0 18px rgba(213,224,77,0.5))`,
                    }}
                  >
                    <rect
                      x={2} y={2} width={bw - 4} height={bh - 4} rx={RADIUS} fill="none"
                      stroke={LIME} strokeWidth={beam1On ? 5 : 3.5} strokeLinecap="round"
                      pathLength={1} strokeDasharray="0.14 1"
                      strokeDashoffset={-(beam1On ? beam1Prog : beam2Prog)}
                    />
                    <rect
                      x={2} y={2} width={bw - 4} height={bh - 4} rx={RADIUS} fill="none"
                      stroke={BEAM_CORE} strokeWidth={beam1On ? 2.5 : 1.75} strokeLinecap="round"
                      pathLength={1} strokeDasharray="0.14 1"
                      strokeDashoffset={-(beam1On ? beam1Prog : beam2Prog)}
                    />
                  </svg>
                ) : null}

                {beamTrail > 0.01 ? (
                  <div
                    style={{
                      position: 'absolute', inset: -3, borderRadius: RADIUS + 3,
                      border: `1.5px solid ${LIME}`, opacity: beamTrail, pointerEvents: 'none',
                    }}
                  />
                ) : null}
              </div>
            </div>
          </PageCam>

          {/* roving / locking spotlight: warm-neutral pool + purple dim outside */}
          <AbsoluteFill
            style={{
              background: `radial-gradient(${poolRx}px ${poolRy}px at ${spotX}% ${spotY}%, rgba(255,252,240,0.40), rgba(255,250,235,0.10) 45%, rgba(42,15,71,${vignette * spotOn}) 100%)`,
              pointerEvents: 'none',
              opacity: spotOn,
            }}
          />
          <AbsoluteFill
            style={{
              background: `radial-gradient(300px 220px at ${spotX - 6}% ${spotY + 10}%, rgba(213,224,77,0.10), transparent 70%)`,
              pointerEvents: 'none',
              opacity: spotOn * 0.7,
            }}
          />
        </AbsoluteFill>
      ) : null}

      {/* ---- brand lockup on a purple stage ---- */}
      {brandOpacity > 0 ? (
        <AbsoluteFill
          style={{
            background: `radial-gradient(1200px 700px at 50% 44%, ${PURPLE} 0%, ${PURPLE_DEEP} 62%, #1d0834 100%)`,
            justifyContent: 'center', alignItems: 'center', pointerEvents: 'none',
            opacity: brandOpacity,
          }}
        >
          <div
            style={{
              textAlign: 'center',
              transform: `translateY(${-brandOut * 40}px) scale(${1 - brandOut * 0.12})`,
              transformOrigin: 'center center',
            }}
          >
            <div
              style={{
                fontFamily: FONT, fontSize: 150, fontWeight: 700, letterSpacing: '-0.03em',
                lineHeight: 1, whiteSpace: 'pre', display: 'inline-flex', alignItems: 'flex-end',
              }}
            >
              {WORDMARK.split('').map((ch, i) => {
                const delay = 10 + i * 3;
                const t = interpolate(frame, [delay, delay + 12], [0, 1], {
                  extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
                  easing: Easing.bezier(0.2, 0.7, 0.25, 1),
                });
                return (
                  <span
                    key={i}
                    style={{
                      position: 'relative', display: 'inline-block', opacity: t,
                      color: i < 4 ? '#ffffff' : LIME,
                      transform: `scale(${1.6 - 0.6 * t})`,
                      transformOrigin: 'center bottom',
                      filter: `blur(${(1 - t) * 6}px)`,
                    }}
                  >
                    {ch}
                  </span>
                );
              })}
            </div>

            <div
              style={{
                fontFamily: FONT, fontSize: 34, fontWeight: 400, letterSpacing: '0.22em',
                color: 'rgba(255,255,255,0.78)', marginTop: 34, height: 32,
                display: 'flex', justifyContent: 'center', alignItems: 'center',
              }}
            >
              <span style={{ whiteSpace: 'pre' }}>{KICKER.slice(0, kickChars)}</span>
              <span
                style={{
                  display: 'inline-block', width: 14, height: 26, marginLeft: 6,
                  background: LIME, opacity: cursorOn ? 0.9 : 0,
                }}
              />
            </div>
            <div
              style={{
                width: 260, height: 4, borderRadius: 2, background: `linear-gradient(90deg, ${LIME}, ${MAGENTA})`,
                margin: '38px auto 0',
                transform: `scaleX(${interpolate(frame, [40, 52], [0, 1], {
                  extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.3, 0, 0.2, 1),
                })})`,
                borderTop: `0px solid ${LINE}`,
              }}
            />
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
