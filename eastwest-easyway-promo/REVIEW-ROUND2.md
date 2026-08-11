# REVIEW ROUND 2 — eastwest-easyway-promo.mp4

Independent reviewer, clean context, round 2. I did not make this film and I did not read the
maker's rationale beyond the list of claimed fixes. Every verdict below is backed by a frame I
looked at, a pixel measurement I ran, or a number out of `ffmpeg astats`. I re-measured from the
delivered MP4, not from the previous report.

**Subject:** 1495f / 49.83s / 30fps / 1920×1080. Both deliverables present.

**Verdict: NOT DELIVERABLE.**

- **4 of 9** claimed fixes VERIFIED (3, 4, 6, 9)
- **2 of 9** PARTIALLY FIXED (2, 8)
- **3 of 9** NOT FIXED (1, 5, 7)

Two of the three failures are the two defects round 1 said were *visible at normal playback speed
without frame stepping* — the blank hole at the wipe and the duplicated deck card. Neither was
closed: the blank hole **moved and got longer** (2 frames → 7 frames), and the duplicate is now
**more** obvious than the frame round 1 cited. On top of that, re-timing the wipe desynchronised
three of its five SFX cues and left `analysis/render_sync.json` describing a cue the film no longer
has, and the newly captured lock page added a fresh Q11 legibility violation.

Measurement method: frame numbers are absolute frames of the delivered MP4. Stillness and
"blankness" are mean absolute per-pixel luma difference / per-frame std at 160×90 greyscale over all
1495 decoded frames. Colours are sampled from decoded RGB24 of the delivered file. Text heights are
measured as dark-pixel band heights on the rendered 1920×1080 frame, per Q11's "measure the render,
not the fontSize".

---

## Part A — the nine claimed fixes, one by one

### 1. Blank frames at the step wipe — **NOT FIXED (regressed: 2 frames → 7)**

The overlap itself works, for the first half of the wipe. The wipe now starts at **f1263**
(`beats.ts` `wipe: shot(87, 90)`), and f1268 and f1277 both show the block growing over the live
8.88% frame. `npm run check` confirms `wipe: overlaps the outgoing shot by 15f (takeover)`.

But the wipe is 44f long and the shot it eats is still only 175f long, so the overlap covers steps
1–2 and **not** steps 3–4. `SceneRewards`' Sequence still ends at **f1277** (from 1103, duration
175). The block's third step (1440×360) fires at local 16 = **f1279** and full coverage at local 22 =
**f1285**. So:

| Frame | What is on screen | Measured |
|---|---|---|
| f1277 | odometer + 900×96 block | mean 225.8, std 46.7 |
| **f1278** | **empty off-white canvas + a 900×96 purple bar (4.2% of frame)** | mean 238.65, std 34.79 |
| **f1279–f1284** | **empty off-white canvas + a 1440×360 magenta bar (25% of frame)** | mean 201.02, std 77.48 |
| f1285 | full-frame magenta | mean 66.01, std 0.10 |

The measured mean/std match the arithmetic for "flat canvas #f7f5fa plus one block" to within 1 LSB
(predicted mean 237.7 / std 35.1 for f1278; 201.1 / 76.0 for f1279), which is what "the outgoing shot
is gone" looks like numerically. I looked at f1278 and f1279 and they are exactly that — a white
frame with a floating bar. **f1278–f1284 = 7 frames (0.23s) of 75–96% empty canvas mid-film**, where
round 1 had 2. There is no `FlashCut` on this boundary (`Main.tsx` puts flashes only on the deck,
transfers, bills, lock and rewards cuts), so nothing motivates the white.

**Fix:** the overlap has to cover the *whole* growth, not the first half. Either extend the rewards
Sequence to f1285 (`rewards: shot(76, 88)` → hold the scene one extra beat, or render `StepWipe` as
an overlay above it), or move full coverage to wipe-local ≤ 14 so it completes before f1277.

### 2. Badge lifetime / takeover hold — **PARTIALLY FIXED**

Verified from the frame-diff spikes (each hard step shows as a single-frame mad spike with 0.000
either side, which also confirms zero interpolation — the card's grammar):

| Event | Declared | Frame | mad spike |
|---|---|---|---|
| step 1 (300×96) | local 2 | f1265 | 2.341 |
| step 2 (900×96) | local 8 | f1271 | 4.676 |
| step 3 (1440×360) | local 16 | f1279 | 37.767 |
| step 4 (full) | local 22 | f1285 | 135.133 |
| badge 0.55 | local 26 | f1289 | 0.498 |
| badge 1.12 | local 34 | f1297 | 2.022 |
| badge 1.00 | local 42 | f1305 | 0.723 |

So: wipe **44f** ✓, jump gaps **6/8/6** (unequal) ✓, badge steps **8f** apart ✓ (floor 5f), badge
lifetime **18f** (f1289–f1306) vs 7f in round 1 ✓, and the magenta field does carry into the outro
(`fieldOut` f1307→f1325) ✓.

Two residuals:

- **The badge's settled pose lives 2 frames and then vanishes in one.** Scale reaches 1.0 at f1305,
  and the wipe Sequence ends at f1307, so the payoff pose of the 0.55→1.12→1 overshoot is on screen
  for **0.07s** before a hard cut. f1306 shows the badge; f1307 shows the same magenta field with no
  badge at all. The element does not exit, it disappears.
- **The solid-colour takeover is ~26f, not 30f.** Frame std: f1285–1288 = 0.10 (pure field),
  f1307 = 0.19, f1310 = 3.49, f1315 = 10.29 — by f1315 the app page is plainly readable through the
  wash. The card's floor is ≥30f of solid colour; the film has about 26.

### 3. Outro never held still — **VERIFIED**

`FREEZE = STAMP + 40` = local 83 = **f1390**, and that is exactly where the pixels stop moving:

```
f1388 mad=0.377   f1389 mad=0.401   f1390 mad=0.401
f1391 mad=0.008   f1392 mad=0.009  ...  f1483 mad=0.003
f1484 mad=6.461  (fade begins)
```

**f1391–f1483 = 93 consecutive frames at mad ≤ 0.011.** Round 1 measured 2183–2567 changed pixels
*every* frame from f1347 to f1483. I also ran the maker's own tool independently:
`node tools/still-check.mjs` reports `PASS shot 10 · sign-off hold: 55 frames, worst frame-to-frame
diff 0.004 (limit 1.2) at f1456` — matches the claimed 0.004. f1430 and f1470 are pixel-identical to
the eye. This is the cleanest fix in the round.

Bonus, unclaimed and also verified: shot 1's wordmark hold is now genuinely still too —
**f47–f76, 30 frames at mad ≤ 0.006** (round-1 defect 19: the blinking cursor broke it every ~4f).

### 4. "Active" + "LOCKED" / amber badge / toggle track — **VERIFIED**

**Badge opacity and the state contradiction.** Full-resolution crop of f1017 (the badge's first
visible frame — `locked` crosses 0.02 there): the pill is fully opaque lime and covers the entire
baked status field. Neither "STATUS" nor "Active" reads through. The card reads
`CARD HOLDER / EASYWAY USER · VALID THRU / 08 29 · [LOCKED]`. f0940 (before the lock) shows the
unlocked field `STATUS / Active`, so the swap is clean.

**Amber.** Badge centre sampled from decoded RGB: f1016 = RGB(138,26,116) (card), **f1017 =
RGB(183,194,70)** — hue ≈ 66°, i.e. lime; f1018 RGB(187,196,69); f1060 RGB(181,190,69). There is no
intermediate tan frame. Round 1 measured RGB(157,120,97) here.

**Toggle track vs knob.** Horizontal scan across the ATM toggle at y=178:

| Frame | track colour | knob position |
|---|---|---|
| f1016 | RGB(178,0,110) magenta | right (x1732–1750) |
| f1017 | RGB(201,104,171) | centre (x1720–1738) |
| f1018 | RGB(211,168,207) | left of centre |
| f1019 | RGB(220,199,224) | left (x1708–1726) |
| f1021 | RGB(221,214,233) = off `#ded7e8` | fully left |

The track interpolates in lockstep with the knob. There is no frame where they disagree.

Two notes that are not this defect but sit next to it:

- The LOCKED badge lands at f1017 while "Online purchases" and "In-store payments" stay fully ON
  until f1025 and f1029, so the card reads LOCKED over two enabled channels for ~12f. Defensible as
  a cause→effect cascade, but the order is backwards — the toggles should fall first, then the badge
  should land.
- The scan trail still resolves to a tan over the magenta card: **f0960 at (500,490) = RGB(189,145,95)**,
  hue 32°, sat 0.50. That is round-1 defect 15's second half, not one of the nine, and it is still open.

### 5. Undeclared missing inline digit roll — **NOT FIXED (still undeclared)**

The device is genuinely absent: `SceneTransfers.tsx` contains no `DigitReel`, and the panel is
measurably static (still runs f576–f635 and f657–f696, 60f and 40f at mad ≤ 0.6 — nothing in the
frame animates). At f0640 "AVAILABLE TO SEND TODAY ₱ 148,920.75" is baked texture.

But **nothing in the repo records the drop**, which was the actual defect (B4: "removed after the
storyboard was released with no recorded reason"):

- `DESIGN-SPEC.md` stage 2 still maps `data/odometer-digit-roll` **(inline amount)** to feature 3;
- the stage 3 storyboard row for shot 4 still reads "the ₱ amount rolls and locks on b40";
- `SceneTransfers.tsx`'s header says nothing about it;
- the "Deliberate rule deviations" list still has exactly three entries, none of them this.

Round 1 offered two acceptable outcomes — implement it, or amend the feature map, storyboard and
deviation list. Neither was done. Calling it "P4: the odometer owns that device" in a review reply is
not a declaration; it has to be in the written artefact the next reviewer reads.

**As requested, the spec/film contradictions this round created or left standing:**

| `DESIGN-SPEC.md` says | The film does |
|---|---|
| shot 9 = beats 88–91, f1278–1322 | beats 87–90, **f1263–1307** |
| shot 10 starts beat 91 / f1322 | beat **90 / f1307** |
| shot 4 has an inline digit roll on b40 | no digit roll at all |
| shot 5's line: "Pay every bill in one place." | "Pay every enrolled biller in one tap." (f0726) |
| shot 7's scan line: 2.5px | 3px (`LINE_H = 3`) |
| deviation #1: captions are 22px / 30px | `Caption.tsx` renders **56px** (measured 58px, f0400) |
| rest budget: 45f hold after the odometer locks | **38f** of actual stillness (see N9) |
| "the template's amber never appears" | true for the badge now; still tan at f0960 |

### 6. Real trademarks / PII as demo data — **VERIFIED**

- **Billers (f0880):** Metro Electric · City Water District · FibrOne Home · TelcoOne Postpaid ·
  EastWest Credit Card · Sunrise Life Insurance. Meralco, Maynilad, PLDT Home Fibr and Globe
  Postpaid are gone. The finale carries "Metro Electric" (f1430), so the recapture reached the outro
  cutouts too.
- **Payees (f0640):** "M. R. · savings", "My KOMO wallet", "A. S. · other bank", "L. G. · other
  bank", "Corner store · QR". No personal names anywhere in the list.
- **Card face (f1017 full-res crop):** PAN is `•••• •••• •••• 4821` — the `5412` BIN prefix is gone.
  CARD HOLDER reads **EASYWAY USER**, a role, not a name.

Residuals, both minor: `VALID THRU 08/29` still sits beside the last four (low risk now that the BIN
and holder name are gone); and "6 enrolled · due this week" now spans **Aug 14 – Aug 25 = 12 days**,
wider than the 9 days round 1 flagged.

### 7. Two copies of one card in one frame — **NOT FIXED**

The claimed geometric guarantee only constrains **landed** slots. The extras fly from the pile
(page y≈300) down to y=1878, and their flight paths pass straight through the window that also holds
their originals in row 1.

- **f0400:** two identical "Peso & foreign currency savings" cards — the settled one at row 1 col 1
  and the extra copy in flight at frame centre. Same title, same body, same DEPOSIT tag.
- **f0405:** two identical "Send money for free" cards, adjacent and at nearly the same size. This is
  more obvious than the round-1 evidence frame, not less.

The exposure window is roughly **f398–f414** (extras are k=12/13/14, cues 78.1 / 80.5 / 82.6 local,
12f flights, deck.from = 320). f0425 and f0440 are clean, which is why the *landed* reasoning looked
sound.

Two things underneath this:

- The code comment is now wrong in three places. `const N_CARDS = real.length + extras.length; // 24`
  evaluates to **15** (12 real + 3 extras, `EXTRA_ROWS = [1878]`). The header still says "24 EastWest
  feature cards (12 real + 12 extras…)" and "24 cards → an 84px pile" (15 × 3.5px = **52.5px**).
- The extras are literal re-renders of `card1/2/3`, so the settled board at **f0440** shows a fourth
  row that repeats row 1 verbatim, while the page header says "12 of 12 features shown" and the
  caption says "Twelve things you used to queue for". Fifteen cards, three exact repeats, on a board
  that claims twelve.

**Fix:** three distinct filler compositions for the extras (or delete the extra row and let twelve
cards be twelve), and route their flights in from below frame so no path crosses row 1.

The rest of the deal cadence is fine, and I checked it because the brief asked: `cue = 36 + 4.5k −
0.09k(k−1)` gives gaps of `4.5 − 0.18k` → **4.50 → 2.16f**, monotonically decreasing, so it still
accelerates (R2). Last card cues at local 82.6 and lands at 94.6, comfortably before the rest, and
the rest is real: **f423–f442, 20 frames at mad ≤ 0.6** (`check:still` worst 0.010 at f441).

### 8. Q11 legibility of the deck copy — **PARTIALLY FIXED**

Fixed and measured on the render:

| Element | Round 1 | Now | Floor |
|---|---|---|---|
| Narration caption (f0400) | 56px (already passing) | **58px band / 5.37% frame** | ≥56px / 5.2% ✓ |
| Outro tagline (f1430) | 30px | **44px** (code) | ≥32px ✓ |
| Outro source line | absent | **34px / 3.15%** | ≥32px ✓ |
| Deck chase / glide zoom | 0.72 | **0.95 / 1.15** | — ✓ |

Not fixed:

| Element | Measured | % frame | Floor |
|---|---|---|---|
| Deck card titles (f0440, zoom 0.95) | 21px | 1.94% | ≥32px / 3% ✗ |
| Deck card titles (f0470, zoom 1.15) | 25px | 2.31% | ✗ |
| Deck card body (f0470) | 16px | 1.48% | ✗ |
| Deck card tags | 9px | 0.83% | ✗ |
| Biller names (f0880) | 13–18px | 1.20–1.67% | ✗ |
| Biller detail lines (f0880) | 7–8px | 0.65–0.74% | ✗ |
| Opening kicker | 28px (`SceneOpen.tsx:318`, unchanged) | 2.6% | ✗ |
| Outro legal line | 24px on a dark field | 2.2% | ✗ |
| **Closing CTA / URL** | **still absent** | — | ✗ |

The zoom change bought a real 1.32× on the deck, and the captions now do their job — but the copy
that carries the six must-show features is still rendered crisp, dark and centre-frame at two-thirds
of the floor (titles) and half of it (body). Q11's forbidden middle state is narrower, not closed.

**And the added 34px line is not a CTA.** "Features documented at eastwestbanker.com/easyway-app" is
a source citation. Round-1 P1 ("the film has no call to action of any kind — no 'Download EasyWay',
no app-store cue") is unaddressed, and Q11 calls the closing CTA "the one line in the film that
should never be small". It is still not there at all.

**New in this round:** the re-captured lock page's "Recent card activity" panel is a fresh Q11
violation — see **N4**.

### 9. Audio peaked at −0.02 dBFS — **VERIFIED**

`ffmpeg -af astats` on the delivered files:

| File | Overall peak | Max level |
|---|---|---|
| `eastwest-easyway-promo.mp4` | **−0.3376 dBFS** | 0.961874 |
| `eastwest-easyway-promo-nobgm.mp4` | **−1.4646 dBFS** | 0.820508 |

Round 1: +0.0345 dBFS and +0.000085 dBFS. Located by 1-second window scan: the peak is in the
**45–46s** window = the finale impact at f1350 (45.00s). BGM is 0.30 in `Main.tsx` and the impact is
0.46 (was 0.6). The SFX-only bed in the finale is now −1.46 dBFS, where it used to hit 0.0.

Two bonuses I verified while I was in there, both unclaimed:

- `riser-cine` now carries `dur: 40` (from `SHOTS.outro.from + 8` = f1315, cut at f1355, peak at
  f1350 = the stamp). Round-1 defect 13 — it used to hold 0.0 dBFS for 25 frames past the stamp.
- **The two deliverables now share one video stream, bit-for-bit.**
  `ffmpeg -map 0:v -f md5` = `9a5e3945c9f3ead32a45529871f34a79` on *both* files. Round 1 found 271
  differing frames. A8 is now structurally satisfied.

One caveat: **0.34 dB is thin headroom.** Any downstream loudness normalisation or platform
re-encode can push it back over. Target ≥1 dB (BGM 0.27, or impact 0.42).

---

## Part B — new and regressed defects, prioritised

### Must fix

**N1 — The blank hole at the wipe moved instead of closing. (f1278–f1284)**
7 frames of 75–96% empty off-white canvas, up from 2 fully blank frames. Full evidence in claim 1.
*Fix:* extend the rewards Sequence to f1285, or bring full coverage forward to wipe-local ≤ 14.

**N2 — Two copies of the same deck card are still co-visible. (f0400, f0405)**
Full evidence in claim 7. *Fix:* three distinct filler compositions for the extras, and route their
flights in from below frame.

**N3 — Re-timing the wipe desynchronised its own SFX table, and `render_sync.json` now describes a
cue the film does not have.**
The picture steps at wipe-local **2 / 8 / 16 / 22** and the badge at **26**. The table in `Main.tsx`
still fires from the old 29f version — `transition-snap` at local 2 / 8 / **14**, `bass-hit-short` at
local **20** annotated "full-screen jump", `pop` at local **22** annotated "badge". After peak
pre-roll the audible onsets land at f1277 (jump is at f1279), f1283 (jump is at f1285) and f1286
(badge is at f1289): **2f, 2f and 3f early**, and every comment now names the wrong picture event.
The 2f misses are inside A3's 3-frame budget; the badge pop is at the limit.
Meanwhile `analysis/render_sync.json` — regenerated at the same timestamp as the render (03:25) —
still lists `"anchor": "shot 9 wipe", "beat": 88, "frame": 1278`, and still records
`"sweep pass 1" … "total_frames": 3.70`, **over A3's 3-frame budget** (round-1 defect 11, unfixed).
*Fix:* derive the five wipe cue offsets from `StepWipe`'s `stepVal` thresholds in the same commit
that changes them; re-run `verify:beats`; re-measure `data-scan.mp3`'s audible onset and re-pre-roll.

**N4 — The new "Recent card activity" panel is a fresh Q11 violation, on screen for the whole lock
shot. (f0929–f1103; measured at f1017)**
Row titles **24px / 2.22%** of frame height, detail lines **15px / 1.39%**, "Posted" 25px — all
crisp, dark, dead centre, against a floor of 32px / 3%. The panel occupies the bottom ~40% of the
frame for the shot's full 174 frames. Round 1 called page-copy legibility "the most systematic
failure in the film"; this round added 8 more lines of it.
*Fix:* either raise the panel's type to ≥32px on screen (larger design type, or camera zoom ~1.5 on
the panel for a beat) or declare it texture — blur/dim it the way Q11 requires — or cut it.

### Should fix

**N5 — The wipe's first two steps land across the 8.88% figure. (f1265–f1277)**
A 300×96 then 900×96 block appears dead centre, directly over the lime rule and between "8.88%" and
"cash reward on qualified card spend" (see f1268, f1277). For its first 6 frames it reads as a stray
rectangle or a redaction bar over the film's headline claim rather than the opening of a transition.
*Fix:* start the growth from an edge or corner (full-width band at y=0, or top-left), or make step 1
large enough that the intent is legible immediately.

**N6 — The lock shot's framing clips its own new content, for 162 frames. (f0929–f1103)**
Camera is pinned at cx930 / cy660 / zoom1.22 from local frame 12 to the end. At the top edge two
headless half-sentences collide — "goes missing — and switch it back on when it turns up." over
"…store payments the moment it" (f0940, f1017). At the bottom edge the activity panel's third row is
sliced in half (the ₱5,000.00 row). New page content was added without re-framing the shot.
*Fix:* cy ≈ 720 and zoom ≈ 1.12, or trim the page so the panel ends on a whole row.

**N7 — The EW badge is hard-cut out of existence at the shot boundary. (f1306 → f1307)**
Reaches its settled 1.0 pose at f1305, holds 2 frames, gone in one. *Fix:* extend the wipe Sequence
~12f and fade/scale the badge out under the field crossfade, or hand it to `SceneOutro`'s first
frames so it exits with the field.

**N8 — Six new places where the written record contradicts the code.**
`SceneDeck.tsx`: "24 EastWest feature cards (12 real + 12 extras)" and `// 24` (actual **15**);
"24 cards → an 84px pile" (actual **52.5px**); "the fastest chase leg is capped at ~38px/f" (the
fastest leg now measures **22.5px/f** page-space / 21.4px/f on screen — the number is stale in the
other direction now). `DESIGN-SPEC.md`: the full list is in claim 5's table (shot 9/10 beats and
frames, the digit roll, shot 5's line, shot 7's 2.5px, deviation #1's caption size).
This is the exact failure round 1 diagnosed as "the written record actively misleads the verification
step it was written to enable", reproduced inside the fix round. *Fix:* edit the comment and the
constant in the same commit; regenerate the deviation list and the storyboard table from the code.

**N9 — The two verification scripts now disagree with each other and with the spec, and both pass.**
The spec reserves "45f hold after the odometer locks". `check-timeline.mjs` certifies
`beatF(88) − beatF(84) = 58f ≥ 45f`. The pixels are still for **38f** (f1227–f1264 at mad ≤ 0.6),
because the wipe now starts eating the frame at f1263. And `still-check.mjs` checks a **30f** window
(f1232–f1261) with a hand-written comment explaining why it stops early. Three different numbers for
one hold; the two that are automated both pass.
`check-timeline.mjs` also carries `ok(from === cursor || from === beatF(87), …)` — a hard-coded
escape hatch that makes the no-gap assertion unfalsifiable for the wipe specifically.
*Fix:* derive the still window from the shot table (`beatF(84)` → `SHOTS.wipe.from`) and assert it
against the declared budget, so that shortening the hold fails the check instead of moving it.

**N10 — New copy repetition in the bills segment.**
f0726 title card "Pay every enrolled biller in **one tap**." → f0880 page headline "Every bill,
**one screen**." → f0876–f0926 caption "Six billers, **one screen**." Three sentences saying the same
thing in ~7 seconds, two of them sharing a phrase verbatim. F2 / C2. *Fix:* keep one; make the
caption carry something the page does not (e.g. "Due dates and amounts, already filled in").

**N11 — The caption pill still covers elements the audience has to see arrive.**
`Main.tsx` comment: "captions wait for the rows/list to finish landing, so the pill never sits on top
of an element the audience still has to see arrive." At **f0405** the pill sits over the deck's
bottom row while cards are still landing (caption f360–f418, last card lands f415). At **f0640** the
`bottom: 190` change moved the pill off row 5 and onto **row 4** — "L. G. · other bank / Other bank
•••• 3390 · s…" is cut mid-line for the caption's full 74 frames. Round-1 defect 26 relocated rather
than resolved.

### Low priority

**N12 — The outro wordmark overlaps the hero card. (f1430)** Full-res crop: the "E" of "EastWest"
(x≈426–500) sits on the hero card's magenta corner. It stays legible (white on magenta), but the
lockup is no longer clear of the cast, which is the point of a group photo. *Fix:* shift the hero
card ~90px left or drop the wordmark's `transformOrigin` a little.

**N13 — The outro's field handover shows a near-sharp repeat of the app page. (f1315)** `fieldOut`
runs 0→18f while `blur` runs 0→24f, so for ~15 frames the outro reads as the shot-1/shot-3 app page
under a flat magenta wash rather than a stage. It is also that page state's third appearance (P4
dedupe). *Fix:* front-load the blur (0→10f) so the page is already texture when the field lifts.

**N14 — Six identical featureless magenta tiles now stand in for the biller logos. (f0880)** The
rename removed the brand marks and left placeholder blobs, which reads as unfinished against Q10's
publication-grade bar. *Fix:* six distinct simple glyphs (bolt, droplet, wifi, phone, card, shield).

**N15 — Delegate imbalance persists in the group photo. (f1430)** "Transfers / send money" now has
three delegates (`card3` "Send money for free", `row1`, `float-sum`) while rewards has exactly one.
Round-1's specific complaint (rewards had none) is fixed; the imbalance is not.

**N16 — Reducing the hits flattened the finale's SFX peak.** In the SFX-only mix the finale impact
(t=44s, −1.46 dBFS) is now only **0.26 dB** above the card-lock cue (t=33s, −1.72 dBFS). The BGM is
at full energy there so the moment still lands, but there is almost no SFX-level separation left
between the film's biggest beat and its second-biggest.

### Carry-overs from round 1 that are still open (not among the nine, listed so they are not lost)

Opening kicker still 28px (`SceneOpen.tsx:318`) · off-token `#7b2079` still in `StepWipe.tsx:31` ·
orphaned top-edge half-sentences at f0148 / f0205 / f0640 · scan-trail tan RGB(189,145,95) at f0960 ·
`sweep pass 1` still 3.70 frames late · "due this week" now spans 12 days · **no CTA**.

### Round-1 defects I verified as genuinely fixed but which were not claimed

Shot 1's wordmark hold is now 30 truly static frames (f47–f76, mad ≤ 0.006; defect 19) · lightning
capped at 8 strikes with an enforced 9f minimum gap and life ≤ 4f, so two bolts can never coexist
(`Titles.tsx:61`; defect 14) · scan line 3px, trail 158px, 10px inset (defect 15) · the wordmark
accent is lime in both lockups (f1430; defect 22) · the outro tagline no longer repeats the opening
kicker (defect 18, partly) · the rewards feature has a delegate (defect 17) · `riser-cine` truncated
(defect 13) · the two deliverables share one video stream bit-for-bit (defect 32) · the outro is now
a dark-purple stage where the group photo, the stage light and the lime dust all read, and it is no
longer the film's calmest frame (defect 29 — this one is a real improvement, and f1352/f1430/f1470
all support it).

---

## Part C — the specific things the brief asked me to hunt for

**"Recent card activity" panel.** It is real, dense and native-looking (Q10 ✓), and it makes the lock
shot's page genuinely informative. But it is sub-floor type (N4) and the camera was not re-framed
around it, so it is clipped at the bottom edge while the page header is clipped at the top (N6).

**The outro's dark-purple stage.** The group photo reads clearly — light UI cards, lime dust and the
stage light all separate against the field, which is a straight win over the near-white version. Two
things do not read: the 24px "Unofficial concept film…" line at 62% white over the purple (~3.4:1,
6px at 480px wide), and the flown cards' body copy, which is crisp small text rather than declared
texture. The wordmark overlaps one card (N12).

**The deck's new deal cadence.** Sound. Gaps go 4.50 → 2.16f monotonically (`4.5 − 0.18k`), so it
still hard-accelerates; the last card cues at local 82.6 and lands at 94.6, before the rest begins at
local 104; and the rest is genuinely still — f423–f442, 20 frames at mad ≤ 0.6. The problem with the
15-card deck is not its rhythm, it is that three of the fifteen are duplicates (N2).

**The shortened wipe/odometer overlap.** It creates two collisions: the visible one is the block
landing across the 8.88% figure for its first 15 frames (N5), and the structural one is that the
overlap ends before the wipe does, which is N1.

---

## Part D — could not verify

1. **Anything subjective about the audio.** I measured peaks, per-second windows, cue offsets against
   picture events, and the SFX/BGM separation, but I cannot listen. S1's "close your eyes — launch
   or mobile game?" is unverified.
2. **Factual accuracy of the product claims.** No network access. 8.88%, "₱50,000 per InstaPay
   transfer" and the free-transfer scope are still asserted with no captured page or dated citation in
   the repo (round-1 D5, unchanged).
3. **Perceptual audibility of each cue under the bed** after the level reductions.
4. **Whether the re-captured pages were actually re-captured** rather than edited. `live-layout.json`
   grew a taller `cards.pageH` (1329) and a `status` box consistent with the new page, and the
   textures are on disk, but I did not re-run `tools/capture.mjs`.
5. **Render determinism.** I did not re-render. The bit-identical video streams prove the two
   deliverables came from one encode, not that a re-run would reproduce it.
6. **Frames I did not inspect.** I looked at 24 frames (16 from `out/review/`, 8 extracted myself:
   f405, f1277, f1278, f1279, f1306, f1308, f1390, f1470, plus four full-res crops) and measured all
   1495 numerically. Defects confined to unexamined frames could remain, particularly f0100–f0330 and
   f1120–f1210, which I only checked numerically.
7. **BGM licensing.**

---

## Bottom line

The three fixes that were pure engineering — the outro freeze, the badge/toggle state, the audio
ceiling — are done properly, and the data-safety pass is thorough and complete. The outro is a
genuinely better shot than it was.

The three that needed the maker to re-check the *rendered frames* after changing the timeline are the
three that failed. The blank hole was diagnosed correctly (the wipe must overlap) and then the
overlap was made too short to cover the wipe's own growth, so the hole moved from f1278–79 to
f1278–84 and got longer. The duplicate-card fix reasoned about landed positions and never looked at
the flight frames, where the duplicate is now more visible than the frame round 1 cited. And moving
the wipe left its SFX table, its `render_sync.json` row, its storyboard row and one of its two
automated checks all describing the previous cut.

That is the same three-part failure round 1 named — a check that cannot fail, a critic loop that
stopped early, a written record that drifted — and it recurred inside the round that was supposed to
fix it. **Do not ship.** N1–N4 are blockers; N1 and N2 are visible at normal playback speed.
