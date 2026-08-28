"""Real browser screenshots of the Eureka dashboard, the Config Server and the
two services.

Chromium loads each page over HTTP exactly as a person would, the page is
photographed, and the shot is then wrapped in a browser window frame carrying
the real URL. The frame is drawn around the screenshot; the screenshot itself is
untouched.

    python3 scripts/capture_ui.py <phase>

run.sh calls this at four points, because several of the shots only mean
anything at a particular moment: the registry with both services up, the
configuration after a refresh, the registry with one service gone, and the
registry once it has come back.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
SHOTS = os.path.join(ROOT, "screenshots")

sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
from chrome_frame import add_chrome  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

EUREKA = "http://localhost:8761"
CONFIG = "http://localhost:8888"
PRODUCT = "http://localhost:9081"
ORDER = "http://localhost:9082"

# phase -> [(output name, url, viewport height, full page)]
PHASES: dict[str, list[tuple[str, str, int, bool]]] = {
    "registered": [
        ("eureka-dashboard.png", f"{EUREKA}/", 900, True),
        ("config-application.png", f"{CONFIG}/application/default", 760, True),
        ("config-product.png", f"{CONFIG}/product-service/default", 800, True),
        ("config-order.png", f"{CONFIG}/order-service/default", 760, True),
        ("product-list.png", f"{PRODUCT}/products", 900, True),
        ("product-config-before.png", f"{PRODUCT}/products/config", 620, True),
        ("order-discovery.png", f"{ORDER}/orders/discovery", 820, True),
        ("orders-list.png", f"{ORDER}/orders", 900, True),
    ],
    "refreshed": [
        ("config-product-after.png", f"{CONFIG}/product-service/default", 800, True),
        ("product-config-after.png", f"{PRODUCT}/products/config", 620, True),
        ("product-low-stock.png", f"{PRODUCT}/products/low-stock", 700, True),
    ],
    "deregistered": [
        ("eureka-deregistered.png", f"{EUREKA}/", 900, True),
        ("order-discovery-empty.png", f"{ORDER}/orders/discovery", 700, True),
    ],
    "restored": [
        ("eureka-restored.png", f"{EUREKA}/", 900, True),
    ],
}


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "registered"
    shots = PHASES.get(phase)
    if shots is None:
        raise SystemExit(f"unknown phase {phase!r}; "
                         f"expected one of {sorted(PHASES)}")

    os.makedirs(SHOTS, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox",
                                          "--force-color-profile=srgb",
                                          "--font-render-hinting=none"])
        for name, url, height, full in shots:
            page = browser.new_page(viewport={"width": 1180, "height": height},
                                    device_scale_factor=2)
            try:
                page.goto(url, wait_until="load", timeout=30000)
                # The Eureka dashboard fills its tables from the template on
                # load; a short settle avoids catching it half drawn.
                page.wait_for_timeout(700)
                raw = os.path.join(SHOTS, "_raw.png")
                page.screenshot(path=raw, full_page=full)
                add_chrome(raw, os.path.join(SHOTS, name), url, scale=2)
                os.remove(raw)
                print(f"  shot {name}  <- {url}")
            except Exception as exc:  # noqa: BLE001
                print(f"  FAILED {name} <- {url}: {exc}")
            finally:
                page.close()
        browser.close()


if __name__ == "__main__":
    main()
