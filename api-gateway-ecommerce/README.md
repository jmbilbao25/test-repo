# Day 14: API Gateway and Service Communication

The write-up is **[API-Gateway-Service-Communication-Assignment.docx](../API-Gateway-Service-Communication-Assignment.docx)**,
with a **[PDF copy](../API-Gateway-Service-Communication-Assignment.pdf)** — 34
pages, 43 figures, 8 of them real Chromium screenshots of the storefront and the
API taken through the gateway.

Bilbao Bazaar: a two-service e-commerce back end behind an NGINX API gateway.
FastAPI on Python 3.12, nginx 1.27-alpine, three containers.

| Container | Image | Listens on | What it does |
| --- | --- | --- | --- |
| `bazaar-gateway` | `bazaar/api-gateway:1.0` | `0.0.0.0:8091` | Routes `/api/...` to both services, serves the storefront |
| `bazaar-products` | `bazaar/products-service:1.0` | `127.0.0.1:8000` | The catalogue. Products, prices, stock. Calls nobody |
| `bazaar-orders` | `bazaar/orders-service:1.0` | `127.0.0.1:8001` | Takes orders. Prices every line through `products-service` |

## Reproducing it

```bash
cd api-gateway-ecommerce
./run.sh                         # builds, starts, exercises everything, tears down
python3 scripts/make_figures.py  # results/ and screenshots/ into figures/
python3 build.py                 # figures/ into the .docx and .pdf
```

`run.sh` does everything in one invocation, because the three containers only
live for the length of it. It builds the images, starts them in dependency order,
waits on each health endpoint, exercises both communication patterns, drives a
real Chromium for the screenshots, stops the catalogue container to show what
partial failure looks like, starts it again, and captures every command and
response into `results/`.

About three minutes, most of it the two pip installs in the image builds.

## The two patterns

**North-south** is the gateway. One entry point, prefix routing, and because
`proxy_pass` is given a URI as well as a host the public path and the internal
path differ:

| Public route | Goes to |
| --- | --- |
| `/api/products` | `products-service:8000/products` |
| `/api/orders` | `orders-service:8001/orders` |
| `/api/status/products` | `products-service:8000/health` |
| `/health` | answered by the gateway itself |
| `/` | the storefront, served from disk |

**East-west** is `orders-service` calling `products-service` for a price. It uses
synchronous REST rather than a queue, because the orders service cannot write an
order until it knows the price — there is nothing to do while it waits, so a
broker would add an answer to correlate without removing any waiting. It also
skips the gateway, so internal traffic does not depend on the front door.

The address is never a literal: `PRODUCTS_BASE_URL` is a name, and
`GET /api/orders/dependency` reports the name, what it resolved to, and a live
health probe.

## What it demonstrates

**One request, three container logs.** The gateway mints an `X-Request-ID`, the
orders service logs it and forwards it on its own call, the catalogue logs it
again with who called. `results/correlation.txt` follows a single POST through
all three. It is also stored on the order, so one order can be turned back into
the log lines that produced it.

**The gateway is the only way in.** `scripts/check_isolation.py` dials all three
ports twice — once on loopback, once on the machine's routable address. Only 8091
answers on the second, so the claim is tested rather than asserted.

**Partial failure.** With `bazaar-products` stopped, two *different* 503s come
back: NGINX's shaped JSON when it cannot reach an upstream at all, and the orders
service's own, which names the missing dependency and its address. Reading orders
keeps working, and the storefront goes half-available rather than blank — the
`products-service` pill turns red and the orders table stays.

## Notes

- **No `RUN nginx -t` in the gateway Dockerfile.** `nginx -t` resolves every name
  in an `upstream` block, and during a build there is no network and nothing to
  resolve, so it fails on a valid file. `run.sh` runs the check twice on the same
  image — once with `--network none`, once with the names mapped — to show that
  resolution is the only difference. The same startup-time resolution is why
  compose declares `depends_on`.
- **`add_header` does not merge across levels.** A `location` block that declares
  one of its own drops every `add_header` inherited from `server`. That silently
  cost `/health` its `X-Request-ID`, which is why the two headers are repeated
  inside that block.
- **`proxy_hide_header X-Request-ID`** drops the copy the services echo back, so
  the client gets one value instead of `id, id`.
- **Host networking, not a bridge.** The runtime here is Podman without
  `CAP_NET_ADMIN`, so netavark allocates bridge addresses and programs no routes
  to them; published ports fail for the same reason. All three containers share
  the host network namespace and the isolation is done with bind addresses.
  `docker-compose.yml` describes this and explains what the bridge version would
  look like. It is validated with `docker compose config`, but `run.sh` starts
  the containers with equivalent `docker run` commands, because `podman-compose`
  puts every service in a pod and that combination deadlocked the runtime.
- **Port 8091, not 8080 or 8090.** 8080, 8081 and 8083 were taken on the build
  machine. 8090 is worse than taken: a server binds it and no connection to it
  ever completes.
