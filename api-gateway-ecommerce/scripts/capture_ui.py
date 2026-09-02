"""Real browser screenshots of the storefront, taken through the gateway.

Chromium loads http://localhost:8091 exactly as a customer would: it fetches the
page from NGINX, then the page's own JavaScript calls /api/products and
/api/orders back through the same gateway. Nothing is mocked and no service is
addressed directly. The shot is then wrapped in a browser window frame carrying
the real URL; the screenshot inside the frame is untouched.

    python3 scripts/capture_ui.py <phase>

run.sh calls this three times, because the interesting states only exist at
particular moments: everything up, the catalogue container stopped, and the
catalogue container back.
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

BASE = "http://localhost:8091"

# phase -> [(output name, url, viewport height, settle ms)]
PHASES: dict[str, list[tuple[str, str, int, int]]] = {
    "running": [
        ("storefront.png", f"{BASE}/", 1000, 1200),
        ("api-products.png", f"{BASE}/api/products", 900, 400),
        ("api-orders.png", f"{BASE}/api/orders", 800, 400),
        ("api-dependency.png", f"{BASE}/api/orders/dependency", 620, 400),
        ("gateway-health.png", f"{BASE}/health", 320, 300),
    ],
    # Shorter viewport: with the catalogue gone the page is a third of its
    # height, and a full-page shot of the tall one is mostly empty background.
    "degraded": [
        ("storefront-degraded.png", f"{BASE}/", 620, 1500),
        ("api-products-down.png", f"{BASE}/api/products", 400, 400),
    ],
    "restored": [
        ("storefront-restored.png", f"{BASE}/", 1000, 1500),
    ],
}


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "running"
    shots = PHASES.get(phase)
    if shots is None:
        raise SystemExit(f"unknown phase {phase!r}; "
                         f"expected one of {sorted(PHASES)}")

    os.makedirs(SHOTS, exist_ok=True)

    with sync_playwright() as play:
        browser = play.chromium.launch(args=["--no-sandbox",
                                             "--force-color-profile=srgb",
                                             "--font-render-hinting=none"])
        for name, url, height, settle in shots:
            page = browser.new_page(viewport={"width": 1180, "height": height},
                                    device_scale_factor=2)
            try:
                page.goto(url, wait_until="load", timeout=30000)
                # The storefront fills itself in after load: three status
                # probes, the catalogue, then the orders table. Photographing it
                # too early catches "Loading the catalogue...".
                page.wait_for_timeout(settle)
                raw = os.path.join(SHOTS, "_raw.png")
                page.screenshot(path=raw, full_page=True)
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
