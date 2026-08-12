"""The text of the write-up.

The timings quoted here are read out of results/compare.txt, the same file the
figure is built from, so the prose cannot end up disagreeing with the screenshot
next to it.
"""
from __future__ import annotations

import os
import re

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

TITLE = "Async IO in Python: Fetching Several APIs at Once"
DAY = "Day 4 Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 11, 2026"


def _timings() -> dict:
    with open(os.path.join(RESULTS, "compare.txt"), encoding="utf-8") as fh:
        text = fh.read()
    wanted = {
        "requests": r"^(\d+) requests",
        "sequential": r"one after another\s+([\d.]+)s",
        "concurrent": r"all at once\s+([\d.]+)s",
        "speedup": r"([\d.]+)x faster",
        "saved": r"faster, ([\d.]+)s saved",
    }
    out = {}
    for key, pattern in wanted.items():
        m = re.search(pattern, text, re.MULTILINE)
        if not m:
            raise ValueError(f"could not find {key} in compare.txt")
        out[key] = m.group(1)
    return out


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    t = _timings()

    # ------------------------------------------------------------ introduction
    h("Introduction")
    p("This assignment asks for a Python program that fetches data from several "
      "APIs at the same time using asyncio and aiohttp, and a short report on "
      "why doing it that way helps.")
    p("I wrote three small scripts. async_fetch.py is the assignment itself: it "
      "fetches five endpoints concurrently and prints what came back. "
      "compare.py runs the same requests one after another and then all at "
      "once, so the benefit is measured rather than asserted. errors.py shows "
      "what happens when some of the endpoints fail, which turned out to be the "
      "part I learned the most from.")
    p("All of them use jsonplaceholder.typicode.com, a free JSON API that needs "
      "no key.")

    # -------------------------------------------------------------- step 1
    h("Step 1: Setting up the environment")
    p("aiohttp is the only thing that needs installing. asyncio is in the "
      "standard library.")
    b.append(("code", [
        "$ pip install aiohttp",
        "Successfully installed aiohttp-3.13.5",
        "",
        "import asyncio",
        "import aiohttp",
    ]))
    p("asyncio provides the event loop and the tools for running coroutines "
      "together. aiohttp is an HTTP client built to work with it. The ordinary "
      "requests library cannot be used here: its calls block the thread, so the "
      "event loop would sit still during every request and nothing would "
      "overlap.")

    # ------------------------------------------------------------ steps 2 & 3
    h("Steps 2 and 3: The async function and the main function")
    p("fetch_data sends one GET request and returns the decoded JSON. The "
      "important line is the await: while the network is busy, await gives "
      "control back to the event loop, which is free to start or continue the "
      "other requests. Without it there would be no concurrency, only a more "
      "complicated way of writing a loop.")
    p("main builds one coroutine per URL and hands them all to asyncio.gather, "
      "which runs them together and returns the results in the order the URLs "
      "were listed, not the order the responses arrived.")
    b.append(("fig", "fig-code.png",
              "fetch_data and main from async_fetch.py", 6.3))
    p("Two details worth pointing out. The session is created once and passed "
      "in, because a ClientSession holds a connection pool and making a new one "
      "per request throws that away. And nothing is awaited inside the loop that "
      "builds the list: awaiting there would finish each request before starting "
      "the next, which is the usual way of accidentally writing sequential code "
      "that looks asynchronous.")

    # -------------------------------------------------------------- step 4
    h("Step 4: Running the program")
    p("The five requests all finish in about the time one of them takes, and "
      "the responses come back out of order while the printed results stay in "
      "the order the URLs were given.")
    b.append(("fig", "fig-run.png", "The output of python3 async_fetch.py", 6.2))

    # -------------------------------------------------------------- step 5
    h("Step 5: Why this is worth doing")
    p("Five requests against this API are too quick to compare meaningfully, so "
      f"compare.py uses {t['requests']} and warms the connection up first, "
      "which keeps DNS and the TLS handshake out of the measurement.")
    b.append(("fig", "fig-compare.png",
              "The same requests done sequentially and then concurrently", 5.6))
    p(f"One after another takes {t['sequential']} seconds. All at once takes "
      f"{t['concurrent']}, which is {t['speedup']} times faster and saves "
      f"{t['saved']} seconds.")
    p("The reason is that almost none of that time is Python doing work. It is "
      "time spent waiting for the network, and waiting is something a program "
      "can do for twenty connections as easily as for one. Sequentially the "
      "waits happen one after the other and add up; concurrently they overlap, "
      "so the total is close to the slowest single request instead of the sum "
      "of all of them.")
    p("This is also why async is the right tool for this problem and the wrong "
      "tool for many others. It only helps when the program is waiting on "
      "something external. Work that keeps the CPU busy gets no benefit at all, "
      "because there is no idle time to reuse, and a long calculation inside a "
      "coroutine will block the event loop and stall every other task with it.")
    p("Threads could also overlap the waiting, but each thread needs its own "
      "stack and the operating system has to switch between them. Here "
      f"{t['requests']} concurrent requests run on one thread, and the only "
      "places control changes hands are the awaits, which are visible in the "
      "source.")

    # ------------------------------------------------------------- the errors
    h("Errors, and what gather does with them")
    p("This is where my first version was wrong. asyncio.gather stops at the "
      "first exception, and the results that had already arrived are lost with "
      "it. One bad URL out of five and the whole batch returns nothing.")
    p("errors.py runs a deliberately broken list: a working endpoint, a path "
      "that returns 404, a hostname that does not resolve, and a real endpoint "
      "given a timeout of a thousandth of a second so it cannot possibly "
      "finish.")
    b.append(("fig", "fig-errors.png",
              "The same batch with and without return_exceptions=True", 6.2))
    p("With the default, the run ends with a TimeoutError and the two responses "
      "that succeeded are thrown away. Passing return_exceptions=True changes "
      "the failures into ordinary return values: each slot in the result list "
      "holds either the data or the exception object, so the two that worked "
      "still come back and the three that failed can be reported. The three "
      "failures arrive as different types, which is useful, because a 404 is a "
      "problem with the request and a DNS error or a timeout is a problem with "
      "the connection.")
    p("The other thing this made clear is that a timeout has to be set. Without "
      "one, a single endpoint that never answers keeps the whole gather waiting "
      "indefinitely, and concurrency does not save you from that.")

    # ------------------------------------------------------------- conclusion
    h("What I took away from it")
    p("The syntax is the easy part. async def, await and asyncio.gather took a "
      "few minutes to get working, and the program was fetching five endpoints "
      "at once almost immediately.")
    p("What actually needed thinking about was everything around it: that "
      "awaiting inside the loop would have quietly made the whole thing "
      "sequential again, that the session has to be shared for the connection "
      "pool to be any use, that gather throws away good results when one task "
      "fails unless you ask it not to, and that without a timeout the batch can "
      "hang forever on one bad endpoint. Those are the parts that would have "
      "caused problems in something real, and none of them are visible from the "
      "syntax alone.")

    return b
