# JVM Tuning and Spring Boot Microservice Performance

Assignment submission. The write-up is **[JVM-Tuning-Assignment.docx](JVM-Tuning-Assignment.docx)**,
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

Fill in `[Course / Section]` at the top of the document. Regenerate afterwards with:

```bash
python3 make_docx.py
soffice --headless --convert-to pdf JVM-Tuning-Assignment.docx
```
