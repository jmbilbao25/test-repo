"""Runs the Postman collection against the real server with Newman.

Newman is Postman's command line runner and reads the same collection file the
Postman app does, so the assertions in the collection are executed rather than
just described.

    python3 scripts/run_newman.py
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
COLLECTION = os.path.join(ROOT, "postman", "secure-api.postman_collection.json")
PORT = 8000
PROMPT = r"PS C:\Users\John\secure-api>"

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def find_newman() -> tuple[str, dict]:
    """The newman executable, and an environment where node is on PATH.

    Newman is a Node script, so running it needs node reachable. Under nvm
    neither is on PATH for a non-login shell, so the directory holding them is
    prepended here.
    """
    env = dict(os.environ)
    found = shutil.which("newman")
    if found and shutil.which("node"):
        return found, env

    versions = "/root/.nvm/versions/node"
    if os.path.isdir(versions):
        for base in sorted(os.listdir(versions), reverse=True):
            bindir = os.path.join(versions, base, "bin")
            candidate = os.path.join(bindir, "newman")
            if os.path.exists(candidate):
                env["PATH"] = bindir + os.pathsep + env.get("PATH", "")
                return candidate, env

    if found:
        return found, env
    raise SystemExit("newman is not installed: npm install -g newman")


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


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    newman, env = find_newman()
    server = start_server()
    try:
        result = subprocess.run(
            [newman, "run", COLLECTION, "--reporters", "cli",
             "--color", "off"],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=300,
        )
    finally:
        server.terminate()
        server.wait(timeout=10)

    output = ANSI.sub("", result.stdout + result.stderr).replace("\r\n", "\n")
    print(output)
    print("newman exit code:", result.returncode)

    command = (f"{PROMPT} newman run "
               f"postman\\secure-api.postman_collection.json")
    lines = output.rstrip().split("\n")

    with open(os.path.join(RESULTS, "newman.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"{command}\n" + "\n".join(lines) + "\n")

    # The whole run is over 100 lines, which is far too tall for one figure, so
    # it is also saved in two pieces: the first folder, and the totals.
    table_at = next((i for i, l in enumerate(lines) if l.startswith("┌")),
                    len(lines))
    head = lines[:table_at]
    # Cut the head after the first folder, which is the Auth requests.
    folder_ends = [i for i, l in enumerate(head) if l.startswith("❏")]
    if len(folder_ends) > 1:
        head = head[:folder_ends[1]]

    with open(os.path.join(RESULTS, "newman-head.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(f"{command}\n" + "\n".join(head).rstrip()
                 + "\n\n  ... the Reports and Rejected folders follow\n")

    with open(os.path.join(RESULTS, "newman-summary.txt"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(lines[table_at:]).rstrip() + "\n")

    print("wrote results/newman.txt, newman-head.txt, newman-summary.txt")

    if result.returncode != 0:
        raise SystemExit("the collection has failing assertions")


if __name__ == "__main__":
    main()
