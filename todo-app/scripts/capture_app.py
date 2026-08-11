"""Screenshots the running app.

Starts the real Flask app on a local port and drives it in a headless Chromium
the same way a person would: typing in the box, pressing the button, ticking
items off. Each screenshot is then wrapped in a browser window frame by
chrome_frame, which draws the window bar and the address bar but does not touch
the page itself.

The page is driven at the top level rather than inside an iframe. The error
messages are flash messages kept in the session cookie, and Chromium will not
send a SameSite=Lax cookie into a cross-site frame, so in an iframe the errors
never appear.

    python3 scripts/capture_app.py
"""
from __future__ import annotations

import os
import socket
import sys
import tempfile
import threading
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from chrome_frame import add_chrome
from todo_app.app import create_app

WIDTH = 640
SCALE = 2


def pick_port(preferred: int = 5000) -> int:
    """Use the usual Flask port if it is free, otherwise anything going."""
    try:
        with socket.socket() as s:
            s.bind(("127.0.0.1", preferred))
        return preferred
    except OSError:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def start_server(db_path: str, port: int) -> None:
    app = create_app(db_path=db_path)
    app.config["SECRET_KEY"] = "screenshot-key"
    threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port,
                               debug=False, use_reloader=False),
        daemon=True,
    ).start()
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("the server did not come up")


class Session:
    def __init__(self, page, base: str) -> None:
        self.page = page
        self.base = base

    def open(self, path: str = "/") -> None:
        self.page.goto(self.base + path)
        self.page.wait_for_load_state()

    def add(self, title: str) -> None:
        self.page.fill("input[name=title]", title)
        self.page.click("button.add-btn")
        self.page.wait_for_load_state()

    def tick_first(self) -> None:
        self.page.locator("li.item").first.locator("button.check").click()
        self.page.wait_for_load_state()

    def save(self, name: str) -> None:
        """Fit the viewport to the card, photograph it, then add the frame."""
        height = int(self.page.locator("main.card").bounding_box()["height"]) + 96
        self.page.set_viewport_size({"width": WIDTH, "height": height})
        self.page.wait_for_timeout(350)
        raw = os.path.join(FIG, "_raw.png")
        self.page.screenshot(path=raw)
        add_chrome(raw, os.path.join(FIG, name),
                   self.page.url.replace("127.0.0.1", "localhost"), scale=SCALE)
        os.unlink(raw)
        print(f"  wrote {name}")


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    db = os.path.join(tempfile.mkdtemp(), "tasks.json")
    port = pick_port()
    start_server(db, port)
    base = f"http://127.0.0.1:{port}"
    print(f"app running on {base}")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox",
                                          "--force-color-profile=srgb",
                                          "--font-render-hinting=none"])
        context = browser.new_context(viewport={"width": WIDTH, "height": 800},
                                      device_scale_factor=SCALE)
        s = Session(context.new_page(), base)

        # 1. The empty list, before anything has been added.
        s.open()
        s.save("fig-app-empty.png")

        # 2. Four tasks typed in through the form, then the first ticked off.
        for title in ["Finish the AI tools assignment",
                      "Review the CodeWhisperer suggestions",
                      "Push the project to GitHub",
                      "Buy milk"]:
            s.add(title)
        s.tick_first()
        s.save("fig-app-filled.png")

        # 3. The duplicate message, from a real rejected submission.
        s.add("  buy   MILK ")
        s.save("fig-app-duplicate.png")

        # 4. An empty submission.
        s.add("    ")
        s.save("fig-app-empty-error.png")

        # 5. A title made of markup, to show it is escaped rather than run.
        s.add("<script>alert('xss')</script>")
        s.save("fig-app-escaped.png")

        # 6. The Active tab, with the finished task filtered out.
        s.open("/?view=active")
        s.save("fig-app-active.png")

        browser.close()
    print("done")


if __name__ == "__main__":
    main()
