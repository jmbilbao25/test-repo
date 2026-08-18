"""Measures the two performance claims the case study makes.

The case study states two things that can be tested rather than asserted:

  1. asyncio.gather makes the outbound mainframe checks concurrent.
  2. offloading work means "the main API thread never blocks".

The first is true and is measured here. The second is not, and this is what
shows it: the NumPy and Pandas work is called synchronously from inside async
handlers, so it runs on the event loop and requests serialise behind one
another.

    python3 scripts/measure.py
"""
from __future__ import annotations

import asyncio
import os
import statistics
import subprocess
import sys
import time

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
BASE = "http://127.0.0.1:8000"

sys.path.insert(0, ROOT)


class Server:
    """A uvicorn process holding a given number of rows in memory."""

    def __init__(self, rows: int) -> None:
        self.rows = rows

    def __enter__(self) -> "Server":
        env = dict(os.environ, SEED_ROWS=str(self.rows),
                   PYTHONPATH=ROOT)
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "scripts.seeded:app",
             "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
            cwd=ROOT, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(120):
            try:
                httpx.get(BASE + "/openapi.json", timeout=1)
                return self
            except Exception:
                time.sleep(0.25)
        self.proc.kill()
        raise SystemExit(f"server with {self.rows} rows never came up")

    def __exit__(self, *exc) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def ms(seconds: float) -> str:
    return f"{seconds * 1000:.1f} ms"


# ------------------------------------------------- 1. does gather help at all?

def measure_gather() -> list[str]:
    """The mainframe check is a 150ms await. Concurrent should beat sequential.

    This calls the functions directly rather than over HTTP, to time the
    asyncio behaviour without the server in the way.
    """
    from app import simulate_mainframe_check

    accounts = [f"acc_{i}" for i in range(1, 4)]

    async def sequential() -> float:
        t = time.perf_counter()
        for acc in accounts:
            await simulate_mainframe_check(acc)
        return time.perf_counter() - t

    async def concurrent() -> float:
        t = time.perf_counter()
        await asyncio.gather(*(simulate_mainframe_check(a) for a in accounts))
        return time.perf_counter() - t

    seq = asyncio.run(sequential())
    con = asyncio.run(concurrent())

    return [
        "Outbound mainframe checks: 3 accounts, 150 ms of latency each",
        "",
        f"  one after another (await in a loop)   {ms(seq)}",
        f"  together (asyncio.gather)            {ms(con)}",
        "",
        f"  {seq / con:.2f}x faster, and the concurrent time is the cost of a",
        "  single check rather than the sum of all three.",
    ]


# ------------------------------- 2. does the CPU work block the event loop?

def measure_blocking(rows: int, concurrency: int) -> list[str]:
    """Fire N requests at once against a server holding `rows` transactions.

    If the handler really never blocks, N at once should cost about what 1
    costs. If the Pandas work runs on the event loop, N at once costs N times
    as much.
    """
    out: list[str] = []

    with Server(rows):
        url = f"{BASE}/v1/accounts/acc_1/summary"

        with httpx.Client(timeout=120) as c:
            c.get(url)                                   # warm pandas imports
            single = []
            for _ in range(5):
                t = time.perf_counter()
                c.get(url)
                single.append(time.perf_counter() - t)
        one = statistics.median(single)

        async def burst() -> list[float]:
            async with httpx.AsyncClient(timeout=120) as c:
                async def one_call() -> float:
                    t = time.perf_counter()
                    await c.get(url)
                    return time.perf_counter() - t
                return await asyncio.gather(
                    *(one_call() for _ in range(concurrency)))

        t0 = time.perf_counter()
        latencies = asyncio.run(burst())
        wall = time.perf_counter() - t0

    latencies.sort()

    # The handler is one awaited sleep plus a block of CPU work. Separating
    # them matters: the sleep is genuinely concurrent, the CPU work is not, and
    # a single "Nx slower" figure would hide that.
    sleep = 0.02                      # the awaited asyncio.sleep in the handler
    cpu = one - sleep
    if_parallel = one
    if_serial = sleep + concurrency * cpu

    out += [
        f"GET /v1/accounts/acc_1/summary with {rows:,} rows in memory",
        "",
        f"  one request on its own              {ms(one)}",
        f"    of which awaited sleep            {ms(sleep)}   (concurrent)",
        f"    of which NumPy/Pandas work        {ms(cpu)}   (runs on the loop)",
        "",
        f"  {concurrency} requests issued at the same time:",
        f"    total wall time                   {ms(wall)}",
        f"    slowest single request            {ms(latencies[-1])}",
        f"    median request                    {ms(statistics.median(latencies))}",
        "",
        "  Two predictions, and which one the measurement matches:",
        f"    if nothing blocked                {ms(if_parallel)}",
        f"    if the CPU work serialises        {ms(if_serial)}",
        f"    measured                          {ms(wall)}",
        "",
        f"  The measurement lands within {abs(wall - if_serial) / if_serial * 100:.0f}% of the serialised",
        "  prediction. The awaited sleep does overlap across requests; the",
        "  NumPy and Pandas work does not, because it is called directly from",
        "  the coroutine instead of being handed to a thread.",
    ]
    return out


# ------------------------------------ 3. how does it scale with table size?

def measure_scaling(sizes: list[int]) -> list[str]:
    """The handler rebuilds a DataFrame from the whole table on every call."""
    # The handler always awaits a fixed 20ms sleep. Subtracting it isolates the
    # part that actually depends on how much data is stored.
    sleep_ms = 20.0

    rows_out = [
        "GET /v1/accounts/acc_1/summary, median of 7 requests",
        "",
        f"  {'rows in memory':>16}  {'median':>10}  {'minus the 20 ms':>16}"
        f"  {'requests/sec':>13}",
        f"  {'':>16}  {'latency':>10}  {'fixed sleep':>16}  {'one worker':>13}",
        f"  {'-' * 16}  {'-' * 10}  {'-' * 16}  {'-' * 13}",
    ]
    for n in sizes:
        with Server(n):
            url = f"{BASE}/v1/accounts/acc_1/summary"
            with httpx.Client(timeout=180) as c:
                c.get(url)
                times = []
                for _ in range(7):
                    t = time.perf_counter()
                    c.get(url)
                    times.append(time.perf_counter() - t)
        med = statistics.median(times) * 1000
        rows_out.append(
            f"  {n + 5:>16,}  {med:>7.1f} ms  {med - sleep_ms:>13.1f} ms"
            f"  {1000 / med:>10.1f}/s")

    rows_out += [
        "",
        "  The fourth column is the ceiling for a single worker: one request",
        "  has to finish before the next can be served, because the work is on",
        "  the event loop. pd.DataFrame(db_transactions) copies the whole",
        "  table on every call before filtering it to one account, so the cost",
        "  is driven by total rows stored and not by the rows returned.",
    ]
    return rows_out


def write(name: str, lines: list[str]) -> None:
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, name), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
    print("  wrote", name)


def main() -> None:
    write("measure_gather.txt", measure_gather())
    write("measure_blocking.txt", measure_blocking(rows=50_000, concurrency=20))
    write("measure_scaling.txt",
          measure_scaling([0, 1_000, 10_000, 50_000, 200_000]))


if __name__ == "__main__":
    main()
