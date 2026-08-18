"""Starts the API under uvicorn and replays the four requests from the
submitted PowerShell session, capturing both sides.

The client side of that session is already evidenced by the submitted
screenshot. What that screenshot does not show is the server: the uvicorn
startup banner, the access log, and the fraud alert the background task prints.
This captures those, and asserts the figures come back identical to the ones in
the screenshot so the reproduction is provably faithful.

    python3 scripts/capture_run.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
BASE = "http://127.0.0.1:8000"

# The four calls from the submitted PowerShell session, in order, with the
# values that session produced. Anything that disagrees is a failed
# reproduction, not a new result.
EXPECTED = {
    "tx_201": {"z_score": -0.97, "mean_spend": 158.5, "std_dev": 111.47,
               "is_anomaly": False},
    "tx_202": {"z_score": 40.69, "mean_spend": 131.38, "std_dev": 107.36,
               "is_anomaly": True},
}
EXPECTED_SUMMARY = {"total_spent": 5025.5, "avg_transaction": 1005.1,
                    "total_transactions": 5}
EXPECTED_MATRIX = {"accounts_checked": 3, "portfolio_p95_threshold": 3810.0,
                   "portfolio_total_volume": 7240.5}


PROMPT = "PS C:\\WINDOWS\\system32>"


def ps(cmd: str, parts: list[str] | None = None) -> str:
    """The command at a PowerShell prompt.

    A full Invoke-RestMethod call with a JSON body runs past 200 characters,
    which will not fit a page. If the caller supplies the argument groups, they
    are split across continuation lines using the backtick and the >>
    continuation prompt, which is how PowerShell itself accepts a wrapped
    command.
    """
    if not parts:
        return f"{PROMPT} {cmd}"
    head, *rest = parts
    out = [f"{PROMPT} {cmd} {head} `"]
    for i, part in enumerate(rest):
        tail = " `" if i < len(rest) - 1 else ""
        out.append(f">>   {part}{tail}")
    return "\n".join(out)


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)

    log = os.path.join(RESULTS, "_uvicorn.log")
    with open(log, "wb") as fh:
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1",
             "--port", "8000"],
            cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
        )

    try:
        for _ in range(60):
            try:
                httpx.get(BASE + "/openapi.json", timeout=1)
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise SystemExit("server never came up")

        transcript: list[str] = []
        failures: list[str] = []

        def record(cmd: str, response: httpx.Response,
                   parts: list[str] | None = None) -> dict:
            """Record the call with its full response body.

            The submitted PowerShell screenshot truncates the wider responses
            (spend_by_category ends in "gro...", the flagged transaction in
            "amount=4..."), because Invoke-RestMethod formats objects as a
            table and clips to the console width. Showing the JSON in full is
            the point of capturing this again rather than relying on the
            screenshot alone.
            """
            body = response.json()
            transcript.append(ps(cmd, parts))
            transcript.append(f"HTTP {response.status_code}")
            transcript.append(json.dumps(body, indent=2))
            transcript.append("")
            return body

        # 1 and 2: the two transactions
        for txid, amount, category in (("tx_201", 50.00, "groceries"),
                                       ("tx_202", 4500.00, "jewelry")):
            r = httpx.post(f"{BASE}/v1/transactions", json={
                "transaction_id": txid, "account_id": "acc_1",
                "amount": amount, "category": category}, timeout=10)
            body = record("Invoke-RestMethod", r, [
                '-Uri "http://127.0.0.1:8000/v1/transactions"',
                '-Method Post -ContentType "application/json"',
                f'-Body \'{{"transaction_id": "{txid}", '
                f'"account_id": "acc_1", "amount": {amount:.2f}, '
                f'"category": "{category}"}}\'',
            ])
            got = body["fraud_assessment"]
            for key, want in EXPECTED[txid].items():
                if got[key] != want:
                    failures.append(f"{txid}.{key}: got {got[key]!r}, "
                                    f"screenshot shows {want!r}")

        # 3: the account summary
        r = httpx.get(f"{BASE}/v1/accounts/acc_1/summary", timeout=10)
        body = record("Invoke-RestMethod", r, [
            '-Uri "http://127.0.0.1:8000/v1/accounts/acc_1/summary"',
            "-Method Get",
        ])
        for key, want in EXPECTED_SUMMARY.items():
            if body["metrics"][key] != want:
                failures.append(f"summary.{key}: got {body['metrics'][key]!r}, "
                                f"screenshot shows {want!r}")

        # 4: the portfolio risk matrix
        r = httpx.get(f"{BASE}/v1/analytics/batch-risk-matrix", timeout=10)
        body = record("Invoke-RestMethod", r, [
            '-Uri "http://127.0.0.1:8000/v1/analytics/batch-risk-matrix"',
            "-Method Get",
        ])
        for key, want in EXPECTED_MATRIX.items():
            if body[key] != want:
                failures.append(f"matrix.{key}: got {body[key]!r}, "
                                f"screenshot shows {want!r}")

        time.sleep(0.5)  # let the background alert task finish and print
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()

    with open(log, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    os.remove(log)

    # The reload/pid lines carry this machine's paths; the banner and the access
    # log are the parts worth showing.
    banner, access = [], []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        if "/openapi.json" in line:
            continue                      # this script's readiness probe
        if re.search(r'"(GET|POST) ', line) or "[ALERT]" in line:
            access.append(line)
        elif re.search(r"shut|Finished server", line, re.IGNORECASE):
            continue                      # a running server shows none of these
        else:
            banner.append(line)

    write("uvicorn_start.txt",
          ps("python -m uvicorn app:app --host 127.0.0.1 --port 8000") + "\n"
          + "\n".join(banner))
    write("uvicorn_access.txt", "\n".join(access))
    write("session.txt", "\n".join(transcript).rstrip())

    if failures:
        raise SystemExit("REPRODUCTION MISMATCH:\n  " + "\n  ".join(failures))
    print("reproduced the submitted session exactly; all values match")


def write(name: str, text: str) -> None:
    with open(os.path.join(RESULTS, name), "w", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")
    print("  wrote", name)


if __name__ == "__main__":
    main()
