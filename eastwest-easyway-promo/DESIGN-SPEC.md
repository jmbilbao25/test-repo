# EastWest EasyWay — 2.5D feature promo · design spec

Made with the [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) agent skill
(Remotion + real page captures + 2.5D camera + beat-synced cuts + film SFX).
Mode: **autonomous free creation** (`references/pipeline.md`, stages 0–7) — the brief was a
single line ("2.5D mp4 about EastWest features, use its style / theme colours"), so the agent
decided visual direction, shot mapping, storyboard, assets and audio and ran straight through,
recording its judgements here instead of stopping for approval.

This file describes **the delivered film**, not an earlier plan. Where the film departs from the
first storyboard, the change and its reason are recorded in [Changes after review](#changes-after-review).

> **Unofficial concept piece.** Not affiliated with, endorsed by, or produced for EastWest
> Banking Corporation. Every screen in the film is a UI the agent built locally for this video
> (`site/`); no bank page was screenshotted. All names, amounts and account numbers are
> fictional, and card numbers are fully masked. Feature claims are paraphrased from EastWest's
> public product pages ([EasyWay app](https://www.eastwestbanker.com/easyway-app),
> [debit cards](https://www.eastwestbanker.com/cards/debit-cards)); the closing frame carries
> that disclaimer on screen.

---

## Stage 0 — product brief & execution constraints

| Field | Decision | Evidence / consequence for this film |
|---|---|---|
| Subject | EastWest Bank PH digital banking (EasyWay app + cards) | user brief "east west features" |
| Purpose | Feature-showcase promo (portfolio/demo grade) | drives the launch-event outro energy |
| Audience | Filipino retail banking customers | English copy, PHP amounts, local context |
| Must-show features | 6 (see stage 2 map) | taken from EastWest's public EasyWay/cards pages |
| Format | 1920×1080, 30 fps, **1495f = 49.83 s**, MP4 (H.264 + AAC) | brief said "mp4" |
| Audio | `bgm-tech-house.mp3` (skill library) + 17 pinned SFX cues; delivered with and without BGM | S1: strong-kick electronic bed for the promo genre |
| Data rule | 100% fictional; no personal names, no issuer BIN, card PAN masked, no third-party trademarks | Q1 |
| Reproduction rule | UI is hand-built (non-reproduction scenario), then **really captured** at 2× (heroes at 4×) and driven as page textures | Q1 permits hand-built UI outside reproduction; real capture keeps text crisp under the 2.5D camera |

## Stage 1 — visual direction (from the real brand, not an invented promo skin)

Tokens extracted read-only from `eastwestbanker.com` computed styles
(`tools/extract-brand.mjs` → `brand/tokens-raw.json`), so the film's type and colour are the
brand's own, per the skill's core principle 2:

| Token | Value | Where it came from |
|---|---|---|
| Type family | **Poppins** 300/400/500/600/700/800 | the only family on both pages (1464 nodes) |
| Primary magenta | `#B2006F` | most-used brand surface (129 nodes) |
| Deep purple | `#542785` | second brand surface + heading colour |
| Lime accent | `#D5E04D` | accent surface / gradient stop |
| Brand gradient | `linear-gradient(90deg, #542785, #B2006F)` | EasyWay page hero |
| Ink / body | `#151515` / `#404040` | text colours |
| Radii | pill `25px`, cards `8/16/24/32px` | radius tally |
| Type scale | 80 / 40 / 32 / 28 / 24 / 16 / 12 px | fontSize tally |

Beams, seams, scan lines, dust and glows use the lime on dark and the magenta on light — the
template's amber never appears, and the two title cards' gradients use only brand tokens.
The styleframe step was **skipped deliberately** (pipeline stage 1 permits this with a recorded
reason): the brand spec above is measured rather than invented, and every shot is verified with
`remotion still` frames instead.

**Brand → motion tokens** (pipeline stage 1 table): energy axis mid-high, tone axis
serious-but-consumer → start from *professional trust* (~21f, `bezier(0,0,0.2,1)`, no bounce)
and blend one step toward *bold vitality*:

| Token | Value |
|---|---|
| Main entrance duration | 24f (0.8 s) |
| Entrance easing | `bezier(0.16,1,0.3,1)` |
| Landing easing (anything that must land) | `bezier(0.34,1.4,0.44,1)` — y1 > 1, real overshoot |
| Overshoot ceiling | 1.06 (cards) / 1.12 (group photo) |
| Squash | 0 |
| Camera | slow, no handheld shake (Q3) |

## Music (stage 0 addendum — `references/music-beat-sync.md`)

`tools/beat-analysis.py` (librosa) → `analysis/beat_data.json`, `analysis/grid_drift.json`:

- least-squares grid fit on the beat series: **124.00 BPM**, `T = 0.48389 s`,
  fit residual **±7.6 ms** (≤15 ms ⇒ machine grid, trustworthy)
- half/double + phase check: `beat_track`'s phase sat a half beat off; re-locking `t0` to the
  circular mean of the kick transients flipped kick placement from 22.6% → **40.1% on integer
  beats** (and 40.1% → 22.6% on half beats), so the winning grid is `1x-locked`
  (`t0 = 0.00451 s`)
- energy structure (RMS): 0–8 s intro ≈0.33, 8–16 s build 0.47→0.63, **full energy from 16 s** —
  the film rides it: brand + hero card in the intro, the feature deck accelerating through the
  build, everything from the transfers shot on at full energy
- the film's three slams are pinned to real strong kicks — b40 (transfer rows seat), b70 (card
  lock snaps), b93 (wordmark stamp)
- the timeline is written as `beatF(n)` only, never bare frame numbers:
  `beatF(n) = round((0.004511 + n·0.48389)·30)`, 1 beat = 14.5167f

Percussive cues are pinned by their **internal peak**, not their file head
(`start = target beat − (peak − trim)`), measured per sample: impact-deep-whoosh 632 ms (19f),
bass-hit-short 85 ms (3f), transition-snap 115 ms (3f), pop 37 ms (1f), data-scan 123 ms (4f),
lock-quick and switch-click-quick effectively instant. `riser-cine` peaks at 35f — which is
exactly why the reference film's finale puts the riser 35 frames before the impact; its swell
peaks **on** the stamp. That gap is kept verbatim.

## Stage 2 — feature → shot map (P4: every feature has a shot, no repeated device)

| # | EastWest feature (public) | Shot card (`references/shots/…`) | Why this motion grammar |
|---|---|---|---|
| 1 | The app itself / balance at a glance | `opening/spotlight-hero-card` | single-protagonist opening: one card = the product's atom (Q5) |
| 2 | Savings, QR InstaPay, auto loan, credit-card apply, installment, Insta-Cash, time deposit (breadth) | `ui-entrance/deck-deal-flyin` | "lots of things pour in" — the dealing metaphor for a feature wall (R2) |
| 3 | Free transfers to EastWest/KOMO, InstaPay & PESONet 24/7 | `ui-entrance/row-embed` | structured data growing into a page |
| 4 | One-stop bills payment, enrolled billers | `ui-entrance/list-reveal` | a low-energy readable beat between two loud shots |
| 5 | Card lock/unlock for ATM, online, in-store | `effects/scan-bracket-sweep` | "the machine is inspecting this card" = security semantics |
| 6 | Up to 8.88% cash rewards | `data/odometer-digit-roll` | one ace number, mechanical roll + per-digit lock |
| — | chapter break into the finale | `transition/color-block-step-wipe` (variant A) | brand purple→magenta hard steps, zero interpolation |
| — | title cards | `typography/gradient-word-sweep`, `typography/marker-underline-title` | two different devices so the two cards aren't the same trick twice |
| — | brand sign-off | `outro/outro-group-photo-launch` | launch-event group photo at peak energy (Q8) |

Each card was read in full and its exact reference implementation read before any code was
written: `template/src/aifl/live/SceneOpen.tsx`, `SceneFlyIn.tsx`, `SceneDetail.tsx`,
`SceneOutroLive.tsx`, `demos/data/odometer-digit-roll/`, `demos/effects/scan-bracket-sweep/`,
`demos/transition/color-block-step-wipe/`, `demos/typography/gradient-word-sweep/`.
`assets/lib/PageCam.tsx` (2.5D page camera; layout-scale CSS `zoom` for sharp text under
magnification) is copied in verbatim — the foundation of every "real page" shot — along with
`FlashCut` and `rand`.

## Stage 3 — storyboard as delivered (every boundary on a beat)

| # | Beats | Frames | Shot | Key motion | Caption |
|---|---|---|---|---|---|
| 1 | 0–16 | 0–232 | brand open + `spotlight-hero-card` | wordmark letterpress + 30f still hold → spotlight roves, locks the balance card, 16f push-in to a left-oblique, card rises, lime beam runs 2 laps, reseats | ONE APP FOR EVERYTHING YOU BANK |
| 2 | 16–22 | 232–320 | `gradient-word-sweep` | "Open a savings account in **minutes**." — lime→magenta→purple charge sweep, ≤2 bolts on screen | — |
| 3 | 22–36 | 320–523 | `deck-deal-flyin` | the page's twelve feature cards orbit on dark brushed metal, pull back, deal into their real slots on a hard-accelerating cadence (5.5f → 2.0f gaps), camera chases down, 18f rest | TWELVE THINGS YOU USED TO QUEUE FOR / QR INSTAPAY · LOANS · INSTALLMENTS |
| 4 | 36–48 | 523–697 | `row-embed` | transfer rows drop and embed with a lime seam; the last one seats on b40 with one lime bloom over the two free transfers | FREE TO EASTWEST & KOMO, 24/7 |
| 5 | 48–54 | 697–784 | `marker-underline-title` | "Pay every enrolled biller in **one tap**." — tapered marker stroke drawn under the keyword in 10f | — |
| 6 | 54–64 | 784–929 | `list-reveal` | biller rows find their places on a 10f stagger while the container drifts 32px and eases to a stop | DUE DATES AND AMOUNTS, PRE-FILLED |
| 7 | 64–76 | 929–1103 | `scan-bracket-sweep` | card dead still; brackets drop, a 3px lime line sweeps it once per beat for 5 beats, the three switches fall on b70 and the LOCKED badge lands after them, released on b74 | LOCK ATM, ONLINE AND IN-STORE / SWITCH IT BACK ON ANYTIME |
| 8 | 76–88 | 1103–1278 | `odometer-digit-roll` | 8.88 rolls per digit and locks left→right on b82 / b82.5 / b83, deepening pulse, then 52 frames of true stillness | CASH REWARDS ON CARD SPEND |
| 9 | 87–90 | 1263–1307 | `color-block-step-wipe` A | four hard jumps (6/8/6f gaps) grow from the left edge **over the live odometer frame**, colour stepping purple→magenta, badge pops and steps back out | — |
| 10 | 90–103 | 1307–1495 | `outro-group-photo-launch` | 9 delegates fly in around the wordmark on a deep-purple stage, crane lands, stamp on b93, then the camera freezes for 93 frames | (clean — C1 exception) |

Shots 9 and 10 overlap shot 8 and each other by design: a takeover transition has to eat a live
frame. Rest budget reserved up front (R1/R3) and verified in the delivered pixels by
`npm run check:still`: 30f wordmark hold, 18f full-board rest, 52f after the odometer locks, 37f
sign-off hold.

## Stage 6 — sound design

BGM `bgm-tech-house.mp3` at 0.28 with a 1 s fade-in / 1.7 s fade-out, wrapped in a `bgm` boolean
inputProp so one timeline renders both deliverables. 17 SFX cues from `assets/audio/sfx/**` in a
single declarative table in `Main.tsx`; every `from` is `beatF(n)` or `SHOTS.x.from + offset`, and
the step-wipe hits import the picture's own step thresholds so the two cannot drift apart. Film
vocabulary only (whoosh / impact / riser / sparkle / transition) plus real-object foley for the
switches, the marker stroke and the scanner; no synthesised UI tones (S1). The finale keeps the
fixed three-beat phrase riser → impact → sparkle. Delivered peak: **−0.57 dBFS** (with BGM) and
**−1.72 dBFS** (SFX only).

## Verification

| Command | What it proves |
|---|---|
| `npm run check` | beat grid matches `analysis/beat_data.json`; shots tile the timeline (transitions may overlap, nothing else may); every declared hold has a frame budget; every referenced texture/audio exists; no bare frame numbers in the SFX table |
| `npm run check:blank` | no frame in the film is a near-empty canvas |
| `npm run check:still` | every declared hold is **actually still in the rendered pixels**, and long enough |
| `npm run verify:beats` | re-measures the delivered MP4's audio: BGM offset, then every cut and accent against the nearest real transient. Result: 15 graded anchors, mean audio-truth error 7.4 ms, **worst 0.72 frames** (threshold 3f, ideal 1.5f) |

`analysis/render_sync.json` is the per-anchor audit trail, generated from the delivered file.
Two anchors are reported but **ungraded**, with the reason in the tool: beat 0 sits inside the
music's fade-in and a sweep-pass boundary is continuous motion, so neither has an attack to
measure against.

## Deliberate rule deviations (aesthetic-rules.md asks for these to be written down)

1. **Hand-built UI** (Q1) — no EastWest page is reproduced; the film's screens are original
   layouts in `site/` skinned with the extracted tokens, then captured for real at 2×/4×, which
   is exactly the case Q1's 2026-07-13 revision permits.
2. **Styleframe skipped** (stage 1) — replaced by measured brand tokens plus per-shot
   `remotion still` verification.
3. **Q11, page body copy** — captions (56 px), title cards (92 px), the odometer (190 px) and the
   outro lines (150/44/36/26 px) are all at or above the floor. The *captured page's own* body
   copy is not: it runs 14–21 px CSS. Where a shot lingers on it, it is either enlarged (the deck
   chase and glide run at zoom 0.95/1.15 so card titles read) or **declared texture** and
   defocused (the card page's activity panel, `SceneCardLock.tsx`). No shot asks the audience to
   read something it renders too small to read.
4. **The scan band is 3 px, not the demo's 2.5 px** — the rest of that shot's geometry is scaled
   from the demo's 480×270 design space to our smaller subject, but the band's ceiling ("above
   4 px reads as a mask edge") is absolute, so it is set just under it.
5. **No inline digit roll in shot 4.** The first storyboard had the transfer amount rolling on
   b40. It was cut before implementation: P4 allows one device to star once, and the odometer
   owns that device in shot 8. Shot 4's beat-40 moment is the last row seating plus one lime
   bloom instead.
6. **The film has no product call-to-action.** The closing line points at EastWest's public
   feature page as a source; an unofficial concept film should not tell anyone to download a
   bank's app. Q11's "the closing line is the one that should never be small" is honoured at
   36 px.

## Changes after review

Every change below came from an independent reviewer with a clean context reading the delivered
file (pipeline stage 7 — the maker is not allowed to self-certify — run as the harsh-critic loop
described in the repo table below). Round 1: `FINAL-REVIEW.md`. Round 2: `REVIEW-ROUND2.md`.

| Found | Change |
|---|---|
| 2 blank frames where the step wipe grew on an empty canvas (r1), then 7 when the fix only overlapped half the growth (r2) | the odometer shot is now held to the **end** of the wipe, and `check:blank` scans every frame of every render |
| the outro never held still — the crane pushed to the last frame (r1) | push freezes at STAMP+40; `check:still` measures 37 still frames |
| the card read "Active" and "LOCKED" at once, and the badge blended to amber (r1) | badge is opaque from frame one, sized to cover the status field; the switches now fall *before* it lands |
| two copies of one feature card on screen — first landed (r1), then in flight (r2) | the extras are gone: twelve cards, twelve real slots, which is also what the page and the caption claim |
| trademarked billers, personal payee names, a live BIN prefix (r1) | fictional billers with distinct glyphs, initials-only payees, fully masked PAN, holder shown as a role |
| the wipe's SFX and `render_sync.json` still described the previous edit (r2) | the wipe's hits import `STEPS`/`BADGE_STEPS` from the scene, and both verification tools derive their anchors from the shot table |
| the spec claimed a 45f hold the pixels didn't have, and both checks passed (r2) | the digit locks moved a beat earlier (50f real), `check:still` derives its windows from the shot table and fails when a hold shrinks |
| audio peaked at +0.03 dBFS (r1) then had 0.34 dB headroom (r2) | BGM 0.28, hits re-balanced, delivered peak −0.57 dBFS |
| the two deliverables' video streams differed by 271 frames (r1) | the no-BGM version is muxed from the same encode — both files' video MD5 is identical |
| the wipe's first steps read as a redaction bar over the 8.88% headline (r2) | the block grows from the left edge |
| the lock page's new activity panel was crisp sub-floor type (r2) | declared texture with a defocus band |
| six near-empty frames at shot boundaries (r2 method, found by the new check) | the shots no longer fade to canvas before a hard cut |

## How the other requested repos were folded in

| Repo | What was taken |
|---|---|
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | the whole production method: 8-stage pipeline, shot recipe cards and their exact demo implementations, `PageCam`/`Caption`/`FlashCut` components, the audio library, the aesthetic case law, and the mandatory independent final review |
| [duolahypercho/gauntlet-loop](https://github.com/duolahypercho/gauntlet-loop) | its critic loop, retargeted from games to this film: a fresh-context sub-agent grades the *rendered frames* as a harsh critic and the loop repeats until it stops finding blockers. It is a game-first skill, so only the fan-out / blind-compare / harsh-critic method transfers — and it earned its place here: round 2 caught three defects the maker believed were fixed |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | the "lazy senior dev" ladder: reuse the skill's components verbatim instead of re-writing them, no framework around the timeline, no dependency Remotion/Playwright/ffmpeg-static didn't already cover (the capture script uses the installed Playwright rather than adding Puppeteer), dead assets and dead code deleted, and one runnable check left behind per piece of non-trivial logic — `check`, `check:blank`, `check:still`, `verify:beats` |
| [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | orchestration-workflow habits: a written plan before code, a task list kept current, small verifiable steps, and verification delegated to a separate agent instead of self-certifying |
