// Beat grid for bgm-tech-house.mp3, measured by tools/beat-analysis.py
// (see analysis/beat_data.json + analysis/grid_drift.json).
//   least-squares fit of the beat series : 124.00 BPM, T = 0.4838905 s, residual ±8 ms
//   phase locked to the kick transients  : t0 = 0.004511 s  (kicks 40.1% on integer beats
//                                          vs 22.6% before the lock)
// Every shot boundary and every SFX cue is written as beatF(n) or SHOTS.x.from + offset —
// never a bare frame number (music-beat-sync §4/§4.5), so re-timing one shot can't
// desync the rest.
export const FPS = 30;
export const BEAT0 = 0.004511;
export const BEAT_INT = 0.4838905;

export const beatT = (n: number) => BEAT0 + n * BEAT_INT;
export const beatF = (n: number) => Math.round(beatT(n) * FPS);

const shot = (a: number, b: number) => ({ from: beatF(a), duration: beatF(b) - beatF(a), beats: [a, b] as const });

// Energy arc rides the track's own RMS profile: intro (0-8s) under the brand open,
// build (8-16s) under the title + deck, full energy (16s+) from the transfers shot on.
export const SHOTS = {
  open: shot(0, 16), //   0- 232  brand lockup + spotlight-hero-card
  title1: shot(16, 22), // 232- 319  gradient-word-sweep title
  deck: shot(22, 36), //  319- 523  deck-deal-flyin feature wall
  transfers: shot(36, 48), // 523- 697 row-embed
  title2: shot(48, 54), // 697- 784  marker-underline title
  bills: shot(54, 64), // 784- 929  list-reveal
  lock: shot(64, 76), //  929-1103  scan-bracket-sweep + lock/unlock
  rewards: shot(76, 88), // 1103-1278 odometer-digit-roll
  // The step wipe is a TAKEOVER transition, so it deliberately overlaps the shot it eats:
  // it starts a beat before the odometer shot ends and grows over the live 8.88% frame.
  // (Rendering it in its own non-overlapping slot left two blank frames — caught in review.)
  wipe: shot(87, 90), //  1263-1307 color-block-step-wipe, on top of the odometer's last beat
  outro: shot(90, 103), // 1307-1495 outro-group-photo-launch
} as const;

export const TOTAL = beatF(103); // 1495f = 49.83s

/** beat number → frame local to a shot */
export const localBeat = (s: { from: number }, n: number) => beatF(n) - s.from;
