# Assignments

| Day | Assignment | Write-up | Project |
| --- | --- | --- | --- |
| 2 | JVM tuning and Spring Boot microservice performance | [docx](JVM-Tuning-Assignment.docx) · [pdf](JVM-Tuning-Assignment.pdf) | [`itemservice/`](itemservice) |
| 3 | A to-do list app built with Copilot, ChatGPT and CodeWhisperer | [docx](AI-Tools-ToDo-Assignment.docx) · [pdf](AI-Tools-ToDo-Assignment.pdf) | [`todo-app/`](todo-app) |
| 4 | Async IO in Python: fetching several APIs at once | [docx](Async-IO-Assignment.docx) · [pdf](Async-IO-Assignment.pdf) | [`async-io/`](async-io) |

---

# Day 2: JVM Tuning and Spring Boot Microservice Performance

The write-up is **[JVM-Tuning-Assignment.docx](JVM-Tuning-Assignment.docx)**,
with a **[PDF copy](JVM-Tuning-Assignment.pdf)** for easier viewing.

## What is here

| Path | What it is |
| --- | --- |
| `JVM-Tuning-Assignment.docx` | The assignment write-up to submit |
| `JVM-Tuning-Assignment.pdf` | PDF version of the same document |
| `itemservice/` | The Spring Boot microservice (Java 21, Boot 3.4.1) |
| `figures/` | The VisualVM screenshots used in the write-up |
| `loadtest.py` | Load generator used to produce the measurements |
| `benchmark.sh` | Runs the service under a set of JVM flags and reports results |
| `results/` | GC logs and raw numbers from each run |
| `make_docx.py` | Script that generates the .docx |

## The service

One REST endpoint that returns a JSON list of items. The list is rebuilt on every
request on purpose, so there is real allocation pressure to observe in VisualVM.

```
GET http://localhost:8085/api/items?count=5000
```

Build and run:

```bash
cd itemservice
mvn package -DskipTests
java -jar target/itemservice-0.0.1-SNAPSHOT.jar
```

## Reproducing the measurements

```bash
./benchmark.sh baseline -Xms64m -Xmx128m -XX:+UseSerialGC
./benchmark.sh tuned    -Xms512m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=100
```

## Results

Load test with VisualVM detached: 1,200 requests, 16 concurrent, 25,000 items per request.

| Measurement | Before | After | Change |
| --- | --- | --- | --- |
| Requests per second | 103.0 | 173.5 | 68% faster |
| Average response time | 155.0 ms | 92.0 ms | 41% lower |
| p95 response time | 287.7 ms | 115.3 ms | 60% lower |
| Collections | 369 | 32 | 91% fewer |
| Full GCs | 76 | 0 | eliminated |
| Total stop-the-world pause | 9,812 ms | 191 ms | 98% lower |

Monitored sessions with VisualVM attached, about 2.5 minutes of sustained load each:

| | Baseline | Tuned |
| --- | --- | --- |
| Max heap | 128 MB | 512 MB |
| GC activity (VisualVM) | 7.2% | 0.1% |
| Collections | 3,137 | 458 |
| Full GCs | 695 | 0 |
| Stop-the-world pause | 95.5 s | 2.3 s |
| Pause share, busiest 10 s | 68% | 3% |

Under a lighter load the same change made no throughput difference at all, which is
covered in the write-up.

## Counting GC pauses correctly

Two things are easy to get wrong when reading the GC log, and both are discussed in
the document:

- Match on `Pause` when summing. G1 also logs concurrent phases, and those do not
  freeze the application, so including them overstates the pause total.
- Divide by the span the log actually covers, not just the measured phase, otherwise
  the pause percentage comes out too high.

```bash
grep -c 'Pause Young\|Pause Full' results/heavy-baseline-gc.log
grep -oP 'Pause (Young|Full).*?\K\d+\.\d+(?=ms)' results/heavy-baseline-gc.log \
    | awk '{s+=$1} END {print s " ms"}'
```

## Before submitting

Regenerate both files after any edit to `make_docx.py`:

```bash
python3 make_docx.py
soffice --headless --convert-to pdf JVM-Tuning-Assignment.docx
```


---

# Day 3: To-Do List App built with Copilot, ChatGPT and CodeWhisperer

The write-up is **[AI-Tools-ToDo-Assignment.docx](AI-Tools-ToDo-Assignment.docx)**,
with a **[PDF copy](AI-Tools-ToDo-Assignment.pdf)**. The project and full notes
are in **[`todo-app/`](todo-app)**.

A small Flask to-do list app: Copilot wrote the interface, ChatGPT wrote the
add-task function, CodeWhisperer reviewed both. The pre-review code is kept in
`todo-app/drafts/` so the six findings can be reproduced rather than just
described.

```bash
cd todo-app
pip install -r requirements.txt
flask --app todo_app.app run     # http://localhost:5000
python3 -m pytest tests/ -v      # 21 tests
python3 benchmark.py 2000        # draft against reviewed
```

The review caught four reproducible bugs, and the two performance findings were
worth less than they looked. Details in
[`todo-app/README.md`](todo-app/README.md).


---

# Day 4: Async IO in Python

The write-up is **[Async-IO-Assignment.docx](Async-IO-Assignment.docx)**, with a
**[PDF copy](Async-IO-Assignment.pdf)**. The scripts are in
**[`async-io/`](async-io)**.

Three scripts using `asyncio` and `aiohttp`: the assignment itself, a sequential
against concurrent measurement, and a run showing what `asyncio.gather` does when
some endpoints fail.

```bash
cd async-io
pip install aiohttp
python3 async_fetch.py     # five endpoints at once
python3 compare.py         # 20 requests: 0.18s sequential, 0.04s concurrent
python3 errors.py          # 404, DNS failure and timeout in one batch
```

`gather` stops at the first exception and discards the responses that already
arrived, unless `return_exceptions=True` is passed. Details in
[`async-io/README.md`](async-io/README.md).
