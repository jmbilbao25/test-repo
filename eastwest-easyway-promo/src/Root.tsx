import { Composition } from 'remotion';
import { EastWestPromo } from './ew/Main';
import { TOTAL, FPS } from './ew/beats';

export const Root: React.FC = () => {
  return (
    <Composition
      id="EastWestPromo"
      component={EastWestPromo}
      durationInFrames={TOTAL}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={{ bgm: true }}
    />
  );
};
