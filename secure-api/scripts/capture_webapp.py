"""Screenshots the demo client at /app.

Everything here is the real page talking to the real API in a headless browser:
the sign-in performs the password grant, the table is filled from /reports, and
the refusals are refusals the API actually sent.

    python3 scripts/capture_webapp.py
"""
from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
FIG = os.path.join(ROOT, "figures")

# The browser frame helper written for the Day 3 assignment, imported rather
# than copied.
sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
from chrome_frame import add_chrome

PORT = 8000
BASE = f"http://127.0.0.1:{PORT}"
WIDTH = 900
SCALE = 2


def start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "secure_api.main:app",
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


@contextlib.contextmanager
def server():
    """A fresh server per group, so the login limit starts unspent."""
    proc = start_server()
    try:
        yield
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def shoot(page, name: str) -> None:
    """Fit the viewport to the card, photograph it, then add a browser frame."""
    card = page.locator("main:not([hidden])").first
    height = int(card.bounding_box()["height"]) + 80
    page.set_viewport_size({"width": WIDTH, "height": height})
    page.wait_for_timeout(350)
    raw = os.path.join(FIG, "_raw.png")
    page.screenshot(path=raw)
    add_chrome(raw, os.path.join(FIG, name),
               page.url.replace("127.0.0.1", "localhost"), scale=SCALE,
               style="windows")
    os.unlink(raw)
    print("  wrote", name)


def sign_in(page, username: str, password: str) -> None:
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("#login-form button[type=submit]")
    page.wait_for_selector("#dashboard:not([hidden])", timeout=15000)
    page.wait_for_selector("#reports tbody tr", timeout=15000)
    page.wait_for_timeout(600)


def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--force-color-profile=srgb",
                  "--font-render-hinting=none"])

        # ------------------------------------------------- the normal journey
        with server():
            context = browser.new_context(
                viewport={"width": WIDTH, "height": 800},
                device_scale_factor=SCALE)
            page = context.new_page()
            page.goto(f"{BASE}/app/")
            page.wait_for_selector("#login-form")
            page.wait_for_timeout(600)
            shoot(page, "fig-app-login.png")

            # Manager: can read and write, cannot delete.
            sign_in(page, "manager", "manager-password")
            shoot(page, "fig-app-manager.png")

            page.fill("#new-title", "Client workshop, Iloilo")
            page.fill("#new-category", "travel")
            page.fill("#new-amount", "9800")
            page.click("#add-form button[type=submit]")
            page.wait_for_selector("#notice:not([hidden])", timeout=15000)
            page.wait_for_timeout(700)
            shoot(page, "fig-app-created.png")

            # The delete buttons are disabled because this token cannot delete.
            # Enabling one and pressing it shows that the API refuses anyway,
            # which is the point: the disabled control is a courtesy, not the
            # protection.
            page.eval_on_selector_all(
                ".delete", "els => els.forEach(e => e.disabled = false)")
            page.locator(".delete").first.click()
            page.wait_for_selector("#notice.warn", timeout=15000)
            page.wait_for_timeout(700)
            shoot(page, "fig-app-forbidden.png")

            # Analyst: read only, so the add form is not rendered at all.
            page.click("#signout")
            page.wait_for_selector("#login-form")
            sign_in(page, "analyst", "analyst-password")
            shoot(page, "fig-app-analyst.png")
            context.close()

        # ------------------------------------- the login limit, fresh server
        with server():
            context = browser.new_context(
                viewport={"width": WIDTH, "height": 800},
                device_scale_factor=SCALE)
            page = context.new_page()
            page.goto(f"{BASE}/app/")
            page.wait_for_selector("#login-form")

            for _ in range(6):
                page.fill("#username", "manager")
                page.fill("#password", "wrong-password")
                page.click("#login-form button[type=submit]")
                page.wait_for_selector("#login-error:not([hidden])",
                                       timeout=15000)
                page.wait_for_timeout(250)

            page.wait_for_timeout(600)
            shoot(page, "fig-app-rate-limited.png")
            context.close()

        browser.close()
    print("done")


if __name__ == "__main__":
    main()
