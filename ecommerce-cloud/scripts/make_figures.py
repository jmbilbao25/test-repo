"""Builds every figure in the write-up.

Three kinds go in:

  * The browser screenshots in screenshots/, taken by capture_ui.py against the
    running applications and already framed. They are copied through untouched.
  * Terminal figures, rendered from the captures in results/.
  * Code figures, sliced out of the actual source files.

Nothing is retyped, so no figure can show something the applications did not do.
The one presentation change is soft wrapping: raw Eureka JSON and Spring log
lines run to two thousand columns, so wrap() folds them at a readable width. The
characters are unchanged; only where the line breaks is.

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

CHAR_EM = 0.602


def read(name: str, folder: str = RESULTS) -> str:
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read().expandtabs(8).rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def wrap(body: str, width: int = 108, indent: str = "  ") -> str:
    """Fold lines longer than width, continuing them on the next line.

    Raw Eureka registry JSON is a single 2,000 column line and Spring log lines
    carry a long timestamp and logger prefix. Both are unreadable at figure
    scale unless folded.
    """
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


def trim(body: str) -> str:
    return body.strip("\n")


def section(text: str, start: str, end: str | None = None) -> str:
    """The part of a capture between two === headers."""
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return trim(text[i:j])


def lines(text: str, first: int, last: int) -> str:
    return trim("\n".join(text.split("\n")[first - 1:last]))


def code_slice(path: str, first: str, last: str) -> tuple[str, int]:
    folder, filename = os.path.split(path)
    src = read(filename, os.path.join(ROOT, folder)).split("\n")
    a = next(i for i, l in enumerate(src) if first in l)
    b = next(i for i, l in enumerate(src) if last in l and i >= a)
    return "\n".join(src[a:b + 1]), a + 1


LANG_LABEL = {"java": "Java", "yaml": "YAML", "xml": "XML"}


def code_figure(r: Renderer, name: str, path: str, first: str, last: str,
                lang: str = "java", width: int = 950) -> None:
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

    build = read("build_summary.txt")
    conf = read("config_server.txt")
    eureka = read("eureka.txt")
    startup = read("startup_logs.txt")
    product = read("product_api.txt")
    order = read("order_api.txt")
    nodisc = read("without_discovery.txt")
    refresh = read("refresh.txt")
    dereg = read("deregister.txt")
    rereg = read("reregister.txt")

    SH = "bash"

    # (filename, title bar, body, font size, width cap)
    shells = [
        ("fig-build.png", f"{SH} - mvn package: four applications",
         build, 12, 1010),

        # ------------------------------------------------- config server
        # The JSON envelope for each application is shown as a browser
        # screenshot instead, so only the plain-YAML view is rendered here.
        ("fig-config-yaml.png",
         "Config Server - the same configuration as plain YAML",
         section(conf, "=== the same file served as plain YAML ==="), 11.5, 1010),

        # ------------------------------------------------------- eureka
        ("fig-eureka-empty.png",
         "Eureka REST API - the registry before anything registers",
         wrap(section(eureka, "=== the registry, empty apart from itself",
                      "=== both services registered ===")), 10.5, 1060),
        ("fig-eureka-both.png",
         "Eureka REST API - both services registered",
         wrap(section(eureka, "=== both services registered ===",
                      "=== the product-service lease in detail ===")), 9, 1090),
        ("fig-eureka-lease.png",
         "Eureka REST API - the product-service lease in full",
         wrap(section(eureka, "=== the product-service lease in detail ===")),
         9, 1090),

        ("fig-startup-product.png",
         "product-service - config fetched, then registered",
         wrap(section(startup, "=== product-service: fetching configuration",
                      "=== order-service: fetching configuration"), 116),
         8.5, 1090),
        ("fig-startup-order.png",
         "order-service - config fetched, then registered",
         wrap(section(startup, "=== order-service: fetching configuration"), 116),
         8.5, 1090),

        # ------------------------------------------------- the two services
        # /products, /products/config and /orders/discovery are shown as browser
        # screenshots; only the single-product response is rendered here.
        ("fig-product-one.png",
         "product-service - GET /products/3, the endpoint order-service calls",
         section(product, "=== one product,", "=== everything the Config Server"),
         12, 1010),

        ("fig-order-place.png",
         "order-service - POST /orders, priced through Eureka",
         section(order, "=== placing an order:",
                 "=== a quantity above the configured maximum"), 11, 1010),
        ("fig-order-limit.png",
         "order-service - a configured business rule refusing an order",
         section(order, "=== a quantity above the configured maximum",
                 "=== both orders ==="), 11.5, 1010),
        ("fig-without-discovery.png",
         "order-service - the same URL without @LoadBalanced",
         nodisc, 11.5, 1010),

        # ------------------------------------------------------ refresh
        ("fig-refresh-before.png",
         "product-service - the value in use, and the edit made to the YAML",
         section(refresh, "=== before: the value",
                 "=== the Config Server serves the new value"), 11, 1010),
        ("fig-refresh-lag.png",
         "Config Server has the new value; the running service does not yet",
         section(refresh, "=== the Config Server serves the new value",
                 "=== POST /actuator/refresh ==="), 10.5, 1060),
        ("fig-refresh-after.png",
         "POST /actuator/refresh - the keys that changed, and the new values",
         section(refresh, "=== POST /actuator/refresh ===",
                 "=== the change reaches behaviour"), 11, 1010),
        ("fig-refresh-behaviour.png",
         "product-service - the new threshold changing what the API returns",
         section(refresh, "=== the change reaches behaviour"), 11.5, 1010),

        # ------------------------------------------------- deregistration
        ("fig-dereg-goodbye.png",
         "product-service - deregistering itself on shutdown",
         wrap(section(dereg, "=== shutting product-service down",
                      "=== the registry no longer lists"), 116), 9, 1090),
        ("fig-dereg-registry.png",
         "Eureka - the registry with product-service gone",
         wrap(section(dereg, "=== the registry no longer lists",
                      "=== and placing an order now fails"), 112), 9.5, 1090),
        ("fig-dereg-order.png",
         "order-service - what a missing dependency looks like to a caller",
         section(dereg, "=== and placing an order now fails",
                 "=== the orders already placed"), 11, 1010),

        # ---------------------------------------------------- re-register
        ("fig-rereg-port.png",
         "product-service - back up, on port 9091 this time",
         lines(rereg, 1, 10), 11.5, 1010),
        ("fig-rereg-registry.png",
         "Eureka - the same logical name, a new port",
         wrap(section(rereg, "=== product-service registers again",
                      "=== order-service finds it again"), 112), 9.5, 1090),
        ("fig-rereg-order.png",
         "order-service - finds it at the new port and prices an order, "
         "with no restart",
         section(rereg, "=== order-service finds it again"), 11, 1010),
    ]

    # (filename, path, first line, last line, language)
    codes = [
        ("fig-code-parent-pom.png", "pom.xml",
         "<modules>", "</dependencyManagement>", "xml"),
        ("fig-code-eureka-java.png",
         "eureka-server/src/main/java/com/bilbao/ecommerce/eureka/EurekaServerApplication.java",
         "@SpringBootApplication", "}", "java"),
        ("fig-code-eureka-yml.png",
         "eureka-server/src/main/resources/application.yml",
         "eureka:", "response-cache-update-interval-ms", "yaml"),
        ("fig-code-config-java.png",
         "config-server/src/main/java/com/bilbao/ecommerce/config/ConfigServerApplication.java",
         "@SpringBootApplication", "}", "java"),
        ("fig-code-config-yml.png",
         "config-server/src/main/resources/application.yml",
         "spring:", "search-locations", "yaml"),
        ("fig-code-config-repo-shared.png", "config-repo/application.yml",
         "spring:", "show-details", "yaml"),
        ("fig-code-config-repo-product.png", "config-repo/product-service.yml",
         "# Configuration served", "low-stock-threshold", "yaml"),
        ("fig-code-product-yml.png",
         "product-service/src/main/resources/application.yml",
         "spring:", "lease-expiration-duration-in-seconds", "yaml"),
        ("fig-code-refreshscope.png",
         "product-service/src/main/java/com/bilbao/ecommerce/product/CatalogProperties.java",
         "@Component", "private int lowStockThreshold", "java"),
        ("fig-code-loadbalanced.png",
         "order-service/src/main/java/com/bilbao/ecommerce/order/OrderServiceApplication.java",
         "    /**", "    public RestTemplate loadBalancedRestTemplate", "java"),
        ("fig-code-productclient.png",
         "order-service/src/main/java/com/bilbao/ecommerce/order/ProductClient.java",
         "    /** Fetch one product", "    public List<ServiceInstance> instances", "java"),
        ("fig-code-nodiscovery.png",
         "order-service/src/main/java/com/bilbao/ecommerce/order/ProductClient.java",
         "    public String fetchWithoutDiscovery", "    }", "java"),
    ]

    with Renderer(scale=2) as r:
        for name, title, body, size, cap in shells:
            r.shot(terminal(title, body, width=fit(body, size, cap),
                            font_size=size),
                   out(name))

        for name, path, first, last, lang in codes:
            code_figure(r, name, path, first, last, lang)

    # The browser screenshots are already framed; they just move across.
    copied = 0
    for shot in sorted(os.listdir(SHOTS)):
        if shot.endswith(".png") and not shot.startswith("_"):
            shutil.copy(os.path.join(SHOTS, shot), out("shot-" + shot))
            copied += 1
            print("  copied shot-" + shot)

    print(f"\n{len(shells) + len(codes)} rendered + {copied} screenshots "
          f"= {len(shells) + len(codes) + copied} figures in {FIG}")


if __name__ == "__main__":
    main()
