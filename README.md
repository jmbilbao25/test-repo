# Assignments

| Day | Assignment | Write-up | Project |
| --- | --- | --- | --- |
| 2 | JVM tuning and Spring Boot microservice performance | [docx](JVM-Tuning-Assignment.docx) · [pdf](JVM-Tuning-Assignment.pdf) | [`itemservice/`](itemservice) |
| 3 | A to-do list app built with Copilot, ChatGPT and CodeWhisperer | [docx](AI-Tools-ToDo-Assignment.docx) · [pdf](AI-Tools-ToDo-Assignment.pdf) | [`todo-app/`](todo-app) |
| 4 | Async IO in Python: fetching several APIs at once | [docx](Async-IO-Assignment.docx) · [pdf](Async-IO-Assignment.pdf) | [`async-io/`](async-io) |
| 6 | Designing a REST API with OpenAPI/Swagger documentation | [docx](REST-API-OpenAPI-Assignment.docx) · [pdf](REST-API-OpenAPI-Assignment.pdf) | [`books-api/`](books-api) |
| 6 | Building a data processing API with Pandas, NumPy and FastAPI | [docx](Data-Processing-API-Assignment.docx) · [pdf](Data-Processing-API-Assignment.pdf) | [`data-api/`](data-api) |
| 7 | Securing an API with OAuth2, JWT and rate limiting | [docx](API-Security-OAuth2-JWT-Assignment.docx) · [pdf](API-Security-OAuth2-JWT-Assignment.pdf) | [`secure-api/`](secure-api) |
| 8 | Optimizing PostgreSQL: indexing, stored procedures and replication | [docx](PostgreSQL-Performance-Assignment.docx) · [pdf](PostgreSQL-Performance-Assignment.pdf) | [`postgres-tuning/`](postgres-tuning) |
| 9 | Optimizing and recovering an Oracle database | [docx](Oracle-Optimization-Recovery-Assignment.docx) · [pdf](Oracle-Optimization-Recovery-Assignment.pdf) | [`oracle-tuning/`](oracle-tuning) |
| 10 | Hands-on JUnit 5: annotations, assertions and advanced concepts | [docx](JUnit5-Testing-Assignment.docx) · [pdf](JUnit5-Testing-Assignment.pdf) | [`calculator-junit5/`](calculator-junit5) |
| 13 | Spring Cloud service discovery with Eureka and Config Server | [docx](Spring-Cloud-Eureka-Config-Assignment.docx) · [pdf](Spring-Cloud-Eureka-Config-Assignment.pdf) | [`ecommerce-cloud/`](ecommerce-cloud) |
| Milestone | Case study: real-time banking fraud & analytics engine | [docx](Banking-Fraud-Analytics-CaseStudy.docx) · [pdf](Banking-Fraud-Analytics-CaseStudy.pdf) | [`banking-api/`](banking-api) |
| Induction | EastWest Bank core banking relational database lab | [docx](EWB-Core-Banking-Database-Lab.docx) · [pdf](EWB-Core-Banking-Database-Lab.pdf) | [`ewb-core-banking/`](ewb-core-banking) |

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


---

# Day 6: Designing a REST API with OpenAPI/Swagger Documentation

The write-up is **[REST-API-OpenAPI-Assignment.docx](REST-API-OpenAPI-Assignment.docx)**,
with a **[PDF copy](REST-API-OpenAPI-Assignment.pdf)**. The API is in
**[`books-api/`](books-api)**.

A book management API with the five CRUD endpoints, specified in
`books-api/openapi.yaml` and implemented in Flask. The spec was written first,
and 14 of the 48 tests check that the implementation still matches it.

```bash
cd books-api
pip install -r requirements.txt
flask --app books_api.app run     # API on :5000, Swagger UI at /docs
python3 -m pytest tests/ -v       # 48 tests
```

The interesting part is `tests/test_spec.py`, which loads `openapi.yaml`, walks
Flask's routing table to catch undocumented routes, and validates real responses
against the documented schemas. Details in
[`books-api/README.md`](books-api/README.md).


---

# Day 6 hands-on: Building a Data Processing API with Pandas, NumPy and FastAPI

The write-up is **[Data-Processing-API-Assignment.docx](Data-Processing-API-Assignment.docx)**,
with a **[PDF copy](Data-Processing-API-Assignment.pdf)** — 30 pages, 29
screenshots. The service is in **[`data-api/`](data-api)**.

A FastAPI service over the Iris dataset. `POST /load_data` reads the CSV into a
Pandas DataFrame held in memory; seven more endpoints describe, filter, group and
run NumPy statistics over it, and every read returns 409 until the data is
loaded.

```powershell
cd data-api
pip install -r requirements.txt
fastapi dev data_api\main.py     # API on :8000, Swagger UI at /docs
python -m pytest tests/ -v       # 40 tests
```

FastAPI generates the OpenAPI document from the type hints, so declaring the
filter operator as a `Literal` produced the validation, the 422 and the dropdown
in the docs without a separate specification to maintain. Details in
[`data-api/README.md`](data-api/README.md).


---

# Day 7: Securing and Documenting a REST API with OAuth2, JWT and Rate Limiting

The write-up is **[API-Security-OAuth2-JWT-Assignment.docx](API-Security-OAuth2-JWT-Assignment.docx)**,
with a **[PDF copy](API-Security-OAuth2-JWT-Assignment.pdf)** — 37 pages, 46
screenshots. The service is in **[`secure-api/`](secure-api)**.

An expense reports API secured with the OAuth2 password flow and JWT bearer
tokens, rate limited, documented with Swagger and a Postman collection, and used
by a web client served at `/app`.

```powershell
cd secure-api
pip install -r requirements.txt
fastapi dev secure_api\main.py    # /docs, /redoc and /app on :8000
python -m pytest tests/ -v        # 49 tests
```

Three accounts with different scopes, so the write-up can show the difference
between a 401 (the API does not know you), a 403 (it knows you and refuses) and a
429 (you have asked too often). Details in
[`secure-api/README.md`](secure-api/README.md).



---

# Day 9: Optimizing and Recovering an Oracle Database

The write-up is **[Oracle-Optimization-Recovery-Assignment.docx](Oracle-Optimization-Recovery-Assignment.docx)**,
with a **[PDF copy](Oracle-Optimization-Recovery-Assignment.pdf)** — 43 pages, 49
figures. The lab is in **[`oracle-tuning/`](oracle-tuning)**.

A real Oracle AI Database 26ai Free instance: two tables, an index, a PL/SQL
average-per-department report, execution plans before and after, then an RMAN
backup, a dropped table and a point-in-time recovery.

```bash
cd oracle-tuning
./setup.sh                       # instance, schema, tuning, backup, recovery
python3 scripts/make_figures.py
python3 build.py
```

The index the assignment asks for turns out not to speed up the query the
assignment asks for. Q1 averages every salary, so it reads every row either way:
`TABLE ACCESS FULL` before and after, the same plan hash value, the same 1,006
buffer gets. The same index makes a single-department query 10.7x faster, and a
covering index on `(department_id, salary)` is what changes Q1 — 43% fewer blocks
via `INDEX FAST FULL SCAN`, while getting *slower* on the clock, because the table
already fits in the buffer cache.

The recovery is a point-in-time restore to the SCN read one statement before the
`DROP TABLE ... PURGE`, verified by a row fingerprint rather than a row count.
Details in [`oracle-tuning/README.md`](oracle-tuning/README.md).


---

# Day 10: Hands-on JUnit 5 — Annotations, Assertions and Advanced Concepts

The write-up is **[JUnit5-Testing-Assignment.docx](JUnit5-Testing-Assignment.docx)**,
with a **[PDF copy](JUnit5-Testing-Assignment.pdf)** — 43 pages, 46 figures. The
project is in **[`calculator-junit5/`](calculator-junit5)**.

A calculator with the four arithmetic operations and 185 JUnit 5 tests across
nine classes: the lifecycle annotations, the assertions, six parameterized
argument sources, a `@Suite`, three kinds of dependency injection, nested tests
and dynamic tests.

```bash
cd calculator-junit5
mvn test                    # 185 tests, 2 skipped
mvn test -Psuite            # the same 185, reached through @Suite
mvn test -Pshow-failure     # three tests that fail on purpose
mvn compile exec:java       # the calculator on its own
```

The calculator is deliberately given something worth testing: division refuses
rather than returning `Infinity`, rounding is an injected policy, and an
injected operation log gives the lifecycle annotations real work to do.

Two findings from building it, both covered in the write-up:

- JUnit resolves **constructor** parameters against the class-level
  `ExtensionContext`, and store lookups fall through to ancestor stores. An
  extension that caches there hands one instance to every test in the class —
  with all tests still passing, because the `afterEach` cleanup hid it. The
  `@RepeatedTest` is what caught it.
- `0.1 * 0.3` is exactly `0.03` as a double, while `0.3 - 0.2` is
  `0.09999999999999998`. Whether an exact comparison passes depends on the
  values and the operation, so a tolerance belongs everywhere rather than only
  where a failure has already shown up.

Details in [`calculator-junit5/README.md`](calculator-junit5/README.md).



---

# Day 13: Spring Cloud Service Discovery and Configuration

The write-up is **[Spring-Cloud-Eureka-Config-Assignment.docx](Spring-Cloud-Eureka-Config-Assignment.docx)**,
with a **[PDF copy](Spring-Cloud-Eureka-Config-Assignment.pdf)** — 36 pages, 47
figures, 14 of them real browser screenshots. The application is in
**[`ecommerce-cloud/`](ecommerce-cloud)**.

Bilbao Bazaar: a Product Service and an Order Service, a Eureka registry and a
Config Server, on Spring Boot 3.4.1 and Spring Cloud 2024.0.0.

```bash
cd ecommerce-cloud
./run.sh                         # builds, starts all four, exercises everything
python3 scripts/make_figures.py
python3 build.py
```

No host and no port for the Product Service appears anywhere in the Order
Service. Two things turn that into evidence rather than a claim: the same URL on
a RestTemplate without `@LoadBalanced` fails with `UnknownHostException:
product-service`, and the Product Service is deregistered and restarted on **port
9091 instead of 9081**, after which the Order Service prices an order against it
with no restart and no configuration change.

The configuration finding is that a refresh has three states, not two. The Config
Server served the edited value immediately while the running service was still
returning the old one; checking the server alone would have looked like success.
Details in [`ecommerce-cloud/README.md`](ecommerce-cloud/README.md).
