// Shot 7 — `effects/scan-bracket-sweep`, extended into a lock → unlock interaction
// Reference implementation read before writing:
// demos/effects/scan-bracket-sweep/ScanBracketSweep.tsx. Kept from the card: the SUBJECT
// NEVER MOVES (its命门 — if the card also animates, the audience can't tell "being
// inspected" from "loading"), four L brackets drop on a 0.022 stagger converging 8 design-px
// inward, the sweep is 5 passes with inOutSine inside each pass and a 12% pause at the end
// of every pass, and the trailing gradient always hangs on the side the line came FROM
// (flipping top offset and gradient direction together — flipping one gives a tail that runs
// ahead of the light). The band is clipped inside a layer with the card's own radius so it
// reads as scanning THE CARD, not the screen.
// Geometry rescaled from the demo's 480×270 design space (its doc is 1200×712 output px;
// ours is ~605×372) so the trail, arm length and bracket weight keep the same proportion of
// the subject: trail 158px, arms 65px, border 4px, offset −12px. The band itself stays at 3px
// because the card's ceiling is absolute (">4px reads as a mask edge"), and the passes are
// inset 10px from the card's edges so the turn-around never degenerates into an edge glow.
// Beat-locked: one pass per beat (the light turns around on every kick), the lock snaps on
// b70 the instant the 5th pass finishes, and the unlock releases on b74.
import React from 'react';
import { AbsoluteFill, Easing, Img, interpolate, interpolateColors, staticFile, useCurrentFrame } from 'remotion';
import { PageCam, CamKey } from '../lib/PageCam';
import { SHOTS, beatF, localBeat, BEAT_INT, FPS } from '../beats';
import { FONT, INK, LIME, MAGENTA } from '../brand';
import layout from '../live-layout.json';

const PAGE_H = layout.cards.pageH;
const CARD = layout.cards.boxes.plastic; // 240,294,560,344
const CTLS = layout.cards.boxes.ctls;
const STATUS = layout.cards.boxes.status;
const RADIUS = 24;

const PASS_LEN = BEAT_INT * FPS; // 14.5167f — one sweep pass per beat
const SCAN_FROM = localBeat(SHOTS.lock, 65);
const LOCK_AT = localBeat(SHOTS.lock, 70); // 5 passes end exactly here
const UNLOCK_AT = localBeat(SHOTS.lock, 74);
const PASSES = 5;

const ARM = 65;
const BORDER = 4;
const OUT = 12;
const LINE_H = 3;
const TRAIL = 158;
const INSET = 10; // keep the pass extremes off the card's own edges

const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
const inOutSin = (x: number) => 0.5 - Math.cos(Math.PI * clamp01(x)) / 2;

const CAM: CamKey[] = [
  { frame: 0, cx: 960, cy: 820, zoom: 0.94, rotX: 10, rotY: 6, rotZ: 0, persp: 1400 },
  { frame: 12, cx: 930, cy: 740, zoom: 1.12, rotX: 4, rotY: 8, rotZ: 0, persp: 1400 },
  { frame: SHOTS.lock.duration, cx: 930, cy: 740, zoom: 1.12, rotX: 4, rotY: 8, rotZ: 0, persp: 1400 },
];

const CORNERS: { style: React.CSSProperties; dx: number; dy: number }[] = [
  { style: { left: -OUT, top: -OUT, borderLeft: `${BORDER}px solid ${LIME}`, borderTop: `${BORDER}px solid ${LIME}` }, dx: 1, dy: 1 },
  { style: { right: -OUT, top: -OUT, borderRight: `${BORDER}px solid ${LIME}`, borderTop: `${BORDER}px solid ${LIME}` }, dx: -1, dy: 1 },
  { style: { right: -OUT, bottom: -OUT, borderRight: `${BORDER}px solid ${LIME}`, borderBottom: `${BORDER}px solid ${LIME}` }, dx: -1, dy: -1 },
  { style: { left: -OUT, bottom: -OUT, borderLeft: `${BORDER}px solid ${LIME}`, borderBottom: `${BORDER}px solid ${LIME}` }, dx: 1, dy: -1 },
];

/** the switch pill drawn over the captured one, so it can actually flip */
const Switch: React.FC<{ y: number; on: number }> = ({ y, on }) => (
  <div
    style={{
      position: 'absolute', left: 1592, top: y + 26, width: 62, height: 34, borderRadius: 25,
      background: interpolateColors(on, [0, 1], ['#ded7e8', MAGENTA]),
    }}
  >
    <div
      style={{
        position: 'absolute', top: 4, left: 4 + 28 * on, width: 26, height: 26, borderRadius: 13,
        background: '#fff', boxShadow: '0 1px 3px rgba(42,15,71,0.25)',
      }}
    />
  </div>
);

export const SceneCardLock: React.FC = () => {
  const frame = useCurrentFrame();

  // brackets: 4 corners, 0.022-of-window stagger, each 0.055 long (scaled to frames)
  const bracketAt = (i: number) =>
    interpolate(frame, [6 + i * 3.3, 6 + i * 3.3 + 8], [0, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
    });

  // sweep: one pass per beat, inOutSine inside the pass, last 12% of each pass is a pause
  const scanEnd = SCAN_FROM + PASSES * PASS_LEN;
  const scanning = frame >= SCAN_FROM && frame <= scanEnd;
  const raw = (frame - SCAN_FROM) / PASS_LEN;
  const pi = Math.min(PASSES - 1, Math.max(0, Math.floor(raw)));
  const local = clamp01((raw - pi) / 0.88);
  const dir = pi % 2 === 0 ? 1 : -1;
  const prog = inOutSin(local);
  const span = CARD.h - INSET * 2;
  const y = INSET + (dir > 0 ? prog * span : span - prog * span);
  const bandOpacity =
    interpolate(frame, [SCAN_FROM, SCAN_FROM + 4], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) *
    interpolate(frame, [scanEnd - 6, scanEnd], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // lock / unlock state
  // the badge lands after the last switch falls — cause first, then the state read-out
  const locked = interpolate(frame, [LOCK_AT + 10, LOCK_AT + 14], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  }) * (1 - interpolate(frame, [UNLOCK_AT + 10, UNLOCK_AT + 14], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  }));
  const ringScale = interpolate(frame, [LOCK_AT + 10, LOCK_AT + 15, LOCK_AT + 19], [1.06, 0.995, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  // each of the three usage switches flips 4f after the previous one, both ways
  const switchOn = (i: number) => {
    const off = interpolate(frame, [LOCK_AT + i * 4, LOCK_AT + i * 4 + 5], [1, 0], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
    });
    const on = interpolate(frame, [UNLOCK_AT + i * 4, UNLOCK_AT + i * 4 + 5], [0, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
    });
    return frame < UNLOCK_AT + i * 4 ? off : on;
  };

  return (
    <AbsoluteFill>
    <PageCam src="textures/live/cards-full.png" pageH={PAGE_H} keys={CAM} ease={Easing.bezier(0.33, 0, 0.2, 1)}>
      {/* the card's own container: subject stays perfectly still, only light moves over it */}
      <div style={{ position: 'absolute', left: CARD.x, top: CARD.y, width: CARD.w, height: CARD.h }}>
        {/* 4x element capture laid out at CSS size — rasterises at the zoomed device size and
            samples down from the 2240px source, so the PAN and the fine card type stay crisp */}
        <Img
          src={staticFile('textures/live/plastic-hires.png')}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', borderRadius: RADIUS, display: 'block' }}
        />
        {/* scan band, clipped to the card's radius */}
        {scanning ? (
          <div
            style={{
              position: 'absolute', inset: 0, borderRadius: RADIUS, overflow: 'hidden',
              pointerEvents: 'none', opacity: bandOpacity, zIndex: 3,
            }}
          >
            <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 0, transform: `translateY(${y.toFixed(2)}px)` }}>
              <div
                style={{
                  position: 'absolute', left: 0, right: 0, height: TRAIL,
                  top: dir > 0 ? -TRAIL : LINE_H,
                  background:
                    dir > 0
                      ? 'linear-gradient(180deg, rgba(255,255,250,0), rgba(255,255,250,0.34))'
                      : 'linear-gradient(180deg, rgba(255,255,250,0.34), rgba(255,255,250,0))',
                }}
              />
              <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: LINE_H, background: LIME, boxShadow: `0 0 12px rgba(213,224,77,0.8)` }} />
            </div>
          </div>
        ) : null}

        {/* four framing brackets */}
        {CORNERS.map((c, i) => {
          const p = bracketAt(i);
          return (
            <div
              key={i}
              style={{
                position: 'absolute', width: ARM, height: ARM, boxSizing: 'content-box',
                opacity: p * (1 - locked),
                transform: `translate(${(1 - p) * 14 * c.dx}px, ${(1 - p) * 14 * c.dy}px)`,
                zIndex: 4,
                ...c.style,
              }}
            />
          );
        })}

        {/* locked state: purple scrim + lime ring on the card */}
        {locked > 0.01 ? (
          <>
            <div
              style={{
                position: 'absolute', inset: 0, borderRadius: RADIUS, background: 'rgba(42,15,71,0.42)',
                opacity: locked, zIndex: 2, pointerEvents: 'none',
              }}
            />
            <div
              style={{
                position: 'absolute', inset: -6, borderRadius: RADIUS + 6, border: `3px solid ${LIME}`,
                boxShadow: `0 0 0 2px rgba(24,6,48,0.45), 0 0 40px rgba(213,224,77,0.4)`,
                opacity: locked,
                transform: `scale(${ringScale})`, zIndex: 5, pointerEvents: 'none',
              }}
            />
          </>
        ) : null}
      </div>

      {/* LOCKED badge lands exactly over the card's baked "Status / Active" field */}
      {locked > 0.02 ? (
        <div
          style={{
            position: 'absolute', left: STATUS.x - 16, top: STATUS.y - 2, minWidth: STATUS.w + 44, height: 42,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 18px', borderRadius: 25,
            background: LIME, color: INK, fontFamily: FONT, fontSize: 16, fontWeight: 700,
            letterSpacing: '0.14em',
            transform: `scale(${0.92 + 0.08 * locked})`,
            transformOrigin: 'left center',
            boxShadow: '0 6px 18px rgba(24,6,48,0.45)',
            zIndex: 6,
          }}
        >
          LOCKED
        </div>
      ) : null}

      {/* the three usage switches flip off on the lock beat and back on when it is released */}
      {[0, 1, 2].map((i) => (
        <Switch key={i} y={CTLS[i].y} on={switchOn(i)} />
      ))}
    </PageCam>

    {/* Q11 allows text to be either "to be read" or "texture" — never a readable-looking
        middle state. The activity panel under the card is context, not copy, so it is
        DECLARED texture: a soft screen-space defocus band below the switches (the card and its
        controls stay sharp). PageCam's own dof is a TOP band — it blurs the far edge of a
        tilted page — which is the opposite of what this shot needs. */}
    <div
      style={{
        position: 'absolute', left: 0, right: 0, top: 500, bottom: 0,
        backdropFilter: 'blur(7px)', WebkitBackdropFilter: 'blur(7px)',
        background: 'rgba(247,245,250,0.28)',
        WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,0) 0px, rgba(0,0,0,1) 70px)',
        maskImage: 'linear-gradient(180deg, rgba(0,0,0,0) 0px, rgba(0,0,0,1) 70px)',
        pointerEvents: 'none',
      }}
    />
    </AbsoluteFill>
  );
};
