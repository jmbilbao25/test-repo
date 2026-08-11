// EastWest EasyWay — 2.5D feature promo. 1495f / 49.83s @ 30fps, 1920×1080.
// Timeline, captions and the whole sound design live in this one file: sound is a
// timeline-level asset, never a shot-level one (video-shotcraft references/sound-design.md).
// Every cue below is written as SHOTS.<shot>.from + offset or beatF(n) — never a bare frame
// number — so re-timing one shot cannot desync the rest of the table (S2 / §4.5).
import { AbsoluteFill, Audio, Sequence, staticFile, interpolate, useCurrentFrame } from 'remotion';
import { loadFont } from '@remotion/google-fonts/Poppins';
import { SHOTS, TOTAL, beatF, localBeat } from './beats';
import { CANVAS } from './brand';
import { Caption } from './lib/Caption';
import { FlashCut } from './lib/FlashCut';
import { SceneOpen } from './scenes/SceneOpen';
import { TitleSweep, TitleMarker } from './scenes/Titles';
import { SceneDeck } from './scenes/SceneDeck';
import { SceneTransfers } from './scenes/SceneTransfers';
import { SceneBills } from './scenes/SceneBills';
import { SceneCardLock } from './scenes/SceneCardLock';
import { SceneRewards, LOCK_BEATS } from './scenes/SceneRewards';
import { StepWipe, STEPS as WIPE_STEPS, BADGE_STEPS as WIPE_BADGE } from './scenes/StepWipe';
import { SceneOutro } from './scenes/SceneOutro';

loadFont('normal', { weights: ['300', '400', '500', '600', '700', '800'], subsets: ['latin'] });

// narration: short lines so they can sit at Q11's 56px subtitle floor and still fit the frame
const CAPTIONS = [
  { from: SHOTS.open.from + 96, duration: 62, text: 'One app for everything you bank' },
  { from: SHOTS.deck.from + 96, duration: 50, text: 'Twelve things you used to queue for' },
  { from: SHOTS.deck.from + 152, duration: 48, text: 'QR InstaPay · Loans · Installments' },
  // Every caption starts AFTER the last element of its shot has landed, measured against the
  // scene's own cue table — the pill must never cover something the audience still has to see
  // arrive (the first two attempts at this moved the collision instead of removing it).
  { from: SHOTS.transfers.from + 117, duration: 55, text: 'Free to EastWest & KOMO, 24/7' },
  { from: SHOTS.bills.from + 92, duration: 50, text: 'Due dates and amounts, pre-filled' },
  { from: SHOTS.lock.from + 20, duration: 62, text: 'Lock ATM, online and in-store' },
  { from: SHOTS.lock.from + 100, duration: 56, text: 'Switch it back on anytime' },
  { from: SHOTS.rewards.from + 18, duration: 74, text: 'Cash rewards on card spend' },
] as const;

// Beat-pinned sound design. Film vocabulary only (whoosh / impact / riser / sparkle /
// transition) plus real-object foley for the switches, the marker and the scanner; no
// synthesised UI tones (S1). Volumes are set against each sample's measured peak — all of
// these sit within 2dB of 0dBFS except sparkle (−6.7dB), which is why it gets 0.5.
// Percussive cues are pinned by their INTERNAL PEAK, not their file head
// (music-beat-sync §4: `start = target beat − (peak − trim)`). Measured peaks:
// impact-deep-whoosh 632ms (19f), impact-zoom-quick 517ms (15.5f — too laggy for a hard
// step, replaced), bass-hit-short 85ms (2.6f), transition-snap 115ms (3.4f), pop 37ms (1.1f),
// lock-quick 16ms, switch-click-quick 7ms (both effectively instant).
// data-scan peaks 123ms in (3.7f); riser-cine peaks at 35f, which is exactly why the
// template's finale phrase puts the riser 35 frames before the impact — its swell peaks ON
// the stamp. That gap is kept verbatim.
const PEAK = { impact: 19, bass: 3, snap: 3, pop: 1, scan: 4 };

type Sfx = { from: number; src: string; volume: number; dur?: number };
const SFX: Sfx[] = [
  // --- shot 1: brand lockup, then the hero card ---
  { from: SHOTS.open.from + 12, src: 'transition-soft.mp3', volume: 0.45 },
  { from: SHOTS.open.from + 78, src: 'whoosh-fast.mp3', volume: 0.45 }, // brand → dashboard
  { from: SHOTS.open.from + 128, src: 'whoosh-big.mp3', volume: 0.5 }, // card springs off the page
  { from: SHOTS.open.from + 141, src: 'sparkle.mp3', volume: 0.5, dur: 58 }, // beam lap 1 (cut before the shot ends)
  { from: SHOTS.open.from + 204, src: 'transition-snap.mp3', volume: 0.5 }, // reseat
  // --- shot 2: title card + charge sweep ---
  { from: SHOTS.title1.from, src: 'swoosh-quick.mp3', volume: 0.42 },
  { from: SHOTS.title1.from + 12, src: 'sweep-metal-quick.mp3', volume: 0.3 },
  // --- shot 3: the deck ---
  { from: SHOTS.deck.from, src: 'transition-soft.mp3', volume: 0.42 }, // pile close-up
  { from: SHOTS.deck.from + 30, src: 'whoosh-big.mp3', volume: 0.5 }, // pull-back + first deals
  { from: SHOTS.deck.from + 52, src: 'whoosh-fast.mp3', volume: 0.42 }, // dealing accelerates
  { from: SHOTS.deck.from + 70, src: 'whoosh-fast.mp3', volume: 0.32 }, // full flurry
  { from: SHOTS.deck.from + 122, src: 'whoosh-big.mp3', volume: 0.45 }, // swoosh back up the board
  // --- shot 4: transfers ---
  { from: SHOTS.transfers.from, src: 'transition-soft.mp3', volume: 0.45 },
  { from: beatF(40) - PEAK.bass, src: 'bass-hit-short.mp3', volume: 0.46 }, // last row seats on the kick
  // --- shot 5: marker title ---
  { from: SHOTS.title2.from, src: 'swoosh-quick.mp3', volume: 0.42 },
  { from: SHOTS.title2.from + 20, src: 'marker-pen-line.mp3', volume: 0.55, dur: 14 }, // the stroke itself (S4)
  // --- shot 6: billers land one by one (double-free ladder 0.40 → 0.25, S2) ---
  { from: SHOTS.bills.from, src: 'transition-soft.mp3', volume: 0.42 },
  ...[35, 45, 56, 66, 77, 87].map((f, i) => ({
    from: SHOTS.bills.from + f,
    src: 'pop.mp3',
    volume: 0.4 - i * 0.03,
  })).map((e) => ({ ...e, from: e.from - PEAK.pop })),
  // --- shot 7: scan, lock, unlock ---
  { from: SHOTS.lock.from, src: 'whoosh-fast.mp3', volume: 0.42 },
  { from: SHOTS.lock.from + localBeat(SHOTS.lock, 65) - PEAK.scan, src: 'data-scan.mp3', volume: 0.42, dur: 60 },
  { from: SHOTS.lock.from + localBeat(SHOTS.lock, 67) - PEAK.scan, src: 'data-scan.mp3', volume: 0.34, dur: 60 },
  { from: beatF(70) + 10, src: 'lock-quick.mp3', volume: 0.46 }, // the lock snaps, after the switches fall
  ...[0, 1, 2].map((i) => ({
    from: beatF(70) + i * 4,
    src: 'switch-click-quick.mp3',
    volume: 0.4 - i * 0.05,
    dur: 18,
  })),
  ...[0, 1, 2].map((i) => ({
    from: beatF(74) + i * 4,
    src: 'switch-click-quick.mp3',
    volume: 0.36 - i * 0.04,
    dur: 18,
  })),
  { from: beatF(74), src: 'shimmer-sparkle-sweep.mp3', volume: 0.3, dur: 40 }, // released
  // --- shot 8: the odometer ("click, click, clunk" on the eighths) ---
  { from: SHOTS.rewards.from, src: 'transition-soft.mp3', volume: 0.42 },
  ...LOCK_BEATS.map((b, i) => ({
    from: beatF(b),
    src: 'switch-click-quick.mp3',
    volume: 0.42 - i * 0.06,
    dur: 14,
  })),
  { from: beatF(LOCK_BEATS[2]) - PEAK.bass, src: 'bass-hit-short.mp3', volume: 0.46 }, // total confirmed
  // --- shot 9: one hit per hard jump of the block (the card's sound dependency) ---
  ...WIPE_STEPS.slice(0, 3).map((f, i) => ({
    from: SHOTS.wipe.from + f - PEAK.snap,
    src: 'transition-snap.mp3',
    volume: [0.44, 0.48, 0.52][i],
    dur: 14,
  })),
  { from: SHOTS.wipe.from + WIPE_STEPS[3] - PEAK.bass, src: 'bass-hit-short.mp3', volume: 0.5 }, // full-screen jump
  { from: SHOTS.wipe.from + WIPE_BADGE[0] - PEAK.pop, src: 'pop.mp3', volume: 0.4 }, // badge pops
  // --- shot 10: the fixed finale phrase riser → impact → sparkle ---
  { from: SHOTS.outro.from + 8, src: 'riser-cine.mp3', volume: 0.46, dur: 40 }, // swell peaks at +35 = the stamp, then hands over
  { from: beatF(93) - PEAK.impact, src: 'impact-deep-whoosh.mp3', volume: 0.5 }, // wordmark stamp, loudest cue
  { from: beatF(93) + 25, src: 'sparkle.mp3', volume: 0.4 },
];

const Bgm: React.FC = () => {
  const frame = useCurrentFrame();
  // 1s fade in, 1.7s fade out. Held at 0.28 rather than the reference film's 0.34: with 16 SFX
  // cues layered on top, 0.34 measured −0.02 dBFS peak on the render and 0.30 left only 0.34dB.
  const volume = interpolate(frame, [0, 30, TOTAL - 50, TOTAL], [0, 0.28, 0.28, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return <Audio src={staticFile('audio/bgm-tech-house.mp3')} volume={volume} />;
};

export const EastWestPromo: React.FC<{ bgm?: boolean }> = ({ bgm = true }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: CANVAS }}>
      {bgm ? <Bgm /> : null}
      {SFX.map((s, i) => (
        <Sequence key={`sfx-${i}`} from={s.from} durationInFrames={s.dur ?? 90}>
          <Audio src={staticFile(`audio/${s.src}`)} volume={s.volume} />
        </Sequence>
      ))}

      <Sequence from={SHOTS.open.from} durationInFrames={SHOTS.open.duration}>
        <SceneOpen />
      </Sequence>
      <Sequence from={SHOTS.title1.from} durationInFrames={SHOTS.title1.duration}>
        <TitleSweep
          before="Open a savings account in "
          keyword="minutes"
          after="."
          sub="No branch visit. Peso and foreign currency, side by side."
        />
      </Sequence>
      <Sequence from={SHOTS.deck.from} durationInFrames={SHOTS.deck.duration}>
        <SceneDeck />
      </Sequence>
      <Sequence from={SHOTS.transfers.from} durationInFrames={SHOTS.transfers.duration}>
        <SceneTransfers />
      </Sequence>
      <Sequence from={SHOTS.title2.from} durationInFrames={SHOTS.title2.duration}>
        <TitleMarker
          before="Pay every enrolled biller in "
          keyword="one tap"
          after="."
          sub="Electricity, water, telco, tuition — and your card."
        />
      </Sequence>
      <Sequence from={SHOTS.bills.from} durationInFrames={SHOTS.bills.duration}>
        <SceneBills />
      </Sequence>
      <Sequence from={SHOTS.lock.from} durationInFrames={SHOTS.lock.duration}>
        <SceneCardLock />
      </Sequence>
      {/* the odometer shot is held all the way to the end of the wipe: the wipe's LAST step is
          what has to land on a live frame, not just its first (round 2 found 7 blank frames when
          the overlap only covered the first half of the growth) */}
      <Sequence
        from={SHOTS.rewards.from}
        durationInFrames={SHOTS.wipe.from + SHOTS.wipe.duration - SHOTS.rewards.from}
      >
        <SceneRewards />
      </Sequence>
      <Sequence from={SHOTS.wipe.from} durationInFrames={SHOTS.wipe.duration}>
        <StepWipe />
      </Sequence>
      <Sequence from={SHOTS.outro.from} durationInFrames={SHOTS.outro.duration}>
        <SceneOutro />
      </Sequence>

      {CAPTIONS.map((c) => (
        <Sequence key={c.from} from={c.from} durationInFrames={c.duration}>
          <Caption text={c.text} duration={c.duration} />
        </Sequence>
      ))}

      {/* bright-field flashes straddling the hard cuts between live shots */}
      {[SHOTS.deck.from, SHOTS.transfers.from, SHOTS.bills.from, SHOTS.lock.from, SHOTS.rewards.from].map((cut) => (
        <Sequence key={`flash-${cut}`} from={cut - 5} durationInFrames={10}>
          <FlashCut duration={10} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
