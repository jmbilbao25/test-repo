"""Screenshots Swagger UI rendering openapi.yaml.

Starts the real server, opens /docs in a headless browser and photographs the
documentation as it appears. The Try it out panel is driven for real, so the
response in that screenshot came back from the running API.

    python3 scripts/capture_swagger.py
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures")
PORT = 5000
BASE = f"http://localhost:{PORT}"
WIDTH = 1000


def start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "flask", "--app", "books_api.app", "run",
         "--port", str(PORT)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                return proc
        except OSError:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("the server did not come up")


def shoot(page, selector: str, name: str) -> None:
    page.locator(selector).first.screenshot(path=os.path.join(FIG, name))
    print("  wrote", name)


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    server = start_server()
    print(f"server up on {BASE}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                args=["--no-sandbox", "--force-color-profile=srgb",
                      "--font-render-hinting=none"])
            page = browser.new_page(viewport={"width": WIDTH, "height": 1000},
                                    device_scale_factor=2)
            page.goto(f"{BASE}/docs")
            # Swagger UI fetches the spec after load, so wait for it to render.
            page.wait_for_selector(".opblock", timeout=30000)
            page.wait_for_timeout(1200)

            # 1. All five operations, collapsed.
            shoot(page, ".swagger-ui", "fig-swagger-overview.png")

            # 2. POST /books expanded, showing the body schema and responses.
            post = page.locator("#operations-books-createBook")
            post.locator(".opblock-summary").click()
            page.wait_for_timeout(900)
            shoot(page, "#operations-books-createBook", "fig-swagger-post.png")

            # 3. The Book schema expanded at the bottom of the page.
            post.locator(".opblock-summary").click()
            page.wait_for_timeout(400)
            page.locator("section.models .model-container",
                         has_text="Book").first.locator(
                             ".model-box-control").first.click()
            page.wait_for_timeout(700)
            shoot(page, "section.models", "fig-swagger-schemas.png")

            # 4. Try it out on GET /books/{id}, executed against the live API.
            get_one = page.locator("#operations-books-getBook")
            get_one.locator(".opblock-summary").click()
            page.wait_for_timeout(700)
            # tryItOutEnabled is set in the page config, so the panel is already
            # active and this button reads "Cancel". Only click it if it is
            # actually offering to turn Try it out on.
            toggle = get_one.locator("button.try-out__btn")
            if "try it out" in toggle.inner_text().strip().lower():
                toggle.click()
                page.wait_for_timeout(400)
            get_one.locator("input[placeholder='id']").fill("1")
            get_one.locator("button.execute").click()
            page.wait_for_selector(
                "#operations-books-getBook .responses-table .response-col_status",
                timeout=15000)
            page.wait_for_timeout(1200)

            # The block also carries the static response documentation, which
            # makes it far too tall for a page. Crop it after the live response,
            # since that is the part showing the request actually ran.
            page.set_viewport_size({"width": WIDTH, "height": 3000})
            page.wait_for_timeout(500)
            top = get_one.bounding_box()
            live = get_one.locator("table.live-responses-table").first
            bottom = live.bounding_box()
            page.screenshot(
                path=os.path.join(FIG, "fig-swagger-tryit.png"),
                clip={
                    "x": top["x"],
                    "y": top["y"],
                    "width": top["width"],
                    "height": bottom["y"] + bottom["height"] - top["y"] + 14,
                },
            )
            print("  wrote fig-swagger-tryit.png (cropped to the live response)")

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)
    print("done")


if __name__ == "__main__":
    main()
