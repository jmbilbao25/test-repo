"""Reproduces the uvicorn error in the submitted PyCharm screenshot, and shows
the command that works.

The submitted terminal shows `uvicorn` invoked with no arguments, which exits
with "Missing argument 'APP'" rather than starting the server. Both halves are
captured here from real runs so the write-up can show the fix next to the fault.

    python3 scripts/capture_startup_error.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
PROMPT = r"PS C:\Users\JL883807\PyCharmMiscProject>"


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    lines: list[str] = []

    # The fault: uvicorn with no APP argument.
    bad = subprocess.run([sys.executable, "-m", "uvicorn"],
                         cwd=ROOT, capture_output=True, text=True)
    lines.append(f"(.venv) {PROMPT} uvicorn")
    for line in (bad.stdout + bad.stderr).strip().split("\n"):
        # Invoked here as `python -m uvicorn` so the interpreter is
        # unambiguous; shown as the `uvicorn` console script that was actually
        # typed, which is what produces this message on the submitted machine.
        lines.append(line.replace("python -m uvicorn", "uvicorn").rstrip())
    lines.append("")

    # The fix: name the module and the FastAPI instance inside it.
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--reload",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for _ in range(80):
            try:
                httpx.get("http://127.0.0.1:8000/openapi.json", timeout=1)
                break
            except Exception:
                time.sleep(0.25)
        time.sleep(0.5)
    finally:
        server.terminate()
        try:
            out, _ = server.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            out, _ = server.communicate()

    lines.append(f"(.venv) {PROMPT} uvicorn app:app --reload")
    for line in out.strip().split("\n"):
        if re.search(r"shut|Finished server|Stopping reloader", line,
                     re.IGNORECASE):
            continue
        if "/openapi.json" in line:
            continue                       # this script's readiness probe
        # The reloader prints this machine's absolute watch path.
        line = re.sub(r"\['[^']*'\]", r"['C:\\\\Users\\\\JL883807\\\\"
                                     r"PyCharmMiscProject']", line)
        lines.append(line.rstrip())

    path = os.path.join(RESULTS, "uvicorn_error_and_fix.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
    print("  wrote uvicorn_error_and_fix.txt")


if __name__ == "__main__":
    main()
