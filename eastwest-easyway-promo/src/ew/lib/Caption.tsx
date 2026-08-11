// Narration caption — video-shotcraft assets/lib/Caption.tsx, re-skinned to the EastWest
// tokens and raised to 56px (Q11's subtitle floor: ≥56px / ≥5.2% of frame height, measured
// on the rendered frame). It rides in a white pill with the brand's 25px radius so it stays
// legible over the light page textures (Q11's scrim requirement), led by a lime dot.
import { interpolate, useCurrentFrame } from 'remotion';
import { FONT, INK, LIME, LINE } from '../brand';

export const Caption: React.FC<{ text: string; duration: number; bottom?: number }> = ({
  text,
  duration,
  bottom = 64,
}) => {
  const frame = useCurrentFrame();
  const inT = interpolate(frame, [0, 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const outT = interpolate(frame, [duration - 8, duration], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
        opacity: inT * outT,
        transform: `translateY(${(1 - inT) * 10}px)`,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 20,
          background: 'rgba(255,255,255,0.93)',
          border: `1px solid ${LINE}`,
          borderRadius: 25,
          padding: '16px 40px',
          boxShadow: '0 10px 30px rgba(84,39,133,0.14)',
        }}
      >
        <span style={{ width: 14, height: 14, borderRadius: 7, background: LIME, display: 'inline-block' }} />
        <span style={{ fontFamily: FONT, fontSize: 56, fontWeight: 500, color: INK, letterSpacing: '-0.01em' }}>
          {text}
        </span>
      </div>
    </div>
  );
};
