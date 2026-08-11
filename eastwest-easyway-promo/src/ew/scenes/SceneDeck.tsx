// Shot 3 — `ui-entrance/deck-deal-flyin`
// Reference implementation read before writing: template/src/aifl/live/SceneFlyIn.tsx.
// Kept from the card: the pile is a real stack (STACK_STEP 3px of physical height per card,
// deterministic ±8px / ±3° jitter from an index formula), a side-oblique orbit over a dark
// brushed-metal plane (4 layers: warm key pool + two 100deg anisotropic streak layers +
// 115deg steel sheen, on a 9000² plane so no angle can miss it), a段落-level anticipation
// beat before the first deal (stack presses down ~60% of its height + top card pulls back —
// amplitude has to clear the eye's threshold, 4px was rejected), the hard-accelerating deal
// cadence cue = 36 + 4k − 0.0792k(k−1) (4f gaps shrinking to 0.2f), per-card flight of 8f
// dive (z arc +90, scale peak 1.06) + 4f settle on bezier(0.3,0,0.25,1.15) + 2f press
// 0.996→1, ghost trail lagging 5% of the path at blur(6px), identity transform forced once
// landed, a chase-scroll that speeds up each leg, 0.6s of rest on the full board, and the
// drag hierarchy on the rest (shadows converge 3f behind the card bodies).
// Adapted: exactly the page's twelve real feature cards in their twelve real slots — no filler
// row. Two review rounds killed every variant of "reuse a few cutouts to lengthen the board":
// whatever the landed geometry, an extra card's FLIGHT path crosses the window that still holds
// its original, and two identical cards on screen reads as a bug (round 2, f0400/f0405). Twelve
// also matches what the page and the caption both claim. Our 464px cards are wider than the
// reference's 357px, so the orbit zoom is 1.95/1.82 instead of 1.95, and the chase tops out at
// ~27px/f in page space — inside the range that needs no motion-blur pass.
import { Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { PageCam, CamKey } from '../lib/PageCam';
import layout from '../live-layout.json';

const real = layout.app.boxes.cards;
const PAGE_H = layout.app.pageH; // 1974
const CARD_W = 464;
const CARD_H = 240;
const COLS = [240, 728, 1216];

const HOVER_H = 40;
const SETTLE_EASE = Easing.bezier(0.3, 0, 0.25, 1.15);
const DIVE_EASE = Easing.bezier(0.3, 0, 0.2, 1);

const PILE = { x: 1180, y: 300 };
const PILE_CX = PILE.x + CARD_W / 2;
const PILE_CY = PILE.y + CARD_H / 2;
const STACK_STEP = 4.5; // 12 cards → a 54px pile: the height has to be perceptible
const DEAL_START = 36;
const METAL_FADE = [34, 56] as const;

const N_CARDS = real.length; // 12

const grid = real
  .map((c, i) => ({ file: `card${i + 1}.png`, x: c.x, y: c.y, w: c.w, h: c.h }))
  .sort((a, b) => a.y - b.y || a.x - b.x)
  .map((c, k) => ({
    ...c,
    // same hard-acceleration shape as the reference (4.5f gaps collapsing to 2.0f over 15 cards)
    cue: DEAL_START + 5.5 * k - 0.16 * k * (k - 1), // gaps 5.5f → 2.0f over twelve cards
    px: PILE.x + (((k * 7) % 9) - 4) * 2,
    py: PILE.y + (((k * 5) % 7) - 3) * 2,
    protZ: ((k * 11) % 7) - 3,
    pz: (N_CARDS - k) * STACK_STEP,
  }));

const CAM_KEYS: CamKey[] = [
  { frame: 0, cx: PILE_CX + 40, cy: PILE_CY + 70, zoom: 1.95, rotX: 46, rotY: -30, rotZ: 9, persp: 1100 },
  { frame: 34, cx: PILE_CX + 90, cy: PILE_CY + 50, zoom: 1.82, rotX: 42, rotY: 26, rotZ: -7, persp: 1100 },
  { frame: 62, cx: 960, cy: 560, zoom: 0.95, rotX: 26, rotY: 0, rotZ: 2, persp: 1300 },
  { frame: 88, cx: 950, cy: 980, zoom: 0.95, rotX: 14, rotY: 0, rotZ: 0, persp: 1300 }, // 16px/f
  { frame: 104, cx: 960, cy: 1406, zoom: 0.95, rotX: 0, rotY: 0, rotZ: 0, persp: 1300 }, // 27px/f — accelerating
  { frame: 122, cx: 960, cy: 1406, zoom: 0.95, rotX: 0, rotY: 0, rotZ: 0, persp: 1300 }, // 0.6s rest
  { frame: 146, cx: 960, cy: 960, zoom: 1.15, rotX: 8, rotY: 0, rotZ: 0, persp: 1300 },
  { frame: 203, cx: 960, cy: 1290, zoom: 1.15, rotX: 2, rotY: 0, rotZ: 0, persp: 1300 },
];

export const SceneDeck: React.FC = () => {
  const frame = useCurrentFrame();
  const dofStrength = interpolate(frame, [86, 104], [5, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // anticipation (段落-level, once — never per card): the stack presses down ~60% of its
  // height and the top card pulls back against the deal direction, released on the first cue
  const dip = interpolate(frame, [22, 34], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad),
  }) * (frame < DEAL_START ? 1 : 0);

  return (
    <PageCam
      src="textures/live/app-empty.png"
      pageH={PAGE_H}
      keys={CAM_KEYS}
      ease={Easing.bezier(0.33, 0, 0.15, 1)}
      dof={dofStrength > 0.1 ? { focusY: 260, strength: dofStrength } : undefined}
    >
      {/* dark brushed-metal table for the opening pile close-up */}
      {frame < METAL_FADE[1] ? (
        <div
          style={{
            position: 'absolute', left: -3000, top: -3000, width: 9000, height: 9000,
            opacity: interpolate(frame, [METAL_FADE[0], METAL_FADE[1]], [1, 0], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
            }),
            background: [
              `radial-gradient(1300px 900px at ${3000 + PILE_CX}px ${3000 + PILE_CY}px, rgba(213,224,77,0.16), rgba(178,0,111,0.08) 40%, transparent 68%)`,
              'repeating-linear-gradient(100deg, rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 2px, rgba(0,0,0,0.13) 3px, rgba(0,0,0,0.13) 6px, transparent 7px, transparent 18px)',
              'linear-gradient(115deg, #26202e 0%, #362c42 28%, #1e1926 55%, #2f2740 78%, #191320 100%)',
            ].join(', '),
            pointerEvents: 'none',
          }}
        />
      ) : null}

      {grid.map((c, i) => {
        const { cue } = c;
        const radius = 24;
        const diveT = interpolate(frame, [cue, cue + 8], [0, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: DIVE_EASE,
        });
        const settleT = interpolate(frame, [cue + 8, cue + 12], [0, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: SETTLE_EASE,
        });
        // drag hierarchy: the shadow converges 3 frames behind the body (rest段 head only)
        const settleLag = interpolate(frame - 3, [cue + 8, cue + 12], [0, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: SETTLE_EASE,
        });

        const dx = (c.px - c.x) * (1 - diveT);
        const dy = (c.py - c.y) * (1 - diveT);
        const rotFlight = c.protZ * (1 - diveT);
        const arc = Math.sin(diveT * Math.PI) * 90;
        const zDive = interpolate(diveT, [0, 1], [c.pz, HOVER_H]) + arc;
        const z = frame < cue ? c.pz : zDive * (1 - settleT);
        const dealScale = 1 + Math.sin(diveT * Math.PI) * 0.06;
        const press = interpolate(frame, [cue + 10, cue + 11, cue + 12], [1, 0.996, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
        });
        const scale = dealScale * press;

        const landed = frame >= cue + 12;
        const inPile = frame < cue;
        const pileDip = dip * (i === 0 ? 43 : 43 * 0.85);
        const pilePull = i === 0 ? dip * 30 : 0;
        const transform = landed
          ? 'translate3d(0px, 0px, 0px)'
          : inPile
            ? `translate3d(${c.px - c.x + pilePull}px, ${c.py - c.y + pileDip}px, ${c.pz * (1 - 0.45 * dip)}px) rotateZ(${c.protZ}deg)`
            : `translate3d(${dx}px, ${dy}px, ${z}px) rotateZ(${rotFlight}deg) scale(${scale})`;

        const shadow = landed
          ? '0 2px 10px rgba(84,39,133,.07)'
          : inPile
            ? '0 1px 3px rgba(30,16,48,.2)'
            : `0 ${36 - 30 * settleLag}px ${70 - 60 * settleLag}px rgba(42,15,71,${0.3 - 0.22 * settleLag})`;

        const showGhost = diveT > 0.02 && diveT < 0.98;

        return (
          <div key={`${c.file}-${i}`} style={{ transformStyle: 'preserve-3d' }}>
            {showGhost ? (
              <div
                style={{
                  position: 'absolute', left: c.x, top: c.y, width: c.w, height: c.h,
                  transform: `translate3d(${dx + (c.px - c.x) * 0.05}px, ${dy + (c.py - c.y) * 0.05}px, ${z}px) rotateZ(${rotFlight}deg) scale(${scale})`,
                  transformOrigin: 'center center',
                  opacity: 0.25 * (1 - diveT),
                  filter: 'blur(6px)',
                  borderRadius: radius,
                  overflow: 'hidden',
                  pointerEvents: 'none',
                }}
              >
                <Img src={staticFile(`textures/live/${c.file}`)} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', display: 'block' }} />
              </div>
            ) : null}

            <div
              style={{
                position: 'absolute', left: c.x, top: c.y, width: c.w, height: c.h,
                transform,
                transformOrigin: 'center center',
                boxShadow: shadow,
                borderRadius: radius,
                overflow: 'hidden',
              }}
            >
              <Img src={staticFile(`textures/live/${c.file}`)} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', display: 'block' }} />
            </div>
          </div>
        );
      })}
    </PageCam>
  );
};
