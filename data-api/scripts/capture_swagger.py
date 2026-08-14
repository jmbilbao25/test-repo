"""Screenshots the interactive documentation FastAPI generates.

Starts the real server and photographs /docs and /redoc in a headless browser.
The Try it out panels are driven for real, so those responses came back from the
running API.

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
PORT = 8000
BASE = f"http://127.0.0.1:{PORT}"
WIDTH = 1020


def start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "data_api.main:app",
         "--port", str(PORT), "--log-level", "warning"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(150):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                return proc
        except OSError:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("the server did not come up")


def block(page, path: str):
    """The operation block for a path, found by the text Swagger UI shows."""
    return page.locator(".opblock", has=page.locator(
        ".opblock-summary-path", has_text=path)).first


def save(locator, name: str) -> None:
    locator.screenshot(path=os.path.join(FIG, name))
    print("  wrote", name)


def crop_below(page, locator, height: int, name: str, width_from=None) -> None:
    """Screenshot a fixed height starting at the top of an element.

    width_from supplies the horizontal extent. A heading button is only as wide
    as its own text, which would otherwise give a narrow strip.
    """
    page.set_viewport_size({"width": WIDTH, "height": 3200})
    page.wait_for_timeout(400)
    box = locator.bounding_box()
    across = (width_from or locator).bounding_box()
    page.screenshot(path=os.path.join(FIG, name), clip={
        "x": across["x"], "y": box["y"],
        "width": across["width"], "height": height,
    })
    print("  wrote", name, "(cropped)")


def crop_to(page, top_locator, bottom_locator, name: str, pad: int = 14) -> None:
    """Screenshot from the top of one element to the bottom of another.

    The operation blocks carry their full static documentation underneath the
    live response, which makes them far too tall for a page.
    """
    page.set_viewport_size({"width": WIDTH, "height": 3200})
    page.wait_for_timeout(400)
    top = top_locator.bounding_box()
    bottom = bottom_locator.bounding_box()
    page.screenshot(path=os.path.join(FIG, name), clip={
        "x": top["x"], "y": top["y"], "width": top["width"],
        "height": bottom["y"] + bottom["height"] - top["y"] + pad,
    })
    print("  wrote", name, "(cropped)")


def try_it(page, path: str, fields: dict) -> None:
    """Open Try it out on an operation, fill the parameters and execute."""
    op = block(page, path)
    op.locator(".opblock-summary").click()
    page.wait_for_timeout(600)
    toggle = op.locator("button.try-out__btn")
    if "try it out" in toggle.inner_text().strip().lower():
        toggle.click()
        page.wait_for_timeout(400)
    for placeholder, value in fields.items():
        op.locator(f"input[placeholder='{placeholder}']").fill(value)
    op.locator("button.execute").click()
    page.wait_for_selector(
        ".opblock.is-open table.live-responses-table", timeout=20000)
    page.wait_for_timeout(1200)


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    server = start_server()
    print(f"server up on {BASE}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                args=["--no-sandbox", "--force-color-profile=srgb",
                      "--font-render-hinting=none"])
            page = browser.new_page(viewport={"width": WIDTH, "height": 1200},
                                    device_scale_factor=2)

            # ------------------------------------------------ 1. the overview
            # The whole page is far too tall for one figure, so it is split: the
            # title and description, then the list of operations.
            page.goto(f"{BASE}/docs")
            page.wait_for_selector(".opblock", timeout=30000)
            page.wait_for_timeout(1500)
            save(page.locator(".information-container"), "fig-docs-header.png")

            sections = page.locator(".opblock-tag-section")
            crop_to(page, sections.first, sections.last,
                    "fig-docs-endpoints.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})

            # -------------------------------------- 2. load_data, expanded
            op = block(page, "/load_data")
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(800)
            save(op, "fig-docs-load.png")
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(300)

            # ------------------------------------- 3. filter_data, expanded
            op = block(page, "/filter_data")
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(800)
            crop_to(page, op, op.locator(".opblock-section-header").last,
                    "fig-docs-filter.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(300)

            # ------------------------------------------------- 4. the schemas
            # The Schemas section is open by default and lists every model
            # FastAPI generated from schemas.py. Each schema name is its own
            # toggle button; StatsResult is the most interesting one to open.
            page.set_viewport_size({"width": WIDTH, "height": 2400})
            page.wait_for_timeout(300)
            save(page.locator("section.models"), "fig-docs-schemas.png")

            # The schemas are listed alphabetically, so a neighbouring name is
            # not a reliable bottom edge. A fixed height below the heading is.
            stats_model = page.get_by_role("button", name="StatsResult",
                                           exact=True).first
            stats_model.click()
            page.wait_for_timeout(800)
            crop_below(page, stats_model, 1140, "fig-docs-schema-stats.png",
                       width_from=page.locator("section.models"))
            stats_model.click()
            page.set_viewport_size({"width": WIDTH, "height": 1200})

            # --------------------------- 5. Try it out on filter_data, live
            page.reload()
            page.wait_for_selector(".opblock", timeout=30000)
            page.wait_for_timeout(1200)
            # The data has to be loaded before a read will succeed.
            try_it(page, "/load_data", {})
            crop_to(page, block(page, "/load_data"),
                    block(page, "/load_data").locator(
                        "table.live-responses-table"),
                    "fig-docs-tryit-load.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})
            block(page, "/load_data").locator(".opblock-summary").click()
            page.wait_for_timeout(300)

            # limit=3 keeps the response short enough to fit in a figure.
            try_it(page, "/filter_data",
                   {"column": "petal_length", "value": "5.0", "limit": "3"})
            crop_to(page, block(page, "/filter_data"),
                    block(page, "/filter_data").locator(
                        "table.live-responses-table"),
                    "fig-docs-tryit-filter.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})
            block(page, "/filter_data").locator(".opblock-summary").click()
            page.wait_for_timeout(300)

            try_it(page, "/stats/{column}", {"column": "petal_length"})
            crop_to(page, block(page, "/stats/{column}"),
                    block(page, "/stats/{column}").locator(
                        "table.live-responses-table"),
                    "fig-docs-tryit-stats.png")

            # ------------------------------------------------------ 6. ReDoc
            page.set_viewport_size({"width": WIDTH, "height": 1400})
            page.goto(f"{BASE}/redoc")
            page.wait_for_selector("h1", timeout=30000)
            page.wait_for_timeout(3000)
            page.screenshot(path=os.path.join(FIG, "fig-redoc.png"))
            print("  wrote fig-redoc.png")

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)
    print("done")


if __name__ == "__main__":
    main()
