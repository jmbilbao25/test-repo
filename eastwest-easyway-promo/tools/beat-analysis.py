"""Beat grid analysis for the promo BGM (video-shotcraft references/music-beat-sync.md §1-§3).

Run: uv run --with librosa --with scipy --python 3.11 tools/beat-analysis.py
Outputs analysis/beat_data.json + analysis/grid_drift.json
"""
import json
import os

import numpy as np
import librosa
from scipy.signal import butter, sosfilt

SRC = "public/audio/bgm-tech-house.mp3"
OUT = "analysis"
os.makedirs(OUT, exist_ok=True)

y, sr = librosa.load(SRC, sr=None, mono=True)
dur = len(y) / sr
print(f"loaded {SRC}: {dur:.2f}s @ {sr}Hz")

# --- §1 grid fit: never trust the beat_track tempo scalar, least-squares the beat series
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, tightness=400, units="time")
# the promo only uses the first ~60s: fit the grid on the first 80s of beats so a
# late-track tempo/edit drift can't bend the grid under our cut points
beats = np.asarray([b for b in beats if b <= 80.0], dtype=np.float64)
i = np.arange(len(beats))
A = np.vstack([i, np.ones_like(i)]).T
(T, t0), *_ = np.linalg.lstsq(A, beats, rcond=None)
bpm = 60.0 / T
resid = beats - (t0 + i * T)
print(f"beat_track tempo scalar = {float(np.atleast_1d(tempo)[0]):.2f}")
print(f"fitted BPM={bpm:.2f} t0={t0:.4f}s T={T:.5f}s residual max ±{np.abs(resid).max()*1000:.0f}ms")


def band_env(lo, hi):
    sos = butter(4, [lo, hi], btype="band", fs=sr, output="sos")
    e = librosa.onset.onset_strength(y=sosfilt(sos, y), sr=sr)
    return e, librosa.times_like(e, sr=sr)


kick_env, times = band_env(40, 160)
snare_env, _ = band_env(150, 500)
hihat_env, _ = band_env(6000, 12000)

# real transients per band (for §3 grid scoring + sparse accent pinning)
def peaks(env, delta_ratio=0.35):
    env = np.asarray(env, dtype=np.float64)
    thr = float(env.max()) * delta_ratio
    idx = librosa.util.peak_pick(env, pre_max=3, post_max=3, pre_avg=5, post_avg=5,
                                 delta=float(thr * 0.25), wait=2)
    return [(float(times[j]), float(env[j])) for j in idx if env[j] >= thr]


kicks, snares, hats = peaks(kick_env), peaks(snare_env), peaks(hihat_env, 0.45)
print(f"transients: kick={len(kicks)} snare={len(snares)} hihat={len(hats)}")


def score_grid(t0c, Tc, hit_times, horizon=70.0):
    """Score a candidate grid by how well ITS OWN beats sit on real transients.

    The band-limited onset envelope has a constant analysis latency, so we remove
    the median signed offset first — otherwise every candidate is penalised by the
    same systematic shift and the comparison is meaningless.
    """
    hit = np.array(sorted(hit_times))
    if len(hit) == 0:
        return None
    n_max = max(0, int((min(dur, horizon) - t0c) / Tc))
    grid = np.array([t0c + n * Tc for n in range(n_max)])
    nearest = hit[np.clip(np.searchsorted(hit, grid), 0, len(hit) - 1)]
    prev = hit[np.clip(np.searchsorted(hit, grid) - 1, 0, len(hit) - 1)]
    signed = np.where(np.abs(nearest - grid) < np.abs(grid - prev), nearest - grid, prev - grid)
    lat = float(np.median(signed))
    errs = np.abs(signed - lat)
    return {
        "t0": t0c, "T": Tc, "bpm": 60.0 / Tc, "beats_checked": int(n_max),
        "envelope_latency_ms": lat * 1000,
        "match_pct": float((errs < 0.06).mean() * 100),
        "mean_abs_ms": float(errs.mean() * 1000),
        "p90_ms": float(np.percentile(errs, 90) * 1000),
    }


# 0.5x / 1x / 2x candidates against kick+snare transients
onsets = sorted([t for t, _ in kicks] + [t for t, _ in snares])
cands = {
    "0.5x": score_grid(t0, T * 2, onsets),
    "1x": score_grid(t0, T, onsets),
    "2x": score_grid(t0, T / 2, onsets),
}
for k, v in cands.items():
    print(k, json.dumps(v))

# --- phase lock: a four-on-the-floor kick IS beat 1, so re-derive t0 from the
# kick transients themselves (circular mean of their phase in the fitted period).
# beat_track's phase can sit a half beat off; the grid period is the reliable part.
kt = np.array([t for t, _ in kicks])
ks = np.array([s for _, s in kicks])
ph = ((kt - t0) / T) % 1.0
ang = 2 * np.pi * ph
mean_ph = (np.arctan2((ks * np.sin(ang)).sum(), (ks * np.cos(ang)).sum()) / (2 * np.pi)) % 1.0
t0_locked = t0 + mean_ph * T
while t0_locked - T > 0:
    t0_locked -= T
print(f"kick circular-mean phase = {mean_ph:.3f} → t0 {t0:.4f}s -> {t0_locked:.4f}s")


def phase_split(t0c, Tc):
    p = ((kt - t0c) / Tc) % 1.0
    return (float(((p < 0.12) | (p > 0.88)).mean() * 100), float((np.abs(p - 0.5) < 0.12).mean() * 100))


print("kick phase (raw fit): %.1f%% integer / %.1f%% half" % phase_split(t0, T))
print("kick phase (locked):  %.1f%% integer / %.1f%% half" % phase_split(t0_locked, T))
cands["1x-locked"] = score_grid(t0_locked, T, onsets)
print("1x-locked", json.dumps(cands["1x-locked"]))

on_int, on_half = phase_split(t0_locked, T)
winner = ("1x-locked", cands["1x-locked"]) if on_int > on_half else max(
    cands.items(), key=lambda kv: (kv[1]["match_pct"], -kv[1]["mean_abs_ms"]))
print("winner:", winner[0])

# kick energy per integer beat of the winning grid → slam candidates
wt0, wT = winner[1]["t0"], winner[1]["T"]
beat_energy = []
for n in range(int((min(dur, 70.0) - wt0) / wT)):
    t = wt0 + n * wT
    j = int(np.argmin(np.abs(times - t)))
    beat_energy.append({"n": n, "t": float(t), "kick": float(kick_env[j]),
                        "snare": float(snare_env[j]), "hihat": float(hihat_env[j])})
slams = sorted(beat_energy, key=lambda b: -b["kick"])[:14]
print("top kick beats:", [(b["n"], round(b["kick"], 1)) for b in slams])

# RMS energy structure (2-second buckets) → where the track is full-energy
rms = librosa.feature.rms(y=y)[0]
rms_t = librosa.times_like(rms, sr=sr)
buckets = []
for s in np.arange(0, min(dur, 70.0), 2.0):
    m = (rms_t >= s) & (rms_t < s + 2.0)
    if m.any():
        buckets.append({"t": float(s), "rms": float(rms[m].mean())})
peak_rms = max(b["rms"] for b in buckets)
for b in buckets:
    b["rel"] = round(b["rms"] / peak_rms, 3)
print("rms profile:", [(b["t"], b["rel"]) for b in buckets])

json.dump({
    "source": SRC, "duration": dur, "sr": int(sr),
    "bpm": winner[1]["bpm"], "t0": wt0, "T": wT,
    "beat_track_tempo_scalar": float(np.atleast_1d(tempo)[0]),
    "fit_residual_max_ms": float(np.abs(resid).max() * 1000),
    "beats": [float(wt0 + n * wT) for n in range(int((min(dur, 70.0) - wt0) / wT))],
    "hits": ([{"t": t, "s": s, "k": "kick"} for t, s in kicks]
             + [{"t": t, "s": s, "k": "snare"} for t, s in snares]
             + [{"t": t, "s": s, "k": "hihat"} for t, s in hats]),
    "beat_energy": beat_energy,
    "slam_candidates": slams,
    "rms": buckets,
}, open(f"{OUT}/beat_data.json", "w"), indent=1)
json.dump({"candidates": cands, "winner": winner[0],
           "reason": "highest transient match against kick+snare onsets over the first 70s"},
          open(f"{OUT}/grid_drift.json", "w"), indent=1)
print("wrote", f"{OUT}/beat_data.json")
