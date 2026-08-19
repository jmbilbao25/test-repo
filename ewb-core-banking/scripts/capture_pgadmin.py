"""Performs the lab a second time, in pgAdmin 4, and photographs it.

setup.sh runs the same SQL through psql and captures the text. This script runs
it through the pgAdmin 4 Query Tool instead and screenshots the browser, so the
write-up can show the tool the lab actually specifies rather than only a
terminal.

Nothing here is staged: pgAdmin is connected to the same local PostgreSQL 16
cluster, every SQL string below is read out of sql/, and each figure is a
screenshot of the window right after Execute finished.

    python3 scripts/capture_pgadmin.py

Everything is started and stopped by this script -- the PostgreSQL cluster, the
pgAdmin web application, and headless Chromium -- because none of them can be
left running between steps.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SQL = os.path.join(ROOT, "sql")
FIG = os.path.join(ROOT, "figures")
LOG = os.path.join(ROOT, "pgadmin.log")

PGA_HOME = os.environ.get(
    "PGADMIN_HOME",
    "/projects/sandbox/.venv-pgadmin/lib/python3.9/site-packages/pgadmin4")
PGA_PY = os.environ.get("PGADMIN_PYTHON",
                        "/projects/sandbox/.venv-pgadmin/bin/python")
PGDATA = os.environ.get("PGDATA", "/var/lib/pgsql/ewb/data")
PGBIN = "/usr/bin"
SOCK = "/var/run/postgresql"
DB = "ewb_core"
PW = "ewb_lab_2026"
URL = "http://127.0.0.1:5050/"

SERVER = "EWB Core Banking"
GROUP = "EastWest Bank"
SERVERS_JSON = os.path.join(HERE, "pgadmin_servers.json")
PGA_DB = "/var/lib/pgadmin/pgadmin4.db"

# Desktop mode, so pgAdmin has no login page and no master password to unlock:
# the figures then show the Query Tool rather than an authentication screen.
CONFIG_LOCAL = f'''\
"""Written by scripts/capture_pgadmin.py. Do not edit by hand."""

SERVER_MODE = False
MASTER_PASSWORD_REQUIRED = False
DEFAULT_SERVER = "127.0.0.1"
DEFAULT_SERVER_PORT = 5050
UPGRADE_CHECK_ENABLED = False
SQLITE_PATH = "{PGA_DB}"
'''

# 1500x900 at 2x: wide enough that the Object Explorer header is not clipped and
# that the Data Output grid is still legible once the figure is placed at 6.4
# inches.
VIEWPORT = {"width": 1500, "height": 900}


# --------------------------------------------------------------------- helpers

def sh(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def pg(*args: str) -> subprocess.CompletedProcess:
    return sh("runuser", "-u", "postgres", "--", *args)


def psql(statement: str) -> subprocess.CompletedProcess:
    return pg(f"{PGBIN}/psql", "-h", SOCK, "-d", DB, "-q", "-c", statement)


def body(filename: str) -> str:
    """A .sql file with its leading comment block and psql \\ commands removed.

    The header comments explain the file to a reader of the repository; in a
    screenshot of the Query Tool they would just push the SQL off the top. The
    backslash commands are psql's, and pgAdmin does not understand them.
    """
    text = open(os.path.join(SQL, filename), encoding="utf-8").read()
    lines = text.split("\n")
    while lines and (lines[0].startswith("--") or not lines[0].strip()):
        lines.pop(0)
    kept = [l for l in lines if not l.startswith("\\")]
    return "\n".join(kept).strip() + "\n"


def statement(filename: str, first: str, last: str) -> str:
    """One statement out of a .sql file, located by a line from each end."""
    lines = body(filename).split("\n")
    a = next(i for i, l in enumerate(lines) if first in l)
    b = next(i for i, l in enumerate(lines) if last in l and i >= a)
    return "\n".join(lines[a:b + 1]).strip() + "\n"


def prepare_pgadmin() -> None:
    """Reset pgAdmin to a fresh state with only the EWB server registered.

    The reset is not tidiness. pgAdmin remembers a saved password, so a second
    run would connect silently and the Connect to Server figure -- the one that
    shows the instance is not reachable without one -- could never be taken.
    """
    with open(os.path.join(PGA_HOME, "config_local.py"), "w",
              encoding="utf-8") as fh:
        fh.write(CONFIG_LOCAL)

    if os.path.exists(PGA_DB):
        os.remove(PGA_DB)

    for command in (["setup-db"],
                    ["load-servers", SERVERS_JSON,
                     "--user", "pgadmin4@pgadmin.org"]):
        done = sh(PGA_PY, "setup.py", *command, cwd=PGA_HOME)
        if done.returncode:
            raise SystemExit(f"pgAdmin {command[0]} failed:\n{done.stdout}"
                             f"\n{done.stderr}")
        print("  pgAdmin", command[0], "ok")


def wait_for_pgadmin(timeout: int = 240) -> None:
    for _ in range(timeout):
        try:
            urllib.request.urlopen(URL, timeout=2)
            return
        except urllib.error.HTTPError:
            return                      # a redirect to /browser is a live app
        except Exception:
            time.sleep(1)
    raise SystemExit("pgAdmin never came up; see " + LOG)


# ------------------------------------------------------------------ the driver

class PgAdmin:
    """Drives the pgAdmin 4 web UI and saves figures out of it."""

    def __init__(self, page) -> None:
        self.page = page
        self.qt = None                  # the Query Tool iframe, once opened
        self.n = 0

    # -- plumbing ---------------------------------------------------------
    def shot(self, name: str) -> None:
        self.page.mouse.move(VIEWPORT["width"] - 5, VIEWPORT["height"] - 5)
        self.page.wait_for_timeout(700)
        self.page.screenshot(path=os.path.join(FIG, name))
        self.n += 1
        print("  wrote", name)

    def shot_element(self, selector: str, name: str) -> None:
        self.page.wait_for_timeout(700)
        self.page.locator(selector).first.screenshot(
            path=os.path.join(FIG, name))
        self.n += 1
        print("  wrote", name)

    def properties(self, figure: str) -> None:
        """Show the Properties tab for whatever the tree has selected."""
        self.page.get_by_role("tab", name="Properties").first.click()
        self.page.wait_for_timeout(3000)
        self.shot(figure)

    def node(self, text: str):
        """A tree node whose label *starts with* text.

        Anchored, because a plain substring match on "Tables" also matches
        "Foreign Tables" and "Partitioned Tables", which sort above it.
        """
        return self.page.locator(
            ".file-label",
            has_text=re.compile(r"^" + re.escape(text) + r"\b")).first

    def collapse(self, text: str) -> None:
        n = self.node(text)
        n.scroll_into_view_if_needed()
        n.click()
        self.page.wait_for_timeout(400)
        self.page.keyboard.press("ArrowLeft")
        self.page.wait_for_timeout(1200)

    def expand(self, text: str, expect: str, timeout: int = 90000) -> None:
        n = self.node(text)
        n.scroll_into_view_if_needed()
        n.click()
        self.page.wait_for_timeout(400)
        self.page.keyboard.press("ArrowRight")
        self.node(expect).wait_for(timeout=timeout)
        self.page.wait_for_timeout(1000)

    def menu(self, name: str, item: str) -> None:
        self.page.locator('[data-test="app-menu-bar"]').get_by_role(
            "button", name=name).click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("menuitem", name=item).first.click()

    # -- the session ------------------------------------------------------
    def connect(self, connect_figure: str, dashboard_figure: str) -> None:
        """Expand the group, connect the server, and photograph both."""
        page = self.page
        self.expand(GROUP, SERVER)
        srv = self.node(SERVER)
        srv.click()
        page.wait_for_timeout(600)
        srv.dblclick()

        dialog = page.locator(".MuiDialog-root", has_text="Connect to Server")
        dialog.first.wait_for(timeout=30000)
        page.wait_for_timeout(1200)
        # Photographed empty: the point of the figure is that the server is not
        # reachable without the password, which is what pg_hba.conf now says.
        # Cropped to the dialog, which otherwise sits in a mostly empty window.
        self.shot_element(".MuiDialog-root .MuiPaper-root", connect_figure)

        page.locator(".MuiDialog-root input").first.fill(PW)
        page.locator(".MuiDialog-root input[type='checkbox']").first.check()
        page.wait_for_timeout(300)
        page.locator('.MuiDialog-root button[data-label="OK"]').first.click()
        self.node("Databases").wait_for(timeout=90000)
        page.wait_for_timeout(6000)
        self.shot(dashboard_figure)

    def open_query_tool(self) -> None:
        """Open the Query Tool on ewb_core and keep a handle on its frame.

        The Query Tool is served in its own iframe (/sqleditor/panel/...), so
        the editor and the Data Output grid are not reachable from the main
        document -- everything below goes through the frame locator.
        """
        page = self.page
        self.expand("Databases", DB)
        self.node(DB).click()
        page.wait_for_timeout(2500)
        self.menu("Tools", "Query Tool")

        # The iframe carries no src attribute -- pgAdmin points it at the panel
        # from JavaScript -- so it is found by the URL of the loaded frame
        # rather than by a CSS selector on the element.
        for _ in range(90):
            found = [f for f in page.frames if "sqleditor/panel" in f.url]
            if found:
                self.qt = found[0]
                break
            page.wait_for_timeout(1000)
        else:
            raise SystemExit("the Query Tool panel never loaded")

        self.qt.locator(".cm-content").first.wait_for(timeout=90000)
        page.wait_for_timeout(6000)

        # The Scratch Pad takes a third of the width and is never used here.
        pad = self.qt.get_by_role("tab", name="Scratch Pad")
        if pad.count():
            pad.first.locator("svg").last.click()
            page.wait_for_timeout(1500)

    def run(self, sql: str, figure: str, tab: str | None = None,
            settle: int = 6000) -> None:
        """Replace the editor contents with sql, Execute, and photograph it."""
        page = self.page
        editor = self.qt.locator(".cm-content").first
        editor.click()
        page.keyboard.press("ControlOrMeta+a")
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)
        page.keyboard.insert_text(sql)
        page.wait_for_timeout(800)
        page.keyboard.press("F5")
        page.wait_for_timeout(settle)
        if tab:
            self.qt.get_by_role("tab", name=tab).first.click()
            page.wait_for_timeout(1500)
        # A script longer than the editor pane leaves the view scrolled to the
        # bottom, which hides the BEGIN that the figure exists to show. The
        # result of the run is in the Messages pane either way.
        editor.click()
        page.keyboard.press("ControlOrMeta+Home")
        page.wait_for_timeout(700)
        self.shot(figure)


# ------------------------------------------------------------------------ main

def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    if not os.path.isdir(PGA_HOME):
        raise SystemExit(f"pgAdmin 4 not found at {PGA_HOME}; set PGADMIN_HOME")

    print("starting PostgreSQL")
    pg(f"{PGBIN}/pg_ctl", "-D", PGDATA, "-l",
       os.path.join(os.path.dirname(PGDATA), "server.log"), "start")
    time.sleep(3)

    # setup.sh has already built the tables through psql. Drop them so that the
    # pgAdmin pass really does create them, rather than photographing an error.
    print("dropping the tables so the pgAdmin pass creates them")
    psql("DROP TABLE IF EXISTS ewb_transactions, ewb_accounts;")

    print("resetting pgAdmin 4 and registering the EWB server")
    prepare_pgadmin()

    print("starting pgAdmin 4")
    log = open(LOG, "w")
    server = subprocess.Popen([PGA_PY, "pgAdmin4.py"], cwd=PGA_HOME,
                              stdout=log, stderr=subprocess.STDOUT)
    try:
        wait_for_pgadmin()
        from playwright.sync_api import sync_playwright

        with sync_playwright() as play:
            browser = play.chromium.launch(
                args=["--no-sandbox", "--force-color-profile=srgb",
                      "--font-render-hinting=none"])
            page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
            page.goto(URL, wait_until="load")
            # The React bundle is large and served by the development server.
            page.locator(".file-label", has_text=GROUP).first.wait_for(
                timeout=120000)
            page.wait_for_timeout(6000)

            app = PgAdmin(page)
            app.connect("fig-pga-connect.png", "fig-pga-dashboard.png")
            app.open_query_tool()

            # ---- Exercise 1 -------------------------------------------
            app.run(statement("01_create_accounts.sql",
                              "CREATE TABLE ewb_accounts", ");"),
                    "fig-pga-create-accounts.png", tab="Messages")
            app.run(statement("02_constraint_tests.sql",
                              "customer_name, balance)", "-500.00);"),
                    "fig-pga-negative-balance.png", tab="Messages")
            app.run(statement("02_constraint_tests.sql",
                              "currency, balance)", "'EUR', 1000.00);"),
                    "fig-pga-bad-currency.png", tab="Messages")

            # ---- Exercise 2 -------------------------------------------
            app.run(body("03_seed_accounts.sql"),
                    "fig-pga-seed.png", tab="Data Output")
            app.run(body("04_create_transactions.sql"),
                    "fig-pga-create-ledger.png", tab="Messages")
            app.run(statement("05_fk_test.sql", "INSERT INTO ewb_transactions",
                              "'EWB-9999', 'DEBIT', 100.00);"),
                    "fig-pga-fk-violation.png", tab="Messages")
            app.run("SELECT account_number, customer_name, balance\n"
                    "  FROM ewb_accounts\n WHERE balance > 5000.00;",
                    "fig-pga-query-a.png", tab="Data Output")

            # ---- Exercise 3 -------------------------------------------
            app.run(body("07_transfer_commit.sql"),
                    "fig-pga-commit.png", tab="Messages", settle=8000)
            app.run("SELECT * FROM ewb_accounts ORDER BY account_number;",
                    "fig-pga-after-commit.png", tab="Data Output")
            app.run("SELECT transaction_id, account_number, transaction_type,\n"
                    "       amount, created_at\n"
                    "  FROM ewb_transactions\n ORDER BY transaction_id;",
                    "fig-pga-ledger.png", tab="Data Output")
            app.run(body("09_overdraw_rollback.sql"),
                    "fig-pga-rollback.png", tab="Messages", settle=8000)
            app.run("SELECT balance FROM ewb_accounts\n"
                    " WHERE account_number = 'EWB-1002';",
                    "fig-pga-after-rollback.png", tab="Data Output")

            # ---- the object tree, now that both tables exist ----------
            # The tree was expanded before the tables existed, so it has to be
            # refreshed; F5 on the selected node is pgAdmin's Refresh.
            # Refresh collapses the node, so the whole path is walked again.
            print("refreshing the Object Explorer")
            app.node(DB).click()
            page.wait_for_timeout(800)
            page.keyboard.press("F5")
            page.wait_for_timeout(8000)
            app.expand(DB, "Schemas")
            app.expand("Schemas", "public")
            app.expand("public", "Tables")
            app.expand("Tables", "ewb_accounts")
            app.expand("ewb_accounts", "Constraints")
            app.expand("Constraints", "check_positive_balance")
            # Seven levels of indentation truncate the constraint names in the
            # tree, and the dock splitter cannot be dragged from a script. The
            # Properties tab lists the same objects in full, which is the more
            # useful half of the figure anyway.
            app.properties("fig-pga-tree.png")

            # ewb_accounts is collapsed first, otherwise "Constraints" below
            # would still resolve to the one already open under it.
            app.collapse("ewb_accounts")
            app.expand("ewb_transactions", "Constraints")
            app.properties("fig-pga-tree-ledger.png")

            browser.close()
            print(f"\n{app.n} pgAdmin figures in {FIG}")
    finally:
        server.terminate()
        time.sleep(2)
        server.kill()
        pg(f"{PGBIN}/pg_ctl", "-D", PGDATA, "-m", "fast", "stop")
        print("stopped pgAdmin and PostgreSQL")


if __name__ == "__main__":
    main()
