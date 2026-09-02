"""Builds every figure in the write-up.

Three kinds go in:

  * The browser screenshots in screenshots/, taken by capture_ui.py against the
    running stack and already framed. They are copied through untouched.
  * Terminal figures, rendered from the captures in results/.
  * Code figures, sliced out of the actual source files by matching the first and
    last line wanted, so a figure cannot drift from the file it claims to show.

Nothing is retyped. The one presentation change is soft wrapping: NGINX access
log lines and a couple of JSON error bodies run past 120 columns, and wrap()
folds them at a readable width. The characters are unchanged; only where the line
breaks is.

    python3 scripts/make_figures.py
"""
from __future__ import annotations

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
FIG = os.path.join(ROOT, "figures")
RESULTS = os.path.join(ROOT, "results")
SHOTS = os.path.join(ROOT, "screenshots")

sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
try:
    from render import Renderer, numbered, terminal
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"could not import todo-app/scripts/render.py: {exc}")

# Average glyph width of the mono face, as a fraction of the font size. Used to
# size a window to its widest line instead of guessing.
CHAR_EM = 0.602


def read(name: str, folder: str = RESULTS) -> str:
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read().expandtabs(8).rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def trim(body: str) -> str:
    return body.strip("\n")


def wrap(body: str, width: int = 108, indent: str = "  ") -> str:
    """Fold lines longer than width, continuing them on the next line."""
    rows = []
    for line in body.split("\n"):
        if len(line) <= width:
            rows.append(line)
            continue
        rows.append(line[:width])
        rest = line[width:]
        step = width - len(indent)
        while rest:
            rows.append(indent + rest[:step])
            rest = rest[step:]
    return "\n".join(rows)


def fit(body: str, font_size: float, cap: int = 1010) -> int:
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, cap))


def section(text: str, start: str, end: str | None = None) -> str:
    """The part of a capture between two === headers."""
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return trim(text[i:j])


def lines(text: str, first: int, last: int) -> str:
    return trim("\n".join(text.split("\n")[first - 1:last]))


def code_slice(path: str, first: str, last: str) -> tuple[str, int]:
    """The lines of a source file from the one containing first to the one
    containing last, with the real line number the slice starts at."""
    folder, filename = os.path.split(path)
    src = read(filename, os.path.join(ROOT, folder)).split("\n")
    try:
        a = next(i for i, l in enumerate(src) if first in l)
    except StopIteration:
        raise SystemExit(f"{path}: no line containing {first!r}")
    try:
        b = next(i for i, l in enumerate(src) if last in l and i >= a)
    except StopIteration:
        raise SystemExit(f"{path}: no line containing {last!r} after {first!r}")
    return "\n".join(src[a:b + 1]), a + 1


LANG_LABEL = {"python": "Python", "yaml": "YAML", "nginx": "nginx",
              "javascript": "JavaScript", "docker": "Dockerfile",
              "html": "HTML"}


def code_figure(r: Renderer, name: str, path: str, first: str, last: str,
                lang: str = "python", width: int = 950) -> None:
    code, start = code_slice(path, first, last)
    filename = os.path.basename(path)
    r.shot(f"""
<div class="win" style="width:{width}px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>{filename}</div>
  </div>
  <div class="ebody">{numbered(code, lang, start=start)}</div>
  <div class="sbar">
    <span>{path}</span><span>{LANG_LABEL.get(lang, lang)}</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
""", out(name))


# --------------------------------------------------------------------- figures

def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    build = read("build.txt")
    validate = read("nginx_validate.txt")
    running = read("docker_running.txt")
    gateway = read("gateway.txt")
    routing = read("routing.txt")
    east = read("east_west.txt")
    corr = read("correlation.txt")
    rules = read("rules.txt")
    isolation = read("isolation.txt")
    outage = read("outage.txt")
    recovery = read("recovery.txt")
    log_gw = read("logs_gateway.txt")
    log_or = read("logs_orders.txt")
    log_pr = read("logs_products.txt")

    SH = "bash"

    # (filename, title bar, body, font size, width cap)
    shells = [
        # ------------------------------------------------------- the images
        ("fig-build.png", f"{SH} - docker build: three images",
         lines(build, 1, 4) + "\n" + section(build, "=== docker build ./gateway ==="),
         11.5, 1010),
        ("fig-docker-running.png", f"{SH} - the three containers, running",
         running, 11.5, 1060),
        # No docker stats figure: this runtime cannot read the containers'
        # cgroup files, so it reports 0B of memory for all three. A figure of
        # that would be worse than no figure.

        # ------------------------------------------ the gateway's own config
        ("fig-nginx-validate.png",
         f"{SH} - nginx -t: the same file, twice",
         validate, 10.5, 1060),

        ("fig-gateway-health.png",
         f"{SH} - the gateway answering for itself",
         section(gateway, "=== the gateway's own health endpoint ===",
                 "=== response headers on a proxied route ==="), 11.5, 1010),
        ("fig-gateway-headers.png",
         f"{SH} - what the gateway adds to a proxied response",
         section(gateway, "=== response headers on a proxied route ===",
                 "=== each service's health, reached through the gateway ==="),
         11.5, 1010),
        ("fig-gateway-status.png",
         f"{SH} - both services' health, reached through the gateway",
         section(gateway, "=== each service's health, reached through the gateway ==="),
         11.5, 1010),

        # ---------------------------------------------------------- routing
        ("fig-routing-one.png",
         f"{SH} - GET /api/products/1002 through the gateway",
         section(routing, "=== GET /api/products/1002 -> a single product ===",
                 "=== the public path and the internal path are not the same ==="),
         12, 1010),
        ("fig-routing-hops.png",
         f"{SH} - the same product, through the gateway and straight at the service",
         section(routing, "=== the public path and the internal path are not the same ===",
                 "=== a filter, passed through as a query string ==="), 11.5, 1010),
        ("fig-routing-filter.png",
         f"{SH} - a query string, passed through untouched",
         section(routing, "=== a filter, passed through as a query string ===",
                 "=== GET /api/products/9999 -> the service's own 404, not the gateway's ==="),
         11.5, 1010),
        ("fig-routing-404.png",
         f"{SH} - a 404 from the service, not from the gateway",
         section(routing, "=== GET /api/products/9999 -> the service's own 404, not the gateway's ==="),
         11.5, 1060),

        # ------------------------------------------------ service to service
        ("fig-dependency.png",
         f"{SH} - what orders-service knows about the service it calls",
         section(east, "=== what orders-service knows about its dependency ===",
                 "=== POST /api/orders: the gateway routes it, products prices it ==="),
         11.5, 1010),
        ("fig-east-west-order.png",
         f"{SH} - POST /api/orders: routed by the gateway, priced by products-service",
         section(east, "=== POST /api/orders: the gateway routes it, products prices it ===",
                 "=== a second order, on a cheaper line ==="), 11.5, 1010),

        # ------------------------------------------------------ correlation
        ("fig-correlation.png",
         f"{SH} - one request id, three container logs",
         wrap(section(corr, "=== one POST /api/orders, and the same ID in three container logs ===",
                      "=== and it is stored on the order itself ==="), 116),
         9.5, 1090),
        ("fig-order-rid.png",
         f"{SH} - the same id, recorded on the order",
         section(corr, "=== and it is stored on the order itself ==="),
         11.5, 1010),

        # ------------------------------------------------------ the refusals
        ("fig-rules-stock.png",
         f"{SH} - two refusals that need the catalogue to answer first",
         wrap(section(rules, "=== a product that is out of stock (1006, stock 0) ===",
                      "=== above the configured per-order maximum of 10 ==="), 112),
         10.5, 1090),
        ("fig-rules-limits.png",
         f"{SH} - a local rule, and a 404 that travelled back from products-service",
         wrap(section(rules, "=== above the configured per-order maximum of 10 ==="), 112),
         10.5, 1090),

        # -------------------------------------------------------- isolation
        ("fig-isolation.png",
         f"{SH} - the same three ports, dialled two ways",
         isolation, 11.5, 1010),

        # ----------------------------------------------------- a service dies
        ("fig-outage-stop.png",
         f"{SH} - docker stop bazaar-products",
         section(outage, "=== docker stop bazaar-products ===",
                 "=== but the catalogue route now has nothing behind it ==="),
         11.5, 1010),
        ("fig-outage-503.png",
         f"{SH} - two different 503s, from two different components",
         wrap(section(outage, "=== but the catalogue route now has nothing behind it ===",
                      "=== orders already placed are still readable ==="), 112),
         10, 1090),
        ("fig-outage-survives.png",
         f"{SH} - what still works with the catalogue gone",
         section(outage, "=== orders already placed are still readable ==="),
         11.5, 1010),
        ("fig-recovery.png",
         f"{SH} - docker start bazaar-products, and no gateway restart",
         recovery, 11, 1010),

        # ------------------------------------------------------------- logs
        ("fig-logs-gateway.png",
         "docker logs bazaar-gateway - the gateway access log",
         wrap(log_gw, 118), 8.5, 1090),
        ("fig-logs-orders.png",
         "docker logs bazaar-orders - every outbound call, with its id",
         wrap(log_or, 116), 9, 1090),
        ("fig-logs-products.png",
         "docker logs bazaar-products - who called, and what for",
         wrap(log_pr, 116), 9, 1090),
    ]

    # (filename, path, first line, last line, language)
    codes = [
        # ------------------------------------------------------- the gateway
        ("fig-code-nginx-log.png", "gateway/nginx.conf",
         "    # $upstream_addr is the useful column", "    error_log  /dev/stderr warn;", "nginx"),
        ("fig-code-nginx-upstreams.png", "gateway/nginx.conf",
         "    # One named upstream per microservice", "    proxy_hide_header X-Request-ID;", "nginx"),
        ("fig-code-nginx-routes.png", "gateway/nginx.conf",
         "        # ------------------------------------------------------- the routes",
         '            add_header Cache-Control "no-store" always;', "nginx"),
        ("fig-code-nginx-errors.png", "gateway/nginx.conf",
         "        # -------------------------------------------------- shaped failures",
         "            return 503 '{\"error\":\"upstream service unavailable\"", "nginx"),
        ("fig-code-gateway-dockerfile.png", "gateway/Dockerfile",
         "FROM nginx:1.27-alpine", "EXPOSE 8091", "docker"),

        # ------------------------------------------------------- the compose
        ("fig-code-compose-services.png", "docker-compose.yml",
         "  products-service:", "      - products-service", "yaml"),
        ("fig-code-compose-gateway.png", "docker-compose.yml",
         "  gateway:", "      - orders-service", "yaml"),

        # ------------------------------------------------------ the catalogue
        ("fig-code-products-catalogue.png", "products-service/app.py",
         "# Stock levels are chosen so the order rules", '"stock": 6},', "python"),
        ("fig-code-products-endpoint.png", "products-service/app.py",
         '@app.get("/products/{product_id}", tags=["catalogue"])',
         '    return {"currency": CURRENCY, "served_by": SERVICE, **product}', "python"),
        ("fig-code-products-trace.png", "products-service/app.py",
         '@app.middleware("http")', "    return response", "python"),

        # --------------------------------------------------------- the orders
        ("fig-code-orders-config.png", "orders-service/app.py",
         "# The dependency arrives as configuration",
         'TIMEOUT = float(os.getenv("PRODUCTS_TIMEOUT_SECONDS", "3.0"))', "python"),
        ("fig-code-orders-fetch.png", "orders-service/app.py",
         "async def fetch_product", "    return reply.json()", "python"),
        ("fig-code-orders-place.png", "orders-service/app.py",
         '@app.post("/orders", status_code=201, tags=["orders"])',
         "    return order", "python"),

        # ----------------------------------------------------- the storefront
        ("fig-code-storefront-call.png", "gateway/html/app.js",
         "/* One wrapper around fetch",
         "  return { ok: response.ok, status: response.status, body };",
         "javascript"),
    ]

    with Renderer(scale=2) as r:
        for name, title, body, size, cap in shells:
            r.shot(terminal(title, body, width=fit(body, size, cap),
                            font_size=size),
                   out(name))
            print("  rendered " + name)

        for name, path, first, last, lang in codes:
            code_figure(r, name, path, first, last, lang)
            print("  rendered " + name)

    # The browser screenshots are already framed; they just move across.
    copied = 0
    for shot in sorted(os.listdir(SHOTS)):
        if shot.endswith(".png") and not shot.startswith("_"):
            shutil.copy(os.path.join(SHOTS, shot), out("shot-" + shot))
            copied += 1
            print("  copied shot-" + shot)

    total = len(shells) + len(codes) + copied
    print(f"\n{len(shells)} terminal + {len(codes)} code + {copied} screenshots "
          f"= {total} figures in {FIG}")


if __name__ == "__main__":
    main()
