# Day 13: Spring Cloud Service Discovery and Configuration

The write-up is **[Spring-Cloud-Eureka-Config-Assignment.docx](../Spring-Cloud-Eureka-Config-Assignment.docx)**,
with a **[PDF copy](../Spring-Cloud-Eureka-Config-Assignment.pdf)** — 47 figures,
14 of them real browser screenshots of the Eureka dashboard, the Config Server
and the two service APIs.

Bilbao Bazaar: a two-service e-commerce back end on Spring Boot 3.4.1 and Spring
Cloud 2024.0.0, Java 21.

| Application | Port | What it does |
| --- | --- | --- |
| `config-server` | 8888 | Serves the YAML in `config-repo/` over HTTP |
| `eureka-server` | 8761 | The service registry, and the dashboard |
| `product-service` | 9081 | The catalogue. Registers with Eureka, configured by the Config Server |
| `order-service` | 9082 | Places orders. Finds `product-service` through Eureka |

Ports 9081/9082 rather than the usual 8081/8082 because something else on the
build machine already held those.

## Reproducing it

```bash
cd ecommerce-cloud
./run.sh                         # builds, starts all four, exercises everything
python3 scripts/make_figures.py  # results/ and screenshots/ into figures/
python3 build.py                 # figures/ into the .docx and .pdf
```

`run.sh` does everything in one invocation, because the four services are its
child processes. It starts them in dependency order, waits on each health
endpoint, exercises both mechanisms, drives a real Chromium for the screenshots,
then shuts down and restores the YAML it edited.

## What it demonstrates

**Service discovery.** No host and no port for the Product Service appears
anywhere in the Order Service — it calls `http://product-service/products/{id}`
and a `@LoadBalanced` RestTemplate resolves the name through Eureka.

Two things make that a demonstration rather than an assertion:

- The same URL on a plain RestTemplate fails with `UnknownHostException:
  product-service`. The name is not resolvable by ordinary means, so the working
  call must be doing a registry lookup.
- After deregistering, the Product Service is restarted on **port 9091 instead of
  9081**. The Order Service places an order against it with no restart and no
  configuration change of its own. Had the address been in a config file, that
  restart would have broken it.

**Configuration management.** Shared values (`store.*`: currency, tax rate) live
in `config-repo/application.yml`; per-service values live in files named after
each service's `spring.application.name`. Neither service declares any of it.

The refresh test has three states, not two, which is the finding worth recording:

| | `catalog.featuredMessage` |
| --- | --- |
| File edited | new |
| Config Server | new **immediately** |
| Running service | **still old** |
| After `POST /actuator/refresh` | new |

Checking the Config Server alone would have looked like success and been wrong.
`/actuator/refresh` returns the list of keys it found changed. And because a
config endpoint reporting a new number is still only a report, the low-stock
threshold going from 5 to 8 is verified against `/products/low-stock`, which goes
from 2 products to 3.

## Notes

- `@RefreshScope` on the `@ConfigurationProperties` beans is what makes refresh
  work at all; without it the values bind once at startup.
- Eureka's self preservation is turned **off** and the lease intervals shortened
  from 30s. Both are correct in production and wrong for an assignment that has
  to show a service disappearing from the registry.
- `spring.config.import` uses `optional:`, so a service still starts if the
  Config Server is down — it just starts unconfigured, which is a better failure
  than refusing to boot.
