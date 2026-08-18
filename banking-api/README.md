# Milestone Case Study — Real-Time Banking Fraud & Analytics Engine

A FastAPI transaction-processing and fraud-detection service using AsyncIO for
outbound I/O, NumPy for the Z-score fraud check, and Pandas for account and
portfolio analytics.

Deliverables are at the repository root:

- `Banking-Fraud-Analytics-CaseStudy.docx`
- `Banking-Fraud-Analytics-CaseStudy.pdf`

20 pages, 22 figures. 17 tests pass.

## Reproducing it

```bash
python3 -m pytest                          # 17 tests
python3 scripts/capture_run.py             # replays the submitted session
python3 scripts/capture_startup_error.py   # the uvicorn error, and the fix
python3 scripts/capture_swagger.py         # Swagger UI, incl. a live execution
python3 scripts/measure.py                 # the three measurements (~2 min)
python3 scripts/make_figures.py            # results/ + app.py  ->  figures/
python3 build.py                           # -> .docx and .pdf
```

To run the service by hand:

```bash
uvicorn app:app --reload
```

`uvicorn` on its own exits with `Error: Missing argument 'APP'` — it needs the
`module:attribute` of the FastAPI instance to import.

## Layout

```
app.py                  the application, byte-for-byte as submitted
tests/                  17 tests pinning down actual behaviour
scripts/                capture and measurement scripts
screenshots/            screenshots from the development machine, unmodified
results/                captured output — the source for the terminal figures
figures/                every figure used in the document
content.py              the text of the case study
build.py                content.py + figures/  ->  .docx and .pdf
```

`app.py` is deliberately left exactly as submitted, since it is the artifact
under study. `scripts/seeded.py` imports it and pre-loads the in-memory table
for the scaling measurement rather than editing it.

Document writers and the figure renderer are imported from `todo-app/` (Day 3)
rather than copied.

## Evidence

Three figures are screenshots from the development machine, used as supplied:
the PowerShell session, the PyCharm window, and the pgAdmin `accounts` table.
`screenshots/` also holds the case-study document and the submission page, which
are not used in the write-up.

Everything else was captured by running the code again. `scripts/capture_run.py`
replays the four calls from the PowerShell screenshot and **asserts every value
matches** — the z-scores, the means, the deviations, the summary totals and the
portfolio figures — so the two sets of evidence are known to describe the same
behaviour. It fails loudly if they diverge.

## What the measurements found

| Claim | Result |
|---|---|
| `asyncio.gather` makes outbound calls concurrent | **Holds.** 451 ms → 150 ms for three 150 ms checks, a factor of 3.00 |
| The request path never blocks | **Does not hold.** 20 concurrent requests cost 591 ms against a 52 ms parallel prediction and a 667 ms serialised one |

The NumPy and Pandas work is called directly from `async def` handlers, so it
runs on the event loop and requests serialise. Combined with rebuilding a
DataFrame from the whole table on every request, single-worker throughput falls
from 42.1/s at seed size to 6.8/s at 200,000 rows — against a stated goal of
thousands per second.

## Principal finding

A transaction 40 standard deviations above the account's mean is flagged
(`is_anomaly: true`), an alert is dispatched, and the API still answers
`"status": "APPROVED"`. The status is a constant; nothing in the request path can
decline. `tests/test_behaviour.py::test_flagged_transaction_is_still_approved`
pins this down.

The full findings table, with severities and recommendations, is in the document.

## Notes

- Terminal figures use PowerShell prompts, matching the earlier submissions in
  this series.
- JSON bodies are indented and long PowerShell commands are wrapped onto
  backtick continuation lines: the API answers on one line, and the commands run
  past 200 characters. Both are disclosed in the document.
- The Swagger execution figure shows different portfolio numbers to the
  PowerShell session because it ran against a freshly restarted server holding
  only the seed data. That is the in-memory storage limitation, and the document
  treats it as one of the findings rather than a footnote.
