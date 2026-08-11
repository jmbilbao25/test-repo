// Shot 6 — `ui-entrance/list-reveal`
// Reference implementation read before writing: the card's参考实现
// demos/ui-entrance/list-reveal/ListReveal.tsx (parameters below are its tuned truth).
// Kept from the card: two completely decoupled layers — every item runs its own local window
// `seg(t, 0.06 + i*0.09, +0.24)` (10f stagger = the "you can read each one" interval, item
// travel 0.24 ≈ 2.6× the stagger so three items are always in motion at once), scale-led
// find-position 0.78→1 with only 14px of travel, a barely-readable overshoot, opacity
// min(1, p*2.2) so nothing lingers half-transparent, and a container drift whose magnitude
// (32px over the whole shot) stays 2× away from the per-item travel so they read as two
// layers rather than one.
// Adapted (the card's known pitfall "the drift never returns"): the drift eases to a full
// stop at t=0.8 so the shot can hold truly still afterwards (R1).
import { Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { PageCam, CamKey } from '../lib/PageCam';
import layout from '../live-layout.json';

const PAGE_H = layout.bills.pageH; // 1080
const billers = layout.bills.boxes.billers;
const WINDOW = 116; // frames the reveal spans; the shot holds still afterwards
const OUT_BACK = Easing.bezier(0.34, 1.06, 0.64, 1);

// the camera is deliberately a single static key: the drifting container is the layer that
// keeps the frame alive here (the card's whole point)
const CAM: CamKey[] = [{ frame: 0, cx: 960, cy: 540, zoom: 1.0, rotX: 6, rotY: 0, rotZ: 0, persp: 1500 }];

export const SceneBills: React.FC = () => {
  const frame = useCurrentFrame();
  const t = Math.min(1, frame / WINDOW);
  const driftT = interpolate(t, [0, 0.8], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad),
  });
  const drift = 16 - 32 * driftT;

  return (
    <PageCam src="textures/live/bills-empty.png" pageH={PAGE_H} keys={CAM}>
      <div style={{ transform: `translateY(${drift}px)`, transformStyle: 'preserve-3d' }}>
        {billers.map((b, i) => {
          const start = 0.06 + i * 0.09;
          const p = interpolate(t, [start, start + 0.24], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: OUT_BACK,
          });
          if (p <= 0) return null;
          return (
            <div
              key={i}
              style={{
                position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h,
                borderRadius: 16, overflow: 'hidden',
                opacity: Math.min(1, p * 2.2),
                transform: `translateY(${14 * (1 - p)}px) scale(${0.78 + p * 0.22})`,
                transformOrigin: 'center center',
                boxShadow: `0 ${12 * (1 - p)}px ${26 * (1 - p)}px rgba(42,15,71,${0.14 * (1 - p)})`,
                pointerEvents: 'none',
              }}
            >
              <Img
                src={staticFile(`textures/live/biller${i + 1}.png`)}
                style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', display: 'block' }}
              />
            </div>
          );
        })}
      </div>
    </PageCam>
  );
};
