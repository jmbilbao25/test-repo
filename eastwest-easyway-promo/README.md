# EastWest EasyWay — 2.5D feature promo

A 49.8-second, 1920×1080 cinematic promo about EastWest Bank's EasyWay digital-banking features,
built programmatically with [Remotion](https://www.remotion.dev/) using the
[video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) agent skill: real page
captures driven by a 2.5D page camera, cuts locked to a measured 124 BPM beat grid, and film-grade
sound design.

> **Unofficial concept piece.** Not affiliated with, endorsed by, or produced for EastWest Banking
> Corporation. Every screen in the film is a UI built for this video (`site/`); no bank page was
> screenshotted. All names, amounts and account numbers are fictional and card numbers are masked.
> Feature claims are paraphrased from EastWest's public
> [EasyWay](https://www.eastwestbanker.com/easyway-app) and
> [card](https://www.eastwestbanker.com/cards/debit-cards) pages, and the closing frame says so on
> screen.

## Deliverables

| File | What it is |
|---|---|
| `out/eastwest-easyway-promo.mp4` | the film, with music (peak −0.57 dBFS) |
| `out/eastwest-easyway-promo-nobgm.mp4` | same picture, SFX only, for your own music (bit-identical video stream) |

## The film

| # | Frames | Shot | Feature |
|---|---|---|---|
| 1 | 0–232 | brand lockup + spotlight on the balance card | one app for everything |
| 2 | 232–320 | title card, charge sweep on "minutes" | open a savings account in-app |
| 3 | 320–523 | twelve feature cards dealt onto the board | the breadth: savings, QR InstaPay, loans, applications, installments, Insta-Cash |
| 4 | 523–697 | transfer rows drop in and embed | free to EastWest & KOMO, InstaPay & PESONet 24/7 |
| 5 | 697–784 | title card, marker underline on "one tap" | bills payment |
| 6 | 784–929 | enrolled billers find their places | enrol once, pay anytime |
| 7 | 929–1103 | the card is scanned, locked, then released | lock/unlock for ATM, online, in-store |
| 8 | 1103–1278 | odometer rolls to 8.88% | cash rewards on card spend |
| 9 | 1263–1307 | brand colour-block step wipe | chapter break |
| 10 | 1307–1495 | launch-style group photo + wordmark stamp | sign-off |

Full production record — brand tokens, motion tokens, beat analysis, feature→shot map, storyboard,
sound design, the deliberate rule deviations and everything the two review rounds changed — is in
[`DESIGN-SPEC.md`](DESIGN-SPEC.md). The reviews themselves are [`FINAL-REVIEW.md`](FINAL-REVIEW.md)
and [`REVIEW-ROUND2.md`](REVIEW-ROUND2.md).

## Build it yourself

```bash
npm install
npx playwright install chromium     # for the page capture step
npm run capture                     # site/ → public/textures/live/ + src/ew/live-layout.json
npm run render                      # → out/eastwest-easyway-promo.mp4
npm run render:nobgm                # → the SFX-only version
npm run dev                         # Remotion Studio, if you want to scrub it
```

## Verification

The film is checked, not vibed. Every one of these runs in CI-friendly isolation:

```bash
npm run check          # beat grid, shot tiling, hold budgets, asset references, no bare frame numbers
npm run check:blank    # no frame of the film is a near-empty canvas
npm run check:still    # every declared hold is actually still in the rendered pixels, and long enough
npm run verify:beats   # re-measures the delivered mp4's audio against the design grid (needs uv)
```

Current results: all timeline invariants hold · no near-empty frames · 4/4 holds still
(worst frame-to-frame difference 0.121) · 15 graded beat anchors, mean audio-truth error 7.4 ms,
**worst 0.72 frames** against a 3-frame perceptual threshold.

## Layout

```
site/                 the UI the film shoots (own layouts, EastWest brand tokens, fictional data)
tools/
  extract-brand.mjs   read-only brand-token extraction from the public site
  capture.mjs         full-page 2x + 4x hero cutouts + layout.json
  beat-analysis.py    librosa beat-grid fit + kick phase lock  → analysis/
  beat-verify.py      post-render sync measurement             → analysis/render_sync.json
  check-timeline.mjs  timeline invariants
  still-check.mjs     pixel stillness of the declared holds
  blank-check.mjs     near-empty frame scan
src/ew/
  beats.ts            the beat grid and the shot table — the film's single source of truth
  brand.ts            the extracted design tokens
  Main.tsx            timeline, captions and the whole SFX table
  lib/                PageCam / Caption / FlashCut, copied from the skill
  scenes/             one file per shot; each header names the shot card it implements
analysis/             beat data, grid candidates, post-render sync audit
```

## Credits

- Method, shot recipe cards, components and audio: [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) (see its `assets/audio/ATTRIBUTION.md` for the SFX/BGM licensing)
- Review loop method: [gauntlet-loop](https://github.com/duolahypercho/gauntlet-loop)
- Minimal-code discipline and the "leave one runnable check behind" rule: [ponytail](https://github.com/DietrichGebert/ponytail)
- Orchestration habits: [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)
- Typeface: Poppins (Google Fonts, OFL)
