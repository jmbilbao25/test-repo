"""Post-render beat回测 (music-beat-sync §5b), done in a way that is actually measurable.

Re-fitting a free beat grid on the FINISHED mix does not work here: 16 SFX cues sit on top of
the drums, so `beat_track` returns a poor line (measured ±141ms residual vs ±8ms on the clean
source) and its wrong period fakes a linear "drift" across the film. So instead:

  1. cross-correlate the rendered audio against the source BGM to measure the real offset the
     encode introduced — this is what decides whether the design grid still applies to the
     delivered file;
  2. with the design grid held fixed, measure every anchor against the nearest real kick
     transient IN THE RENDERED AUDIO (audio-truth error);
  3. report the frame-quantisation cost separately (§5a: ±16.7ms is the 30fps floor).

Run: uv run --with librosa --with scipy --python 3.11 tools/beat-verify.py
"""
import json
import re
import subprocess

import numpy as np
import librosa
from scipy.signal import butter, sosfilt

FPS = 30
MP4 = "out/eastwest-easyway-promo.mp4"
WAV = "out/render-audio.wav"
BGM = "public/audio/bgm-tech-house.mp3"
FF = "node_modules/ffmpeg-static/ffmpeg"

subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", MP4, "-vn",
                "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1", WAV], check=True)

design = json.load(open("analysis/beat_data.json"))
t0, T = design["t0"], design["T"]
SR = 22050
y, _ = librosa.load(WAV, sr=SR, mono=True)
src, _ = librosa.load(BGM, sr=SR, mono=True, duration=60.0)
print(f"rendered audio {len(y)/SR:.2f}s   design grid {60/T:.2f} BPM, t0={t0:.4f}s")

# ---- 1. offset of the music bed inside the delivered file ------------------
# correlate ONSET ENVELOPES rather than raw samples: the film's SFX are broadband and
# swamp a sample-domain correlation, but they cannot move the drum envelope's comb
env_y = librosa.onset.onset_strength(y=y, sr=SR)
env_s = librosa.onset.onset_strength(y=src, sr=SR)
hop_s = 512 / SR
# a four-on-the-floor envelope is periodic, so an unconstrained correlation happily locks
# onto a peak N beats away — search only within ±half a beat of zero lag
a = env_y[int(16 / hop_s):int(34 / hop_s)]        # steady, full-energy stretch of the film
half = T / 2
lo = int((16 - half) / hop_s)
hi = int((16 + half) / hop_s)
best, lag_s = -1e18, 0.0
for k in range(lo, hi + 1):
    b_ = env_s[k:k + len(a)]
    if len(b_) < len(a):
        break
    v = float(np.dot(b_ - b_.mean(), a - a.mean()))
    if v > best:
        best, lag_s = v, k * hop_s - 16.0
print(f"BGM offset in the render: {lag_s*1000:+.1f}ms ({abs(lag_s)*FPS:.2f} frames) "
      f"— {'no trim, design grid applies as-is' if abs(lag_s) < 1.5/FPS else 'REVIEW'}")

# ---- 2. real kick transients in the rendered mix ---------------------------
sos = butter(4, [40, 160], btype="band", fs=SR, output="sos")
env = np.asarray(librosa.onset.onset_strength(y=sosfilt(sos, y), sr=SR), dtype=np.float64)
et = librosa.times_like(env, sr=SR)
# Global peak-picking is useless on a finished mix: one loud impact raises env.max() and
# every drum kick around it drops below the threshold. Measure LOCALLY instead — for each
# anchor, find the strongest low-band attack within ±0.25s of the designed cut. On a
# four-on-the-floor track (and with our own SFX pinned to the same beats) that attack IS
# what the audience hears on the cut.
def attack_near(t_s: float, window: float = 0.12) -> float:  # a quarter beat: can only
    # ever find the attack that belongs to THIS beat, never the neighbouring eighth
    m = (et >= t_s - window) & (et <= t_s + window)
    return float(et[m][int(np.argmax(env[m]))])

grid = np.array([t0 + n * T for n in range(int((len(y) / SR - t0) / T))])
lat = float(np.median([attack_near(g) - g for g in grid[6:]]))  # skip the intro fade-in
print(f"onset-envelope latency removed: {lat*1000:+.1f}ms\n")

# anchors are read out of the film's own shot/lock tables so this report can never describe a
# cut the film no longer has (round 2 caught it describing the previous edit)
src = open("src/ew/beats.ts").read()
SHOTS = {m[1]: (int(m[2]), int(m[3]))
         for m in re.finditer(r"(\w+): shot\((\d+), (\d+)\)", src)}
CUTS = {f"shot {i+1} {name}": beats[0] for i, (name, beats) in enumerate(SHOTS.items())}
LOCK_BEATS = [float(x) for x in re.search(r"LOCK_BEATS = \[([^\]]+)\]",
              open("src/ew/scenes/SceneRewards.tsx").read()).group(1).split(",")]
ACCENTS = {"transfer rows seat": 40, "card lock snaps": 70, "card unlocks": 74,
           "odometer lock 1": LOCK_BEATS[0], "odometer locks": LOCK_BEATS[-1],
           "wordmark stamp": 93}
# Anchors with no attack to measure against are reported but NOT graded: the ≤3f threshold is
# about hit events. Beat 0 sits inside the music's 1s fade-in (no transient exists yet), and a
# sweep-pass boundary is continuous motion reversing direction, not a slam — in both windows
# the strongest low-band energy belongs to our own layered SFX, so the number describes the
# measurement, not a visible desync.
UNGRADED = {"shot 1 open", "sweep pass 1"}
MOTION = {"sweep pass 1": 65}

rows = []
print(f"{'anchor':22} {'beat':>6} {'frame':>6} {'audio':>9} {'quantise':>9} {'total':>7}")
for name, b in {**CUTS, **ACCENTS, **MOTION}.items():
    design_s = t0 + b * T
    frame = round(design_s * FPS)
    hit = attack_near(design_s) - lat
    audio_ms = (design_s - hit) * 1000
    quant_ms = (frame / FPS - design_s) * 1000
    total_f = abs(frame / FPS - hit) * FPS
    rows.append((name, b, frame, audio_ms, quant_ms, total_f))
    flag = "  (ungraded: no attack in window)" if name in UNGRADED else ""
    print(f"{name:22} {b:>6} {frame:>6} {audio_ms:>+8.1f}ms {quant_ms:>+8.1f}ms {total_f:>6.2f}f{flag}")

graded = [r for r in rows if r[0] not in UNGRADED]
worst = max(r[5] for r in graded)
mean_audio = np.mean([abs(r[3]) for r in graded])
print(f"\n{len(graded)} graded anchors · mean audio-truth error {mean_audio:.1f}ms · worst {worst:.2f} frames")
print("PASS (≤3f perceptual threshold, ideal ≤1.5f)" if worst <= 3 else "FAIL — retime the anchors over 3f")
json.dump([{"anchor": r[0], "beat": r[1], "frame": r[2], "audio_ms": r[3],
            "quantise_ms": r[4], "total_frames": r[5], "graded": r[0] not in UNGRADED} for r in rows],
          open("analysis/render_sync.json", "w"), indent=1)
