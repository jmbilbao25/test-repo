"""Screenshots the generated documentation, including the Authorize dialog.

Starts the real server and drives /docs in a headless browser. The sign-in
through the Authorize dialog is real: the page performs the OAuth2 password
grant, and the Try it out calls afterwards carry the token it received.

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
WIDTH = 1040


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


def save(locator, name: str) -> None:
    locator.screenshot(path=os.path.join(FIG, name))
    print("  wrote", name)


def block(page, path: str):
    return page.locator(".opblock", has=page.locator(
        ".opblock-summary-path", has_text=path)).first


def crop(page, top, bottom, name: str, pad: int = 14) -> None:
    page.set_viewport_size({"width": WIDTH, "height": 3400})
    page.wait_for_timeout(400)
    a, b = top.bounding_box(), bottom.bounding_box()
    page.screenshot(path=os.path.join(FIG, name), clip={
        "x": a["x"], "y": a["y"], "width": a["width"],
        "height": b["y"] + b["height"] - a["y"] + pad})
    print("  wrote", name, "(cropped)")


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
            page.goto(f"{BASE}/docs")
            page.wait_for_selector(".opblock", timeout=30000)
            page.wait_for_timeout(1500)

            # ------------------------------------- 1. the description and keys
            save(page.locator(".information-container"),
                 "fig-docs-header.png")

            # ------------------------------- 2. the endpoints, padlocks closed
            sections = page.locator(".opblock-tag-section")
            crop(page, sections.first, sections.last, "fig-docs-endpoints.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})

            # ------------------------------------ 3. the Authorize dialog open
            page.locator("button.btn.authorize").first.click()
            page.wait_for_selector(".dialog-ux .modal-ux", timeout=15000)
            page.wait_for_timeout(700)
            save(page.locator(".dialog-ux .modal-ux"),
                 "fig-docs-authorize-empty.png")

            # Fill it in, tick two of the three scopes, and sign in for real.
            # Swagger UI gives these inputs ids rather than names, and the scope
            # checkbox ids are "<scope>-password-checkbox-<scheme>".
            modal = page.locator(".dialog-ux .modal-ux")
            modal.locator("input#oauth_username").fill("manager")
            modal.locator("input#oauth_password").fill("manager-password")
            # The checkbox itself is hidden and styled through its label, so the
            # label is what a person clicks and what has to be clicked here.
            for scope in ("reports:read", "reports:write"):
                modal.locator(
                    f'label[for="{scope}-password-checkbox-'
                    f'OAuth2PasswordBearer"]').click()
            page.wait_for_timeout(500)
            save(page.locator(".dialog-ux .modal-ux"),
                 "fig-docs-authorize-filled.png")

            # This performs the password grant against /auth/token for real.
            modal.locator("button.modal-btn.auth.authorize").click()
            page.wait_for_timeout(1800)
            save(page.locator(".dialog-ux .modal-ux"),
                 "fig-docs-authorized.png")

            modal.locator("button.modal-btn.auth.btn-done").click()
            page.wait_for_timeout(700)

            # ------------------------------- 4. the token endpoint documented
            op = block(page, "/auth/token")
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(700)
            crop(page, op, op.locator(".opblock-section-header").last,
                 "fig-docs-token-endpoint.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(300)

            # --------------------------- 5. a scoped endpoint, and calling it
            op = block(page, "/reports")
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(700)
            toggle = op.locator("button.try-out__btn")
            if "try it out" in toggle.inner_text().strip().lower():
                toggle.click()
                page.wait_for_timeout(400)
            op.locator("button.execute").click()
            page.wait_for_selector(".opblock.is-open table.live-responses-table",
                                   timeout=20000)
            page.wait_for_timeout(1200)
            crop(page, op, op.locator("table.live-responses-table"),
                 "fig-docs-tryit-reports.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})
            op.locator(".opblock-summary").click()
            page.wait_for_timeout(300)

            # ---------------- 6. an endpoint this token may not use: the 403
            op = block(page, "/reports/{report_id}")
            delete_op = page.locator(".opblock.opblock-delete").first
            delete_op.locator(".opblock-summary").click()
            page.wait_for_timeout(700)
            toggle = delete_op.locator("button.try-out__btn")
            if "try it out" in toggle.inner_text().strip().lower():
                toggle.click()
                page.wait_for_timeout(400)
            delete_op.locator("input[placeholder='report_id']").first.fill("2")
            delete_op.locator("button.execute").click()
            page.wait_for_selector(".opblock.is-open table.live-responses-table",
                                   timeout=20000)
            page.wait_for_timeout(1200)
            crop(page, delete_op,
                 delete_op.locator("table.live-responses-table"),
                 "fig-docs-tryit-forbidden.png")
            page.set_viewport_size({"width": WIDTH, "height": 1200})

            # ------------------------------------------------ 7. the schemas
            page.set_viewport_size({"width": WIDTH, "height": 2200})
            page.wait_for_timeout(400)
            save(page.locator("section.models"), "fig-docs-schemas.png")
            page.set_viewport_size({"width": WIDTH, "height": 1400})

            # -------------------------------------------------- 8. ReDoc
            page.goto(f"{BASE}/redoc")
            page.wait_for_selector("h1", timeout=30000)
            page.wait_for_timeout(3500)
            page.screenshot(path=os.path.join(FIG, "fig-redoc.png"))
            print("  wrote fig-redoc.png")

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)
    print("done")


if __name__ == "__main__":
    main()
