// origin: template/src/aifl/FlashCut.tsx（模板片同源组件）
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

/** Bright-field cut: a bloom that flashes over the hard cut (video-shotcraft assets/lib). */
export const FlashCut: React.FC<{ duration?: number }> = ({ duration = 10 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, duration * 0.4, duration], [0, 0.7, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        opacity: o,
        // brand-neutral bloom with a faint lime core instead of the template's amber
        background: 'radial-gradient(ellipse at 50% 45%, rgba(255,255,252,0.98), rgba(248,250,232,0.5) 55%, transparent 80%)',
      }}
    />
  );
};
