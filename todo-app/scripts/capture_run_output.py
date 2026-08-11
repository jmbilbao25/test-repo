"""Records what `flask run` prints, for the figure showing the app starting.

Starts the server as a subprocess, keeps whatever it wrote to the console for a
few seconds, hits the page once so an access log line shows up, then stops it.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "flask-run.txt")

env = dict(os.environ, TODO_DB=os.path.join(tempfile.mkdtemp(), "tasks.json"))
proc = subprocess.Popen(
    [sys.executable, "-m", "flask", "--app", "todo_app.app", "run"],
    cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True,
)
try:
    time.sleep(3)
    try:
        urllib.request.urlopen("http://127.0.0.1:5000/", timeout=3).read()
    except Exception as exc:
        print("request failed:", exc)
    time.sleep(1)
finally:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(out)
print(out)
