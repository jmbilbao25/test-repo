# JVM Tuning and Spring Boot Microservice Performance

Assignment submission. The write-up is **[JVM-Tuning-Assignment.docx](JVM-Tuning-Assignment.docx)**.

## What is here

| Path | What it is |
| --- | --- |
| `JVM-Tuning-Assignment.docx` | The assignment write-up to submit |
| `itemservice/` | The Spring Boot microservice (Java 21, Boot 3.4.1) |
| `loadtest.py` | Load generator used to produce the measurements |
| `benchmark.sh` | Runs the service under a set of JVM flags and reports results |
| `results/` | GC logs, heap dumps info and raw numbers from each run |
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

## Results summary

Heavy load, 1,200 requests at 16 concurrent, 25,000 items per request:

| Measurement | Before | After | Change |
| --- | --- | --- | --- |
| Requests per second | 103.0 | 173.5 | 68% faster |
| Average response time | 155.0 ms | 92.0 ms | 41% lower |
| p95 response time | 287.7 ms | 115.3 ms | 60% lower |
| Garbage collections | 369 | 32 | 91% fewer |
| Full GCs | 76 | 0 | eliminated |
| Total GC pause time | 9,812 ms | 236 ms | 97% lower |

Under a lighter load the same change made no throughput difference, which is
covered in the write-up.

## Note on screenshots

The document has four marked placeholders reading `[ PASTE SCREENSHOT HERE ]`.
VisualVM is a desktop GUI tool, so those screenshots have to be captured locally
and pasted in before submitting.
