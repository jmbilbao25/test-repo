"""Calls every endpoint against the running API and saves the output.

The server is started here and the requests are real. The command line shown
above each response is written in PowerShell form, using curl.exe and double
quotes, because that is how it is run on Windows; the endpoints all take their
arguments in the query string, so no request bodies and no awkward quoting.

JSON bodies are re-indented and long arrays are trimmed, because the API answers
on a single line and a 150-row response would not fit on a page. Status lines,
headers and values are untouched. Anything trimmed is marked in the output.

    python3 scripts/capture_curl.py
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
PORT = 8000
HOST = f"http://127.0.0.1:{PORT}"
# What the prompt looks like on the machine this is run from.
PROMPT = r"PS C:\Users\John\data-api>"

# name, description, path, whether to POST, how many array entries to keep
CALLS = [
    # These two have to run before the load, or there would be data in memory
    # and neither would show what it is meant to.
    ("health-before", "Before anything is loaded", "/health", False, None),
    ("err-notloaded", "A read before loading", "/columns", False, None),

    ("load", "Load the CSV into a DataFrame", "/load_data", True, None),
    ("health-after", "After loading", "/health", False, None),
    ("columns", "Column types and null counts", "/columns", False, None),
    ("describe", "pandas describe()", "/describe_data", False, None),
    ("filter-text", "Filter by species",
     "/filter_data?column=species&op=eq&value=setosa&limit=3", False, None),
    ("filter-number", "Filter on a numeric column",
     "/filter_data?column=petal_length&op=gt&value=5.0&limit=3", False, None),
    ("filter-contains", "Case-insensitive text match",
     "/filter_data?column=species&op=contains&value=VIRGIN&limit=2",
     False, None),
    ("stats", "NumPy statistics for one column", "/stats/petal_length",
     False, None),
    ("stats-outliers", "A column that has outliers", "/stats/sepal_width",
     False, None),
    ("groupby", "Mean petal length per species",
     "/group_by?by=species&column=petal_length", False, None),
    ("groupby-max", "A different aggregation",
     "/group_by?by=species&column=sepal_length&agg=max", False, None),
    ("correlation", "Pearson matrix from NumPy", "/correlation", False, None),

    # The remaining failures, which all need the data loaded.
    ("err-column", "A column that does not exist",
     "/filter_data?column=height&op=gt&value=1", False, None),
    ("err-value", "Text compared against a numeric column",
     "/filter_data?column=petal_length&op=gt&value=big", False, None),
    ("err-text-stats", "Statistics on a text column", "/stats/species",
     False, None),
    ("err-operator", "An operator the API does not accept",
     "/filter_data?column=species&op=wat&value=setosa", False, None),
]

# Responses with long arrays: field -> how many entries to keep.
TRIM = {
    "rows": 3,
    "preview": 3,
}
# describe() returns a block per column, which is 90 lines for this dataset.
# Three columns is enough to show the shape, including one text column.
DESCRIBE_KEEP = ("sepal_length", "petal_length", "species")


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


def trim(parsed):
    """Shorten the long parts so a response fits on a page."""
    if not isinstance(parsed, dict):
        return parsed

    for field, keep in TRIM.items():
        rows = parsed.get(field)
        if isinstance(rows, list) and len(rows) > keep:
            hidden = len(rows) - keep
            parsed[field] = rows[:keep] + [f"... {hidden} more rows not shown"]

    table = parsed.get("describe")
    if isinstance(table, dict):
        dropped = [c for c in table if c not in DESCRIBE_KEEP]
        kept = {c: table[c] for c in table if c in DESCRIBE_KEEP}
        if dropped:
            kept[f"... {len(dropped)} more columns not shown"] = ", ".join(
                dropped)
        parsed["describe"] = kept

    return parsed


def format_body(output: str) -> str:
    if "\n\n" not in output:
        return output
    head, _, body = output.partition("\n\n")
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return output
    return head + "\n\n" + json.dumps(trim(parsed), indent=2)


def command(path: str, post: bool) -> str:
    """The line as it would be typed in PowerShell."""
    url = f"{HOST}{path}"
    quoted = f'"{url}"' if "?" in url else url
    verb = "-X POST " if post else ""
    return f"curl.exe -i {verb}{quoted}"


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    server = start_server()
    print(f"server up on {HOST}")
    try:
        for name, description, path, post, _ in CALLS:
            args = ["curl", "-s", "-i"]
            if post:
                args += ["-X", "POST"]
            args.append(f"{HOST}{path}")

            result = subprocess.run(args, capture_output=True, text=True,
                                    timeout=30)
            body = format_body(result.stdout.replace("\r\n", "\n").strip())
            text = f"{PROMPT} {command(path, post)}\n{body}\n"
            with open(os.path.join(RESULTS, f"curl-{name}.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(text)
            status = body.split("\n", 1)[0] if body else "(no output)"
            print(f"  {name:16} {description:38} {status}")
    finally:
        server.terminate()
        server.wait(timeout=10)
    print("done")


if __name__ == "__main__":
    main()
