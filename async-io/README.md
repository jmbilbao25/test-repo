# Async IO in Python

Day 4 assignment. The write-up is **[Async-IO-Assignment.docx](../Async-IO-Assignment.docx)**,
with a **[PDF copy](../Async-IO-Assignment.pdf)**.

Three scripts, all against `jsonplaceholder.typicode.com` (no API key needed).

| Script | What it does |
| --- | --- |
| `async_fetch.py` | The assignment: `fetch_data` plus `main`, five endpoints via `asyncio.gather` |
| `compare.py` | The same requests sequentially and then concurrently, so the benefit is measured |
| `errors.py` | A deliberately broken batch, with and without `return_exceptions=True` |

```bash
pip install aiohttp
python3 async_fetch.py
python3 compare.py
python3 errors.py
```

## Results

20 requests, one after another against all at once: **0.18s to 0.04s, 5.1x
faster**. Almost none of that time is Python working, it is waiting on the
network, and concurrently the waits overlap instead of adding up.

The error run is the more useful one. `asyncio.gather` stops at the first
exception and throws away the responses that already arrived; with
`return_exceptions=True` every slot comes back holding either data or the
exception, so 2 successes and 3 failures (404, DNS failure, timeout) all get
reported.

## Rebuilding the write-up

```bash
python3 async_fetch.py > results/async_fetch.txt
python3 compare.py     > results/compare.txt
python3 errors.py      > results/errors.txt

python3 scripts/make_figures.py   # code and terminal figures
python3 build.py                  # writes the .docx and the .pdf
```

`content.py` holds the text and is rendered to both formats, so they cannot drift
apart. The timings in the prose are parsed out of `results/compare.txt`, the same
file the figure is built from. The rendering helpers and the two writers are the
ones from `../todo-app/` and are imported rather than copied.

All four figures are real: the code figure is read out of `async_fetch.py`, and
the three terminal figures are the actual output of the scripts.
