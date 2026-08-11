// Shot 4 — `ui-entrance/row-embed`
// Reference implementation read before writing: template/src/aifl/live/SceneDetail.tsx.
// Kept from the card: rows drop on a 9f cadence with a 12f flight,
// `perspective(900px) translateY(-120·air) rotateX(16°·air)` so they flatten out as they
// seat (a pure vertical drop reads as a sticker), scale 1.06→0.995 then a 4f press back to
// 1, an accent seam 2px tall spreading from the centre of the row's BOTTOM edge over 5f and
// fading over 8f (clipped inside the row's own radius — Q4), and a camera that pans down
// through the whole row-rain instead of waiting for it.
// Adapted: the page texture is the empty plate and the flyers are real row cutouts, so no
// slot patch is needed at all; the last row lands exactly on beat 40 (a top-8 kick), where a
// single lime bloom marks the two free transfers.
import React from 'react';
import { Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { PageCam, CamKey } from '../lib/PageCam';
import { LIME } from '../brand';
import layout from '../live-layout.json';

const PAGE_H = layout.transfers.pageH; // 1291
const rows = layout.transfers.boxes.rows;
const FLY_EASE = Easing.bezier(0.3, 0, 0.25, 1);

const CAM: CamKey[] = [
  { frame: 0, cx: 960, cy: 480, zoom: 1.0, rotX: 12, rotY: 0, rotZ: 0, persp: 1400 },
  { frame: 75, cx: 960, cy: 751, zoom: 1.0, rotX: 4, rotY: 0, rotZ: 0, persp: 1400 },
  { frame: 110, cx: 960, cy: 751, zoom: 1.0, rotX: 4, rotY: 0, rotZ: 0, persp: 1400 },
  { frame: 140, cx: 960, cy: 700, zoom: 1.3, rotX: 0, rotY: 0, rotZ: 0, persp: 1400 },
  { frame: 174, cx: 960, cy: 700, zoom: 1.3, rotX: 0, rotY: 0, rotZ: 0, persp: 1400 },
];

const BEAT40 = 58; // localBeat(SHOTS.transfers, 40) — verified by tools/check-timeline.mjs

export const SceneTransfers: React.FC = () => {
  const frame = useCurrentFrame();

  // everything locking in on the beat: one 2f press on the panel + one lime bloom over the
  // two fee-free rows (one light effect for the shot, on the protagonist — Q4)
  const press = interpolate(frame, [BEAT40, BEAT40 + 2, BEAT40 + 5], [1, 0.997, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const bloom = interpolate(frame, [BEAT40, BEAT40 + 4, BEAT40 + 16], [0, 0.5, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <PageCam src="textures/live/transfers-empty.png" pageH={PAGE_H} keys={CAM} ease={Easing.bezier(0.33, 0, 0.15, 1)}>
      <div style={{ transformStyle: 'preserve-3d' }}>
        {rows.map((r, i) => {
          const cue = 10 + i * 9;
          const land = cue + 12;
          if (frame < cue) return null;

          const p = interpolate(frame, [cue, cue + 12], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: FLY_EASE,
          });
          const appear = interpolate(frame, [cue, cue + 3], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const scale =
            frame < land
              ? 1.06 - 0.065 * p
              : interpolate(frame, [land, land + 4], [0.995, 1], {
                  extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad),
                });
          const air = 1 - p;

          const seamOn = frame >= land && frame < land + 8;
          const spread = interpolate(frame, [land, land + 5], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
          });
          const seamOpacity = interpolate(frame, [land, land + 2, land + 8], [1, 1, 0], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
          });

          return (
            <div
              key={i}
              style={{
                position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h,
                borderRadius: 16, overflow: 'hidden', backgroundColor: '#fff',
                opacity: appear,
                transform: `perspective(900px) translateY(${-120 * air}px) rotateX(${16 * air}deg) scale(${scale * press})`,
                boxShadow: `0 ${30 * air}px ${60 * air}px rgba(42,15,71,${0.2 * air}), 0 ${8 * air}px ${16 * air}px rgba(42,15,71,${0.1 * air})`,
                pointerEvents: 'none',
              }}
            >
              <Img
                src={staticFile(`textures/live/row${i + 1}.png`)}
                style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', display: 'block' }}
              />
              {seamOn ? (
                <div
                  style={{
                    position: 'absolute', left: (r.w * (1 - spread)) / 2, bottom: 0,
                    width: r.w * spread, height: 2, background: LIME,
                    boxShadow: `0 0 6px rgba(213,224,77,0.6)`, opacity: seamOpacity,
                  }}
                />
              ) : null}
            </div>
          );
        })}

        {bloom > 0.01 ? (
          <div
            style={{
              position: 'absolute', left: 1180, top: 590, width: 520, height: 300,
              background: `radial-gradient(closest-side, rgba(213,224,77,0.85), rgba(213,224,77,0) 70%)`,
              opacity: bloom, mixBlendMode: 'multiply', pointerEvents: 'none',
            }}
          />
        ) : null}
      </div>
    </PageCam>
  );
};
