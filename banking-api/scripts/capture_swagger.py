"""Screenshots of the interactive documentation FastAPI generates.

The app declares no OpenAPI document by hand; these pages are built from the
Pydantic model and the route signatures. Includes a live "Try it out"
execution, so the response shown is one the running server actually sent.

    python3 scripts/capture_swagger.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

import httpx
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures")
BASE = "http://127.0.0.1:8000"

# The content column, measured from the rendered page.
X, W = 28, 1224


def start_server() -> subprocess.Popen:
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1",
         "--port", "8000"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            httpx.get(BASE + "/openapi.json", timeout=1)
            return server
        except Exception:
            time.sleep(0.25)
    server.kill()
    raise SystemExit("server never came up")


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    server = start_server()

    def shot(page, name: str, top, height: int) -> None:
        y = top.bounding_box()["y"]
        page.screenshot(path=os.path.join(FIG, name),
                        clip={"x": X, "y": y, "width": W, "height": height})
        print("  wrote", name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1280, "height": 1500},
                                    device_scale_factor=2)
            page.goto(BASE + "/docs", wait_until="networkidle")
            page.wait_for_selector(".opblock", timeout=15000)
            page.wait_for_timeout(700)

            info = page.locator("div.info")
            models = page.locator("section.models")

            # Title, all three endpoints, and the generated schema list.
            end = models.bounding_box()
            height = int(end["y"] + end["height"] - info.bounding_box()["y"]) + 20
            shot(page, "fig-swagger-overview.png", info, height)

            # The POST expanded: the Pydantic model becomes the request schema.
            post = page.locator(".opblock").first
            post.locator(".opblock-summary").click()
            page.wait_for_timeout(800)
            shot(page, "fig-swagger-post.png", post, 1240)
            post.locator(".opblock-summary").click()
            page.wait_for_timeout(400)

            # The Transaction model, as generated from the Pydantic class.
            models.locator(".model-box-control, button").first.click()
            page.wait_for_timeout(700)
            shot(page, "fig-swagger-schema.png", models, 520)

            # A real execution against the running server.
            matrix = page.locator(".opblock",
                                  has_text="batch-risk-matrix").first
            matrix.locator(".opblock-summary").click()
            page.wait_for_timeout(700)
            matrix.locator("button.try-out__btn").click()
            page.wait_for_timeout(300)
            matrix.locator("button.execute").click()
            matrix.locator(".live-responses-table").wait_for(timeout=20000)
            page.wait_for_timeout(800)
            shot(page, "fig-swagger-tryit.png",
                 matrix.locator(".opblock-summary"), 1180)

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
