# FINAL REVIEW — eastwest-easyway-promo.mp4

Independent reviewer, clean context. I did not make this film. Graded against
`video-shotcraft/references/final-review.md` (P/F/V/S/B/D/A/Q) and
`references/aesthetic-rules.md` (R/Q/S/C/P), with the 10 claimed shot cards read in full.

**Subject:** 1495f / 49.83s / 30fps / 1920×1080, both deliverables present.
**Verdict:** the film is competent and in several places genuinely good (the odometer shot, the
hero-card sharpness, the deck's full-board rest, the beat grid). It is **not deliverable as-is.**
There are **4 hard picture defects** (a 2-frame blank hole, a 7-frame badge, a never-still outro,
a state contradiction on the film's security beat), **2 data/rights problems** (real third-party
brands, named payees), **one missing declared feature** (the inline digit roll), and a
**systematic legibility failure** on the copy that carries the must-show features.

Measurement method: frame numbers are absolute frames of the delivered MP4. Stillness is measured
as mean-squared luma difference between decoded frames downscaled to 480×270 (which doubles as
Q11's "shrink to 480px" test). Colours are sampled from the delivered frames, not from source code.

---

## Part A — final-review.md checklist

### P — product goal

- **P1 ✗ (f1420)** Positioning and audience are clear, and the value props are specific. But the
  film has **no call to action of any kind** — no "Download EasyWay", no app-store cue, no URL. A
  feature-showcase promo that never tells the viewer what to do next has an unfinished product goal,
  and Q11 names the closing CTA as "the one line in the film that should never be small."
- **P2 ✓** The energy arc does ride the declared RMS structure: brand + hero in the intro, the deck
  accelerating through the build, everything from the transfers shot at full energy. Verified against
  `analysis/beat_data.json` and the shot boundaries.
- **P3 ✓ (f1240)** Claims are hedged correctly on screen: "UP TO" is present above the 8.88%, and the
  label reads "cash reward on qualified card spend". Free transfers are scoped to "EastWest or KOMO",
  with InstaPay/PESONet named separately (f0470). No invented features. **One caveat**, see D5: the
  film cannot be checked against the public pages from this review, so the *accuracy* of 8.88% and
  "₱50,000 per transfer" is unverified.
- **P4 ✗ (f0523)** The decision table's execution choices are *mostly* traceable, but one is not
  delivered at all: the feature→shot map assigns `data/odometer-digit-roll` (inline amount) to
  feature 3, and the storyboard says "the ₱ amount rolls and locks on b40". The delivered transfers
  shot has no digit roll — the three amounts are baked into the page texture and never animate. See F1.

### F — feature completeness

- **F1 ✗ (f0523–f0697)** All six must-show features do appear somewhere, so nothing is missing
  outright — but feature 3's declared payoff is missing. The "amount rolls and locks on the kick"
  beat does not exist; the shot's only beat-40 event is a 3-frame panel press plus a lime bloom.
  The feature is carried entirely by static texture and a caption.
- **F2 ✗** Three separate repeats:
  - **f0262 / f0330 / f0470** — the savings copy is delivered three times in nine seconds: the title
    card ("Open a savings account in minutes." + "Peso and foreign currency, side by side."), then the
    top pile card ("Open a savings account in the app, then hold peso and foreign currency side by
    side."), then the same card again on the settled board.
  - **f0726 → f0876** — the title card says "Pay every enrolled biller in **one tap**." and the very
    next shot's caption says "Enrol once, then pay **in one tap**."
  - **f0070 → f1420** — the opening kicker "EASYWAY · DIGITAL BANKING" is the outro tagline verbatim.
    This is the exact 已知坑 written on the `outro-group-photo-launch` card.
- **F3 ✓ (f0470, f0840, f0960)** Page states genuinely teach. The settled board with "12 of 12 features
  shown", the enrolled-biller list with due dates and amounts, and the four usage toggles all read as
  real product states rather than decorative motion. This is a strength of the film.

### V — visual direction

- **V1 ✗ (f0070 vs f1420)** The wordmark changes token between the film's two brand moments.
  Sampled: opening "West" = RGB(213,222,83) = lime `#d5e04d`; outro "West" = RGB(178,0,106) = magenta
  `#b2006f`. R1's judgement makes both lockups the film's memory anchors; having the accent word swap
  colour family between them weakens the lock. Also `brand.ts` claims "everything … reuses these
  [tokens]", but `Titles.tsx` and `StepWipe.tsx` introduce five off-token colours: `#ff8ad0`,
  `#7b2fa8`, `#7b2079`, `rgba(216,60,190)`, `#ffd8f2`.
- **V2 ✓** Entrance/landing easings match the declared motion tokens. Spot-checked: hero rise on
  `bezier(0.2,1.25,0.3,1)`, deck settle on `bezier(0.3,0,0.25,1.15)`, outro fly-in on
  `bezier(0.34,1.4,0.44,1)` — all with y1 > 1, i.e. real overshoot, which is the thing the template's
  own source comment says the old curve got wrong. No linear motion found on any element.
- **V3 ✓** No drift to Ink Press, cyber-neon or any unrelated style. The film is consistently a
  light-field fintech promo with a purple/magenta brand bed.
- **V4 ✗ (f1017)** The forbidden amber does appear. Sampled at the LOCKED badge centre on the lock
  frame: **RGB(157,120,97)** — a desaturated tan/amber, not lime. Cause: the badge and ring fade in
  over 4 frames at low alpha over a magenta card, so lime × 25% alpha resolves to amber. The scan
  band's bottom-of-pass glow measures RGB(166,108,108) (f0960) — a muddy rose. The settled badge at
  f1060 measures RGB(202,221,55) = correct lime, so this is a 4-frame transient on the film's
  security beat, not a permanent skin error.

### S — shot cards

- **S1 ✗ (f0523)** Nine of the ten mapped cards are present and identifiable. The tenth —
  `data/odometer-digit-roll` as the inline amount in shot 4 — is absent. (The card's *other* use,
  full-screen in shot 8, is present and is the best-executed shot in the film.)
- **S2 — N/A.** The brief named cards, not `card · style` variants, so no `style-key` claim needs
  cross-checking. I did not verify the gallery `library.json` mapping; see "could not verify".
- **S3 ◐** Motion grammar is faithful in most shots (spotlight arc, deal cadence, row embed, list
  decoupling, odometer reels). Three grammars are broken, all in ways the code comments claim they
  were kept — see S4.
- **S4 ✗ — five cards' 命门/已知坑 violated, four of them with a code comment asserting the opposite:**

  | Card | Card's parameter | Delivered | Evidence |
  |---|---|---|---|
  | `gradient-word-sweep` | lightning "sparse, ≤2 on screen, >8f between strikes" | **4 simultaneous bolts**; 14 frames over the ceiling; **all 27 onset gaps are 1–5f**; 28 strikes in an 87f shot | f0270–f0287, peak f0281 (computed from the shipped mulberry32 seed) |
  | `gradient-word-sweep` | 4 glow layers at 0.55/0.55/0.62/0.72 | 3 text-shaped glow layers (0.55/0.62/0.72); the comment says "four glow layers at 0.55/0.62/0.72" — four layers, three numbers | `Titles.tsx` |
  | `scan-bracket-sweep` | light band 2.5px; **">4px reads as a mask edge, not light"**; trail = 46% of subject height | **LINE_H = 4.5px** (over the absolute ceiling, and the storyboard says 2.5px); TRAIL = 120px while the header comment claims 158px | f0944–f1016 |
  | `color-block-step-wipe` | **unequal** jump gaps 6–12f; badge steps ≥5f apart; ≥30f solid-colour takeover hold | gaps are exactly **6/6/6** (the header comment claims the unequal rule was kept, then says "4 jumps on 6f gaps"); badge steps 3f and 2f apart; **7f of badge life total** | f1280–f1306 |
  | `deck-deal-flyin` | ≥30px/f chase legs get `CameraMotionBlur` | header says "the fastest chase leg is capped at ~38px/f so the shot needs no motion-blur pass" — 38 ≥ 30 by its own number. (Screen-space is ~27px/f once zoom 0.72 is applied, so the *outcome* is probably fine; the *justification* is self-contradicting) | f0400–f0440 |
  | `outro-group-photo-launch` | every shown feature needs a delegate; outro tagline must not duplicate the lockup line | the 8.88% rewards feature has **no delegate**, while "Send money" has two (a quick-action chip and the "Send money for free" card); tagline duplicates the opening kicker | f1420 |

- **S5 ✗ (f0400)** Adaptation is mostly natural, but the extras break it: the code comment claims
  duplicates stay "at least 5 slots — more than a screen — apart". At f0400 the audience can see
  **two "Convert to installment" cards and two "Balance transfer" cards in the same frame.**
- **S6 — N/A.** No card in this film is flagged "reference only" or "no preview".

### B — storyboard consistency

- **B1 ✗** The delivered timeline and copy diverge from the signed-off storyboard in `DESIGN-SPEC.md`:
  - shot 9 is beats 88–90 / **29f**, storyboard says 88–91 / 44f;
  - shot 10 starts at beat 90 / **f1307**, storyboard says beat 91 / f1322;
  - shot 5's line is "Pay every enrolled biller in one tap.", storyboard says "Pay every bill in one place.";
  - shot 7's scan line is 4.5px, storyboard says 2.5px;
  - captions for shots 3, 4, 6 and 8 are all rewritten (shot 4 drops "InstaPay & PESONet", shot 8 drops "up to 8.88%"), and shot 3 gained a second caption.
- **B2 ✗ (f0640)** `Main.tsx` states "captions wait for the rows/list to finish landing, so the pill
  never sits on top of an element the audience still has to see arrive." The caption pill covers the
  fifth transfer row for its full 74 frames (f0593–f0667), hiding the QR InstaPay row's name and
  detail line. Same shape of problem at f1060: the caption "Switch it back on anytime" is on screen
  for 45 frames *before* the unlock actually happens and ends 11 frames after it starts.
- **B3 ✗** Measured stillness (mse of consecutive decoded frames at 480×270; 0.000 = still):

  | Hold | Declared / self-certified | **Measured** | Verdict |
  |---|---|---|---|
  | shot 1 wordmark | 30f ≥ 30f "PASS" | still runs of **~4f**, broken every ~4f by the blinking kicker cursor (f61→f62 mse 3.135, 50px; f74→f75 same) | **✗** |
  | shot 3 full board | 18f ≥ 15f "PASS" | **genuinely still f424–f442** (mse ≤ 0.004) | **✓** |
  | shot 8 odometer | 58f ≥ 45f "PASS" | **genuinely still f1245–f1276+** (mse ≤ 0.001) | **✓** |
  | shot 10 sign-off | 88f ≥ 30f "PASS" | **zero still frames**; 2183–2567 px change every frame from f1347 to f1483 (f1440→f1460 mse 71.3) | **✗** |

  Both failures are on the wordmark — the exact object R1's judgement singles out ("開頭和結尾的
  wordmark 各 hold 滿 1 秒"). Note that `npm run check` reports **PASS on all four**, because it
  measures cue-to-cue frame arithmetic rather than pixel stillness.
- **B4 ✗** Two elements were removed after the storyboard was released with no recorded reason: the
  inline digit roll (shot 4) and 15 frames of the chapter break (shot 9, 44f → 29f).

### D — data & asset safety

- **D1 ✗ (f0840)** The declared rule is "100% fictional demo data". The enrolled-biller list uses
  **four real, trademarked Philippine companies** — Meralco, Maynilad, PLDT Home Fibr, Globe Postpaid —
  each paired with a masked account number, an amount and a due date, inside a film that also carries
  EastWest's own marks and states it is unofficial and unaffiliated. Real brand names are not
  fictional data. Meralco recurs in the finale (f1352–f1495).
- **D2 ✗ (f0560, f0640, f0960)** Personal names on screen:
  - five named payees in the transfer list — Maria Reyes, "Komo Wallet — J. Dela Cruz", Andres Santos,
    Lorna Garcia, "Sari-sari ni Aling Nena" — each with a masked account and an amount;
  - the debit card face carries **CARD HOLDER JUAN DELA CRUZ, VALID THRU 08/29** and a card number
    shown as **first four + last four** ("5412 •••• •••• 4821"). `5412` is a live Mastercard BIN
    prefix; showing BIN + last four + expiry + holder together reproduces the shape of a real card
    face. Q1's case law is explicit on this point: "不要提到客户名字".
  - The data is clearly invented, but it is invented to *look* like customer data rather than
    de-identified. Maria Reyes also appears in the finale for the last 4.6 seconds.
- **D3 ✓** No reproduction of an existing page is attempted, so Q1's screenshot mandate does not
  bind. The hand-built UI clears Q10's quality bar comfortably — publication-grade native typography,
  real content density, complete layout furniture (nav, search, avatar, section headers, counters).
- **D4 ✗ (f1017)** One state contradiction: during the badge's 4-frame fade-in the baked "STATUS /
  Active" field reads through the semi-transparent LOCKED pill, so the card says **Active and LOCKED
  at the same time** on the film's security beat. Fonts, images and dynamic data are otherwise fully
  loaded everywhere. Minor: the biller panel says "6 enrolled · due this week" over dates spanning
  Aug 14–22 (nine days).
- **D5 ✗** Public claims (8.88%, ₱50,000 per InstaPay transfer, "free to EastWest and KOMO") are
  presented as facts sourced from public product pages, but there is no captured evidence in the repo
  — no fetched page, no dated citation, only prose links in `DESIGN-SPEC.md`. Combined with D1, the
  demo data does not have the reviewable public provenance D5 asks for.

### A — audio & rhythm

- **A1 ✓** `bgm-tech-house.mp3` at 0.34 with 1s/1.7s fades. Measured headroom: the BGM bed sits
  ~11.6 dB below full scale at source and is ducked to 0.34, and SFX cues at 0.3–0.6 read clearly
  above it in the no-BGM/BGM window comparison (t=21s: −91.0 dB no-BGM vs −8.7 dB with BGM confirms
  the bed is the only thing in that gap).
- **A2 ◐** 16 cues, every one pinned to `beatF(n)` or `SHOTS.x.from + offset`, every one annotated
  with its picture action, percussive cues pre-rolled by measured internal peak. This is a genuinely
  well-built table. Two misses: the scan cue (see A3) and the "Switch it back on anytime" caption/
  unlock offset (f1029 vs f1074).
- **A3 ✗ (f0944)** The project's own `analysis/render_sync.json` records **"sweep pass 1" at 3.75
  frames** of total offset — over A3's 3-frame budget — and it was shipped unaddressed. All 16 other
  anchors are inside 2.25 frames, most under 0.7. Separately, **two of the four declared slam anchors
  moved with no recorded reason**: the spec pins the card lock to **b68** (the single strongest kick
  in range) and the odometer's final lock to **b86**; the code pins them to **b70** (f1016) and **b84**
  (f1220), neither of which is in the declared top-8 kick list.
- **A4 ✓** The finale keeps the fixed phrase. Verified by measurement: riser-cine's swell peaks 35f
  after its start, impact-deep-whoosh peaks 19f after its start, and the cues are placed so **both
  peaks land on f1350** = beat 93; sparkle follows at f1375 on the rule. The card's 35-frame
  riser→impact gap is preserved in peak-to-peak terms.
- **A5 ✗** No sample in the library exceeds 5s, so the ">5s must be explicitly truncated" list does
  not bind, and the 90f default `durationInFrames` truncates everything. But **riser-cine holds
  0.0 dBFS from t=0 to t=2.0s** (measured per-0.5s: 0.0 / 0.0 / 0.0 / 0.0 / −7.9 / −14.5 / −20.5 …),
  so with no explicit `dur` it is still at **full level for 25 frames after the stamp it was building
  to**, and audible until f1405. That is the "sound still playing after the action ended" case.
- **A6 ✗ (f1329–f1359)** No under-recorded samples are used — every cue's source peak is ≥ −6.7 dB,
  and only sparkle is below −2 dB (it correctly gets 0.5). But the render is **over the ceiling**:
  `astats` reports peak **+0.0345 dBFS** on the BGM deliverable and **+0.000085 dBFS** on the no-BGM
  deliverable, both located in the 44–48s window — the finale impact. The SFX bed alone reaches
  0.0 dB there (measured on the no-BGM file), so the BGM pushes it over.
- **A7 ✓** No synthesised UI tones. `switch-click-quick.mp3` and `lock-quick.mp3` are real-object
  foley (Mixkit light-switch family), `marker-pen-line.mp3` is a real pen, `data-scan.mp3` is used as
  a machine process. None of the `ui-confirm-*` / `ui-*-tone` / `ui-notify-*` synthetic files appear.
  The vocabulary is whoosh / impact / riser / sparkle / transition plus foley, exactly as S1 asks.
- **A8 ◐** Both deliverables exist, both are 1495f / 1920×1080 / 30fps with identical audio duration,
  and the no-BGM version is confirmed to be the same timeline with the bed removed (a no-SFX gap
  measures −91.0 dB there vs −8.7 dB in the BGM version). **But they are two independent renders, not
  one render remuxed:** 271 video frames differ (f0550–f0696 and f0980–f1103). The differences are
  sub-perceptual re-encode noise — worst-case PSNR **49.03 dB** at f651 — so the *picture* matches,
  but "frame-identical" is not literally true and the render scripts (`render` / `render:nobgm`) make
  a real divergence possible on any future re-run.

### Q — visual technical quality

Full pass is in Part B. Headline: **Q2 ✓ (a real strength)**, **Q4 ✗**, **Q6 ✗**, **Q7 ✗**,
**Q8 ✗**, **Q11 ✗ (the most systematic problem in the film)**. Q1, Q3, Q5, Q9, Q10 pass.

---

## Part B — aesthetic-rules.md case law

### Rhythm

- **R1 ✗ (f1347–f1483, f0047–f0074)** Both wordmark holds fail; the two content holds pass. See B3
  for the measurements. The outro is the worse of the two: `pushT` interpolates the crane scale from
  frame 40 all the way to frame 188, so the composition is still growing when the fade starts. The
  spec explicitly congratulates itself on fixing exactly this in shot 1 ("the camera is pinned truly
  static after touchdown (R1 — no 2.6→2.58 tail drift)") and then commits it in shot 10.
- **R2 ✓ (f0424–f0442)** Speed comes from acceleration. The deal cadence
  `36 + 4k − 0.0792k(k−1)` shrinks gaps from 4f to 0.5f, the chase scroll speeds up each leg, the
  physical metaphor (dealing) is present, and the full board then **rests genuinely still for 18
  frames** — measured mse ≤ 0.004 across f424→f442. Nothing in the film moves at constant velocity.
- **R3 ✓** The opening arc runs lock (f114) → touchdown (f212) ≈ 98f ≈ 3.3s, over the 3s floor. The
  lock/unlock interaction plays at human speed (5 sweep passes over 2.4s, then a 2-second beat before
  the release). Hold/rest budget was reserved up front rather than retrofitted.

### Texture, camera, composition

- **Q1 ✓** Non-reproduction scenario, hand-built UI, then genuinely captured at 2× and driven as page
  texture. That is the case Q1's 2026-07-13 revision permits, and the quality bar is met. **But the
  data half of Q1 fails** — see D1/D2.
- **Q2 ✓ — best-executed technical item in the film (f0148, f0205).** Under a 0.78→1.9 push at
  rotY 34°, the hero card's "₱148,920.75", "Account •••• 4821" and "Peso & foreign currency in one
  place" all hold crisp glyph edges with no pixel blocking. The layout-scale CSS `zoom` path plus a
  4× element capture crossfaded in at f114–f120 does what the technique card promises. Checked at
  full resolution on f0148 and f0205; no resampling artefacts.
- **Q3 ✓** No handheld shake anywhere. All camera motion is keyframed `CamKey` interpolation. Checked
  f0148, f0400, f0560, f0960, f1420 — no unintended jitter.
- **Q4 ✗ (f0030, f1017, f1060)** Three separate problems:
  - **群发 glint (f0030):** every one of the eight wordmark glyphs gets its own sweeping glint bar at
    `delay + 12`. Two or three are visibly lit at once. This is precisely the per-element glint the
    case law rejected twice ("不需要每个卡片都闪烁一下"), just moved from cards to letters.
  - **Amber spill (f1017):** the lock badge and ring fade in at low alpha over magenta and resolve to
    RGB(157,120,97) — a cheap-looking amber glow on the film's key beat.
  - **Doubled frames (f1060):** the lime ring (inset −6, scaled 1.06→1) and the four L-brackets form
    two concentric lime outlines around the same card, overlapping at every corner. The ring measures
    RGB(235,231,211) — washed to cream against the white page, so it reads as clutter rather than
    emphasis. Asking the card's own question ("好看吗?") of f1017 and f1060: no.
  - Credit where due: the deck deliberately does **not** glint per card (f0400), and the row-embed
    seam is correctly clipped inside each row's 16px radius (f0560). Those are the right calls.
- **Q5 ✓ (f0148)** The opening gives one protagonist and one complete arc: spotlight roves through
  four waypoints, locks with a pool pulse, pushes in to a left-oblique, the card rises with overshoot,
  bobs, gets two beam laps, reseats with a press. Single subject, start-middle-end. Textbook.
- **Q6 ✗ (f0148, f0205, f0640)** Two composition faults:
  - **Orphaned half-sentences bleeding off the top edge.** At f0148/f0205 the top of frame reads
    "…o app." and "…bills, apply for a card and lock your plastic — without" — a sentence the viewer
    starts and cannot finish, on screen for ~4 seconds. Same at f0640: "PESONet, using an account
    number or a QR." floats headless at the top edge after its heading has scrolled off.
  - **f0330/f0322:** the pile occupies the upper-left third with 55% of the frame dead dark space.
  - Correct calls: the information-dense list shots stay near-frontal (rotX 6° at f0840, rotX 4° at
    f0960), which is exactly what Q6 demands after the global-tilt rollback; and the hero close-up is
    shot from the left side, not from below (f0148 — the left edge is the near edge), matching the
    card's "从左侧拍摄而不是从下方".
- **Q7 ✗ (f0322, f0330)** The object close-up misses two of its four required elements:
  - **The "brushed metal" is not brushed metal.** The two 100° `repeating-linear-gradient` layers
    cross-hatch under the orbit transform into what reads as dark **woven cloth**, and the 1px/2px
    stripe periods alias visibly — there is moiré across the whole frame at f0322. Brushed metal needs
    anisotropic parallel streaks; this is a weave.
  - **The stack has no perceptible volume.** 24 cards × 3.5px = 84px of z is present in the geometry,
    but 24 white cards with white edges and no per-layer edge shading merge into a slab: roughly five
    distinct card edges are countable at f0330. The card's requirement is 可感知 (perceptible) height.
  - The orbit itself and the pull-back-into-page handoff are correct.
- **Q8 ✗ (f1420, f1490)** The outro is the **calmest** frame in the film, not its peak. White field;
  20 lime dust particles at 2–3.5px and 0.16–0.41 opacity, which are effectively invisible against
  a near-white background (they were visible against the magenta at f1307 — the layer only reads
  during the field it was tuned on); stage light at ~0.2; nine static cards; and the film fades to
  off-white. Plus the group photo is **missing a delegate for the 8.88% rewards feature** while
  carrying two "Send money" delegates. Compare the energy of f0400 (deck) or f1240 (odometer) to
  f1420: the finale is a step down. The card's own 已知坑 predicts this ("初版收尾几乎总是偏保守").
- **Q9 ✓ (f0560, f0640, f0470)** Every flown element lands in a real layout slot. Transfer rows seat
  into the panel's row positions with a bottom-edge seam; the deck's 12 extras land in a genuinely
  extended paper region (`PAPER_EXT` grows the page to 2726px) rather than hovering; the biller rows
  occupy real list positions. Nothing is left floating above the page.
- **Q10 ✓ (f0470, f0840, f0960)** Mock content is publication-grade: native typography, full copy
  density, real section furniture (nav, search field, avatar, "12 of 12 features shown",
  "6 enrolled · due this week", "All amounts in PHP", per-row due dates and channel tags). Pause on
  any frame and it reads like a real product.
- **Q11 ✗ — the most systematic failure in the film.** Shrinking each frame to 480px wide:

  | Element | Size | % frame height | Floor | At 480px |
  |---|---|---|---|---|
  | Narration captions | 56px | 5.2% | ≥56px | **✓ 14px, readable** |
  | Title-card headlines | 92px | 8.5% | — | ✓ |
  | Odometer figure / label | 190 / 52px | — | — | ✓ |
  | Deck card titles (f0400/f0470) | ~19–24px | 1.8–2.2% | ≥32px | **✗ ~5px** |
  | Deck card body (f0400) | ~13px | 1.2% | ≥32px | **✗ ~3px** |
  | Biller / toggle / row copy | 14–22px | 1.3–2.0% | ≥32px | **✗ 4–5px** |
  | Opening kicker (f0070) | 28px | 2.6% | ≥32px | **✗ 7px** |
  | Outro tagline (f1420) | 30px | 2.8% | ≥32px | **✗ 7.5px** |
  | Outro legal line (f1420) | 22px | 2.0% | ≥32px | **✗ 5.5px** |
  | Closing CTA / URL | — | — | ≥32px | **✗ absent** |

  This is Q11's forbidden middle state, at scale: the copy that carries six of the must-show features
  is rendered crisp, dark and centre-frame — the audience is invited to read it — at a third of the
  legibility floor. It is not treated as texture (not blurred, not dimmed) and it does not meet the
  floor. The deck shot in particular asks the viewer to absorb twelve feature names in 6.8 seconds at
  ~19px. **Note the declared deviation is stale and points at the wrong element:** `DESIGN-SPEC.md`
  deviation #1 declares "Caption 22px" in its heading and "30px" in its body, but `Caption.tsx`
  actually renders **56px** and complies. The genuinely undersized text — kicker, outro tagline, legal
  line, and all page copy — is undeclared.

### Sound

- **S1 ✓** Film vocabulary throughout, real-object foley for the switches/marker/scanner, no game
  timbres, no synthesised UI tones, tech-house bed. See A7.
- **S2 ◐** The declarative frame-number table with per-cue action comments is exemplary, and the
  six-shot biller ladder does the anti-machine-gun work correctly: **0.40 → 0.37 → 0.34 → 0.31 →
  0.28 → 0.25** with intervals accelerating 10→10→11→10→11→10f. Deduction only for the two moved
  slam anchors (b68→b70, b86→b84) and the 3.75-frame scan miss.
- **S3 ✗** The table is written relatively so a re-time cannot desync it — good. But the film's own
  post-render verification caught a 3.75-frame miss and it shipped anyway, which is the "音画错位是
  交付前必查项" clause.
- **S4 ✗** Foley-first is respected (marker stroke gets a pen, switches get switch clicks, the scan
  gets a scanner). The failure is duration discipline: riser-cine has no explicit `dur` and holds
  full level 25 frames past its target.

### Copy

- **C1 ✗** No silent stretch over 3 seconds, and the outro is correctly caption-free. But the copy
  was **not** rewritten to match the final cut: four of the storyboard's captions were changed in
  ways that drop the specifics the shots exist to communicate ("InstaPay & PESONet" out of the
  transfers caption, "up to 8.88%" out of the rewards caption, "card applications" out of the deck
  caption), and one duplicates the adjacent title card word-for-word.
- **C2 ◐** Lines are concrete and name real features ("Open a savings account in minutes",
  "Free to EastWest & KOMO, 24/7", "Lock ATM, online and in-store"), with lead-in title cards before
  the bills and savings segments as the rule asks. Deduction for the "one tap" duplication and the
  missing CTA.
- **C3 — N/A.** No in-scene 3D annotation is attempted. The optional `hover-3d-annotation` technique
  on the spotlight card was not taken, which is a legitimate omission (it is marked 可选).

### Process

- **P1 ◐** Frames were self-checked — `out/qa/` holds 30 archived stills and `analysis/render_sync.json`
  is a real post-render verification. That is the right instinct. But the checks are **not pixel-level
  where it matters**: `npm run check` certifies four hold budgets by cue arithmetic and passes all
  four, while two of them are not still in the rendered pixels; and `render_sync.json` recorded a
  3.75-frame miss that was then not acted on. P1's clause is "必要时用像素级工具（两帧 diff）自证".
- **P2 ✓** The reference-material discipline is sound: each card was read in full, its exact demo
  implementation located, and per-shot adaptations recorded in the file headers. No global style
  command was applied across shots. The problem is not that adaptations happened — it is that four
  headers assert a parameter was kept when the code below them changed it.
- **P3 — N/A** for this review (no ambiguous feedback round to resolve).
- **P4 ✗** The feature checklist maps cleanly and no手法 is reused as protagonist. But dedupe was not
  run: three repeated messages (see F2) and a repeated page state — the hero balance card plus
  quick-action row appears in shot 1 (f0114–f0232) and again at the end of shot 3 (f0466–f0523).

---

## Part C — prioritised defects

### Must fix before delivery

| # | Frame | Defect | Concrete fix |
|---|---|---|---|
| 1 | **f1278–f1279** | **Two completely blank off-white frames.** `SceneRewards`' Sequence ends at f1277, so the step wipe grows on an empty canvas — the transition never eats the outgoing shot. Its whole premise ("色块吞屏", takeover) is broken and the audience sees a blank flash mid-film. | Extend the rewards Sequence to f1307 (or render `StepWipe` as an overlay above it) so the block steps over the live 8.88% frame. |
| 2 | **f1300–f1306** | **The EW badge lives 7 frames** and is at full size for 2 before being hard-cut at f1307. The card's ≥30f solid-colour takeover hold is arithmetically impossible inside a 29f shot. | Restore the storyboard's 3-beat wipe (b88→b91 = 44f), move the badge steps to gaps of 8/6f, and hold the magenta field ≥30f after full coverage. |
| 3 | **f1347–f1483** | **The outro never holds still.** `pushT` runs to the last frame, so 2183–2567 px change every frame; the film's closing brand moment has zero static frames. R1's central judgement. | Clamp `pushT` to `[40, STAMP+40]` and lock the transform for the final 60f; start the fade after 30 static frames. |
| 4 | **f1017–f1019** | **State contradiction on the security beat:** the semi-transparent LOCKED badge lets the baked "STATUS / Active" read through, so the card says Active and LOCKED at once — and the badge measures amber RGB(157,120,97), a forbidden colour. | Make the badge opaque from its first frame (animate scale/position only, not alpha) and lay an opaque canvas-coloured patch over the baked status field. Same for the ring. |
| 5 | **f1017** | **Impossible UI state:** toggle 1 shows a magenta (=on) track with the knob in the off position for ~2 frames, because the track colour flips on a `on > 0.5` boolean while the knob interpolates. | Interpolate the track colour from the same `on` value (`interpolateColors`). |
| 6 | **f0523–f0697** | **The declared inline odometer digit roll is absent.** The transfers amounts are baked texture; the storyboard's "the ₱ amount rolls and locks on b40" beat does not exist, and the removal is undeclared. | Either drive "AVAILABLE TO SEND TODAY" with the existing `DigitReel` so it locks on b40, or amend the feature→shot map, storyboard and deviation list to match what shipped. |
| 7 | **f0840–f0929, f1352+** | **Real third-party trademarks as demo data** (Meralco, Maynilad, PLDT Home Fibr, Globe Postpaid) in an unofficial, unaffiliated concept film, against the project's own "100% fictional" rule. | Rename to fictional billers — e.g. Metro Electric, City Water, FibrOne, TelcoOne — and re-capture the six biller cutouts. |
| 8 | **f0560–f0697, f0960, f1352+** | **Named payees and a card-face identity.** Five personal names in the transfer list, plus CARD HOLDER JUAN DELA CRUZ with a live BIN prefix (5412) + last four + expiry. Q1's case law: "不要提到客户名字". | Replace payee names with initials/relationship labels ("MR · EastWest Savings ••7714", "My KOMO wallet"); mask the card to `•••• •••• •••• 4821` and set the holder line to a role placeholder. |
| 9 | **f0400, f0470, f0070, f1420** | **Q11 legibility, systematically.** The copy carrying six must-show features runs 13–24px (1.2–2.2% of frame height, floor 32px); kicker 28px; outro tagline 30px; legal line 22px; and there is **no CTA/URL at all**. | Add a 56px caption naming each feature group as it deals; raise the kicker to 34px and the outro tagline to 40px; add a 40px CTA line; either blur/dim the deck body copy to declare it texture, or drop it. |

### Should fix

| # | Frame | Defect | Fix |
|---|---|---|---|
| 10 | f1016, f1220 | Two of the four declared slam anchors moved off the strongest kicks (b68→b70, b86→b84) with no recorded reason — the card lock, the film's biggest interaction, lost the single strongest kick in range. | Re-pin the lock to b68 and the odometer's final lock to b86, or record the change and its reason. |
| 11 | f0944 | `render_sync.json` records the scan cue **3.75 frames** late — over A3's 3-frame budget — and it shipped. | Re-measure `data-scan.mp3`'s audible onset (the 123ms figure in the comment does not match the +115.8ms residual) and re-pre-roll. |
| 12 | f1329–f1359 | Render peaks **+0.0345 dBFS** (BGM) / +0.000085 (no-BGM). The SFX bed alone hits 0.0 dB. | Duck BGM to 0.26–0.28 under the finale, or impact 0.6→0.5; re-verify with `astats` peak < −0.3 dBFS. |
| 13 | f1350–f1405 | `riser-cine` has no `dur`; it holds 0.0 dBFS for 25 frames past the stamp and is audible for 55. | `dur: 36`, or a 6f fade after its peak. |
| 14 | f0270–f0287 | Lightning is 5–10× the card's density: 4 simultaneous bolts (ceiling 2), 14 frames over, all 27 onset gaps 1–5f (floor 8f). | Cut `FLASHES` from 30 to ~8 and enforce a ≥9f minimum gap. |
| 15 | f0944–f1016 | Scan line 4.5px exceeds the card's absolute ">4px reads as a mask edge" ceiling and contradicts the storyboard's 2.5px; trail 120px vs the header's claimed 158px; the line's turn-around sits exactly on the card's bottom edge, where its glow degenerates into a rose edge-highlight (RGB 166,108,108 at f0960). | Line to 3px, trail to 158px, inset the pass extremes ~10px from the edges. |
| 16 | f1280–f1305 | Wipe jump gaps are exactly 6/6/6 (equal — the card's "equal gaps read as a dropped-frame GIF"), badge steps 3f/2f apart (floor 5f) — while the header comment claims the unequal-gap rule was kept. | Gaps of 6/9/7/12; badge steps 8f apart. |
| 17 | f1420 | Group photo has no delegate for the 8.88% rewards feature; "Send money" has two. | Swap the "Send money" quick-action chip for an 8.88% rewards element. |
| 18 | f0070/f1420, f0726/f0876, f0262/f0330/f0470 | Three duplicated messages, one of them the exact 已知坑 written on the outro card. | Rewrite the outro tagline; change one of the two "one tap" lines; cut the savings copy to one instance. |
| 19 | f0047–f0074 | Shot 1's wordmark "hold" is broken every ~4 frames by the blinking kicker cursor; longest still run ~4f against a 30f requirement. | Stop the cursor at the end of the typewriter (f46) and hold 30 truly static frames before the dissolve. |
| 20 | f0400 | Two "Convert to installment" and two "Balance transfer" cards visible in the same frame, contradicting the code's own "≥5 slots apart" claim. | Re-offset the extras rotation, or use 12 distinct filler compositions. |
| 21 | f0322, f0330 | "Brushed metal" reads as dark woven cloth with visible moiré; the 24-card pile reads as ~5 cards. | Single-direction streaks at a coarser period with per-layer edge shading on the stack; add a 1px inner shadow per card so the layers separate. |
| 22 | f0070 vs f1420 | Wordmark accent word changes token: lime RGB(213,222,83) → magenta RGB(178,0,106). | Pick one accent for both lockups. |
| 23 | f0262, f1290 | Five off-token colours in the title cards and wipe, against `brand.ts`'s own claim. | Derive the bolt/gradient stops from the three brand tokens. |
| 24 | f0030 | Per-glyph glint on all eight wordmark letters = the 群发 glint rejected twice in the case law. | One glint across the settled wordmark, or none. |
| 25 | — | Delivered timeline and copy diverge from the signed-off storyboard in six places (see B1). | Reconcile `DESIGN-SPEC.md` with what shipped, or restore the storyboard. |
| 26 | f0640 | Caption pill covers the fifth transfer row for 74 frames, against the code's own comment. | Raise `bottom` to 190 for that caption, or move it to f0668. |
| 27 | f0148, f0205, f0640 | Orphaned half-sentences bleeding off the top edge for ~4s. | Shift `cy` ~40px so the headline is either fully in or fully out. |
| 28 | f1060 | Lock ring + four L-brackets = two concentric lime outlines; the ring washes to cream RGB(235,231,211) against the page. | Fade the brackets out as the ring lands, and give the ring a scrim. |
| 29 | f1420, f1490 | The outro is the film's lowest-energy frame, not its peak; lime dust is invisible on a near-white field; ends on a fade to off-white. | Keep the magenta/purple field behind the group photo, switch dust to a colour with contrast, raise the stage light, add the CTA. |
| 30 | — | `npm run check` certifies four hold budgets and passes all four; two are not still in the rendered pixels. | Assert stillness with a two-frame pixel diff on the rendered MP4 (mse < 0.01 at 480×270), not with cue arithmetic. |
| 31 | — | `DESIGN-SPEC.md` deviation #1 is stale (claims captions are 22/30px; they are 56px) and the genuinely sub-floor text is undeclared. | Rewrite the deviation list to describe what actually ships. |
| 32 | f0550–f0696, f0980–f1103 | The two deliverables are independent renders; 271 frames differ (min PSNR 49.03 dB — sub-perceptual, but not bit-identical). | Render once, then remux with/without the BGM stem so A8's "same timeline" is structurally guaranteed. |

---

## Part D — could not verify (explicitly)

1. **Anything subjective about the audio.** I measured provenance, source peaks, render peaks,
   per-window levels, envelope shapes and cue alignment, but I cannot listen. S1's core self-check
   ("close your eyes — does it sound like a product launch or a mobile game?") is **unverified**.
2. **Factual accuracy of the product claims (P3/D5).** No network access from this review, so I could
   not check 8.88%, "₱50,000 per InstaPay transfer" or the free-transfer scope against EastWest's
   public pages. The repo contains no captured page or dated citation — only prose links.
3. **Provenance of the brand tokens.** `brand/tokens-raw.json` exists and the film's colours match it
   exactly, but I could not confirm those values were actually extracted from `eastwestbanker.com`
   rather than authored.
4. **Line-by-line fidelity to the six demo implementations.** All cited demo and template sources
   exist in the skill repo. I graded against each card document's parameter table and 已知坑 and
   spot-checked the implementation, but I did **not** diff the six demo TSX files line by line, so
   S3-level deviations subtler than the parameter tables may remain.
5. **Gallery reference stills / `library.json` / `style-key` mapping (S2).** Not cross-checked. The
   brief named cards rather than `card · style` variants, so S2 is largely N/A, but I cannot certify
   the mapping.
6. **Render determinism.** I did not re-render. The 271 differing frames between deliverables are
   consistent with two independent encode runs, but I cannot separate "two runs" from "non-deterministic
   render" from the artefacts alone.
7. **BGM licensing** for this use.
8. **Perceptual SFX audibility under the bed (A6, second half).** I confirmed no under-recorded
   samples are used and measured levels, but not whether each cue is actually discernible on playback.
9. **Frames I did not inspect.** I read 27 frames at full resolution (the 19 mandated plus f0060,
   f0070, f0281, f0322, f1240, f1278, f1280, f1306, f1307) and measured 60+ more numerically. Defects
   confined to unexamined frames could remain, particularly in f0700–f0790 and f1090–f1105.

---

## Part E — what I checked and found genuinely clean

Stated with the evidence, so these are not blanket passes:

- **Text sharpness under the 2.5D push (Q2).** Inspected f0148 and f0205 at full resolution under a
  0.78→1.9 zoom at rotY 34°. Glyph edges on the balance figure, the masked account line and the body
  copy are clean — no pixel blocking, no resampling mush. The layout-scale `zoom` + 4× element
  capture + 6f crossfade chain works as designed. This is the film's strongest technical result.
- **Camera stability (Q3).** No handheld noise anywhere; all motion is keyframed. Checked on five
  frames across five different shots.
- **The deck's rest beat (R2).** Measured genuinely still for 18 frames, f0424–f0442, mse ≤ 0.004.
- **The odometer's hold (R1).** Measured genuinely still f1245–f1276+, mse ≤ 0.001. The shot also
  keeps the card's mechanical grammar intact: real digit places, half-row overshoot, left-to-right
  locking, speed-gated afterimages dropped on stop, deepening pulse with a 1.035 scale, and a
  correctly hedged "UP TO … qualified card spend". **The best shot in the film.**
- **Landing physics (V2).** Every landing curve has y1 > 1 (real overshoot); no linear motion found
  on any element in any shot.
- **Embedding (Q9).** All flown elements land in real layout slots; the deck's 12 extras land on a
  genuinely extended page (`PAPER_EXT` to 2726px), not on void.
- **Mock content quality (Q10).** Native typography, real density, complete layout furniture on all
  four page types. Pause anywhere and it reads as a real product.
- **SFX vocabulary and timbre (A7/S1).** No synthetic UI tones; real-object foley for switches,
  marker and scanner; the six-shot biller ladder does 0.40→0.25 with accelerating intervals exactly
  as S2 prescribes.
- **The finale's three-beat phrase (A4).** Measured: the riser's swell peak and the impact's peak
  both land on f1350 = beat 93, with sparkle on the rule at f1375. The card's 35-frame relationship
  is preserved in peak-to-peak terms — this was done carefully.
- **Beat grid integrity.** 124.00 BPM, T = 0.4838905s, residual 7.6ms, phase locked to kick
  transients; every shot boundary lands within 0.01–0.6 frames of its beat (15 of 17 anchors under
  0.7 frames); every SFX cue is written relatively so a re-time cannot desync the table. The grid
  work is the most rigorous part of the project.
- **No amber elsewhere.** Apart from the f1017 fade-in artefact, I found no stray amber, and no
  stray blue anywhere in the film.


---

## Appendix — the three requested repos, applied as review lenses

`DESIGN-SPEC.md` claims contributions from three repos. As the independent reviewer I did two things
with them: **audited whether the claims are true**, and **used each repo's own method as an extra lens
on the film**. Findings below are additive to Parts A–C.

### 1. `duolahypercho/gauntlet-loop` — claim: "its critic loop, retargeted from games to this film"

**Claim audit: accurate but the loop did not terminate correctly.** The repo is a pure-prompt GAME
skill (Matt Shumer's Call-of-Duty aim prompt as one command; explicitly "no harness, no state machine,
no helper scripts"). Its transferable method is exactly what the spec says it took: build against a
**named reference**, **fan out**, use a **separate harsh critic**, **blind-compare to the reference**,
and **"keep going until the human stops you."**

**Applied as a lens — the loop's own exit condition was not met.** Its stopping rule is that the harsh
critic stops finding gaps. I am that critic, running fresh, and the first pass found nine must-fix
items including two that are visible at normal playback speed without any frame stepping (the 2-frame
blank at f1278 and the 7-frame badge at f1300). A critic loop that terminated with those in the cut
either was not run to convergence or was not run against rendered frames.

**Blind-compare against the named reference (the skill's own template promo), applied:**

| Reference behaviour | This film |
|---|---|
| riser peaks **on** the impact (template f945 → f980, 35f gap) | **kept** — both peaks land on f1350 ✓ |
| 30f sign-off hold, camera locked (`template/src/aifl/Main.tsx`) | **broken** — camera pushes to f1483, zero static frames ✗ |
| `click-camera.mp3` at 0.6 = loudest cue, real shutter foley | **kept in spirit** — impact at 0.6 is the loudest cue, real foley throughout ✓ |
| reseat locks `cx/cy/zoom/rot` for ≥15f | **kept** — shot 1 camera is pinned f130→f232 ✓ |
| amber accent | **replaced** with lime, as intended — except for the f1017 fade artefact ✗ |

So the film is faithful to the reference where the reference is *audio*, and diverges where the
reference is *stillness*. That is a consistent signature: this production's weakness is holds.

### 2. `DietrichGebert/ponytail` — claim: "lazy senior dev ladder … one runnable check left behind"

**Claim audit: largely true, with two exceptions.** Verified: the skill's components are reused rather
than rewritten (`PageCam.tsx`, `Caption.tsx`, `FlashCut.tsx` are copied in with origin comments); there
is no framework around the timeline; `package.json` adds **no dependency** beyond Remotion, Playwright
and ffmpeg-static; and `npm run check` exists and runs. **Exception 1:** the check is green while
certifying two hold budgets the film misses (defect 30) — a check that cannot fail on the thing it
guards is worse than no check, because it manufactures confidence. **Exception 2:** the film is not
"lazy" about assets — 2.3 MB of captured material ships unused.

**`ponytail-audit` pass, in the repo's own format** (`tag: what to cut. replacement.`). False positives
excluded: `card2–12`, `biller2–6` and `row2–5` *are* referenced, via template-string paths.

```
delete: plastic-hires.png (1.4 MB) captured at 4x and never rendered.  Nothing — or better, USE it:
        shot 7's protagonist currently runs on the 2x page texture alone.   [public/textures/live/]
delete: transfers-full.png + bills-full.png (852 KB) — both scenes use the -empty plate + cutouts.
        Nothing.                                                            [public/textures/live/]
delete: ctl1–ctl4.png (64 KB) — SceneCardLock reads ctls[] for coordinates only and draws its own
        <Switch>; the toggles come from the baked cards-full.png. Nothing.  [public/textures/live/]
delete: float-search.png (28 KB) — in live-layout.json cutouts, rendered nowhere. Nothing.
delete: click-camera.mp3, switch-light.mp3, impact-zoom-quick.mp3 — not in the SFX table.  Nothing.
delete: <AbsoluteFill background:CANVAS opacity:0/> — a fully invisible layer.  Nothing.
        [src/ew/scenes/SceneOutro.tsx:292]
native: transition:'none' — CSS transitions never run in a frame-by-frame render.  Nothing.
        [src/ew/scenes/SceneCardLock.tsx:63]
delete: borderTop:`0px solid ${LINE}` — a zero-width border.  Nothing.  [src/ew/scenes/SceneOpen.tsx:352]
delete: ENTER_MS = 24 — exported as the declared "main entrance duration" motion token, zero
        references. Either apply it or drop the token from the spec table.   [src/ew/brand.ts]
shrink: FLICKER[] holds 200 random values; one is read per frame across an 87f shot.  Length 90.
        [src/ew/scenes/Titles.tsx]
net: ~2.3 MB of shipped assets and ~12 lines removable, 0 deps.
```

The `ENTER_MS` finding crosses into **V2**: the spec's motion-token table publishes "Main entrance
duration 24f" as a decision, and no code reads it. The measured curves pass anyway, so this is a
documentation defect, not a motion defect.

### 3. `shanraisshan/claude-code-best-practice` — claim: "written plan before code, task list kept current, small verifiable steps, verification delegated to a separate agent"

**Claim audit: three of four are demonstrably true; one is where the process broke.** True: there is a
written plan before code (`DESIGN-SPEC.md`, stages 0–7 with a decision table); the steps are small and
individually verifiable (per-shot files, each with a header naming its card and its kept parameters);
and verification is genuinely delegated rather than self-certified — this review exists because the
pipeline mandates it.

**Where it broke — the habit that was skipped is "keep the written artefact current":** four scene
headers assert a card parameter was kept while the code below them changed it (scan line 4.5px vs the
storyboard's 2.5px and the trail's claimed 158px vs the actual 120px; "unequal jump gaps … kept" above
gaps of 6/6/6; "sparse lightning … kept verbatim" above 4-simultaneous-bolt density; "38px/f so no
motion-blur pass is needed" against a ≥30px/f rule), the deviation list describes a caption size that
no longer exists, and the storyboard describes a timeline the film does not have. For a reviewer this
is the most expensive class of defect in the project: **the written record actively misleads the
verification step it was written to enable.** Under this repo's own orchestration habit the fix is
mechanical — the header comment and the constant must be edited in the same commit, and the
deviation list regenerated from the code rather than maintained by hand.

**Net effect of the three lenses:** they do not change the verdict, and they surface no new *picture*
defect. What they add is the diagnosis of *why* the defects survived to delivery: a self-check that
cannot fail (ponytail), a critic loop that stopped early (gauntlet-loop), and a written record that
drifted out of sync with the code it describes (best-practice). Fixing those three is what stops the
next cut shipping with a blank frame in it.
