"""The text of the case study.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment.

Measured numbers are parsed out of results/, which is the same source the
figures are built from, so the prose cannot disagree with the screenshot beside
it.
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

TITLE = "Real-Time Banking Fraud & Analytics Engine"
DAY = "Milestone Case Study"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 18, 2026"


def _read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read()


def _num(text: str, pattern: str) -> float:
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"could not find {pattern!r} in the captured results")
    return float(m.group(1))


_GATHER = _read("measure_gather.txt")
_BLOCK = _read("measure_blocking.txt")
_SCALE = _read("measure_scaling.txt")

SEQ_MS = _num(_GATHER, r"one after another.*?([\d.]+) ms")
CON_MS = _num(_GATHER, r"together \(asyncio\.gather\).*?([\d.]+) ms")
GATHER_X = SEQ_MS / CON_MS

ONE_MS = _num(_BLOCK, r"one request on its own\s+([\d.]+) ms")
SLEEP_MS = _num(_BLOCK, r"awaited sleep\s+([\d.]+) ms")
CPU_MS = _num(_BLOCK, r"NumPy/Pandas work\s+([\d.]+) ms")
WALL_MS = _num(_BLOCK, r"total wall time\s+([\d.]+) ms")
SERIAL_MS = _num(_BLOCK, r"if the CPU work serialises\s+([\d.]+) ms")


def _scaling() -> list[tuple[str, str, str]]:
    """The rows of the scaling table, as captured."""
    rows = []
    for line in _SCALE.split("\n"):
        m = re.match(r"\s+([\d,]+)\s+([\d.]+) ms\s+([\d.]+) ms\s+([\d.]+)/s",
                     line)
        if m:
            rows.append((m.group(1), f"{m.group(2)} ms", f"{m.group(4)}/s"))
    if len(rows) < 4:
        raise SystemExit("could not parse the scaling table")
    return rows


SCALING = _scaling()
SMALLEST_RPS = SCALING[0][2]
LARGEST_ROWS, LARGEST_MS, LARGEST_RPS = SCALING[-1]


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    fig = lambda name, caption, width: b.append(("fig", name, caption, width))

    # ------------------------------------------------------------ introduction
    h("Overview")
    p("This case study covers a high-throughput, low-latency transaction "
      "processing and fraud detection service for a banking backend. The "
      "service is built on FastAPI, and uses AsyncIO for outbound I/O, NumPy "
      "for the statistical fraud check, and Pandas for account and portfolio "
      "analytics.")
    p("The document does two things. The first half describes the design and "
      "shows it working: the endpoints, the code behind them, the running "
      "server, and the interactive documentation FastAPI generates. The second "
      "half tests the claims the design makes. Two of those claims are "
      "measurable rather than arguable \u2014 that concurrency is achieved on "
      "outbound calls, and that the request path never blocks \u2014 and the "
      "measurements disagree with each other: the first holds, the second does "
      "not.")
    p("Every figure is evidence rather than illustration. The screenshots taken "
      "on the development machine are included as supplied. The remaining "
      "figures were produced by running the same code again: the server log, "
      "the full response bodies, the Swagger UI, the test run, and the three "
      "performance measurements. A capture script replays the exact session "
      "from the PowerShell screenshot and asserts that every number comes back "
      "identical, so the two sets of evidence are known to describe the same "
      "behaviour.")

    # ----------------------------------------------------------- the problem
    h("The Business Problem")
    p("A banking backend has to do three things at once, and they pull against "
      "one another:")
    b.append(("bullets", [
        "Prevent fraud. Identify a suspicious, out-of-character transaction "
        "before it is authorised, without adding friction for the "
        "overwhelming majority of legitimate customers.",
        "Maintain throughput. Outbound calls to a core-banking mainframe, "
        "credit-line checks and notification services take hundreds of "
        "milliseconds each. None of them may hold up the request path.",
        "Deliver real-time insight. Customers and risk officers need current "
        "spend summaries, category breakdowns and portfolio-wide risk "
        "metrics, not overnight batch reports.",
    ]))
    p("The tension is between the first and the second. A fraud decision needs "
      "context \u2014 the account's history, and where this transaction sits "
      "against it \u2014 but gathering context costs time, and the decision has "
      "to be made while the customer is standing at the terminal. The design "
      "below resolves this by splitting the work: anything that waits on the "
      "network is made concurrent, anything that must be decided synchronously "
      "is reduced to arithmetic over an array, and anything that can happen "
      "after the response is pushed into the background.")

    # -------------------------------------------------------------- the stack
    h("Architecture and Technology Choices")
    b.append(("table", [
        ["Component", "Role", "Responsibility in this service"],
        ["FastAPI", "API gateway and routing",
         "Exposes the REST endpoints, validates incoming JSON through a "
         "Pydantic model, and generates the OpenAPI document and Swagger UI "
         "from the route signatures"],
        ["AsyncIO", "Non-blocking outbound I/O",
         "Runs the simulated mainframe validation calls concurrently with "
         "asyncio.gather, and defers the fraud alert through a background "
         "task so it does not delay the response"],
        ["NumPy", "Vectorised statistics",
         "Computes the mean and standard deviation of an account's history and "
         "the Z-score of the incoming amount, plus the portfolio percentile "
         "threshold"],
        ["Pandas", "Aggregation and analytics",
         "Turns the transaction log into a DataFrame to produce totals, "
         "averages, counts and a category-wise groupby breakdown"],
    ], [1.0, 1.5, 3.9]))
    p("The three endpoints map onto the three parts of the business problem:")
    b.append(("table", [
        ["Endpoint", "Purpose", "Libraries exercised"],
        ["POST /v1/transactions",
         "Ingest a transaction and assess it for fraud in flight",
         "AsyncIO, NumPy"],
        ["GET /v1/accounts/{account_id}/summary",
         "Spend analytics for one account", "Pandas"],
        ["GET /v1/analytics/batch-risk-matrix",
         "Portfolio-wide concurrent verification and percentile risk",
         "AsyncIO, Pandas, NumPy"],
    ], [2.5, 2.6, 1.3]))

    # ---------------------------------------------------------- implementation
    h("Implementation")
    p("The incoming payload is described by a Pydantic model. Declaring amount "
      "as gt=0 is what makes a zero or negative amount a 422 before any "
      "handler code runs, and the same declaration is what appears in the "
      "generated documentation.")
    fig("fig-code-schema.png",
        "The request model. The constraint on amount is both the validation "
        "rule and the documentation.", 6.2)
    p("The two outbound calls are coroutines. The 150 ms sleep in the "
      "mainframe check stands in for the round trip to a legacy core-banking "
      "system; the shorter one stands in for firing a webhook at a fraud "
      "operations centre.")
    fig("fig-code-async.png",
        "The simulated outbound I/O. Both are awaitable, which is what allows "
        "them to be gathered and deferred.", 6.2)
    p("The fraud check is deliberately arithmetic and nothing more. It pulls "
      "the account's prior amounts into a NumPy array, takes the mean and "
      "standard deviation, and expresses the incoming amount as a Z-score \u2014 "
      "the number of standard deviations it sits from that account's normal "
      "behaviour. A score beyond the threshold of 2.0 is treated as anomalous. "
      "Keeping the decision to array arithmetic is what makes it cheap enough "
      "to run inside the request.")
    fig("fig-code-numpy.png",
        "The Z-score engine. Note the two early exits on lines 74 and 81 \u2014 "
        "both are revisited in the findings.", 6.2)
    p("The analytics side hands the transaction log to Pandas, filters to one "
      "account, and produces the totals and the category breakdown through a "
      "groupby.")
    fig("fig-code-pandas.png",
        "The account analytics. A DataFrame is constructed from the whole "
        "table on line 99, before being filtered on line 100.", 6.2)
    p("The ingestion endpoint composes those pieces in order: await the "
      "mainframe, read the account's history, score the amount, queue an alert "
      "if the score is beyond the threshold, then store the record. The "
      "ordering of the last two steps matters and is correct \u2014 the history is "
      "read before the new record is appended, so a transaction is never "
      "included in the baseline it is being judged against.")
    fig("fig-code-endpoint.png",
        "POST /v1/transactions. The alert is added as a background task on "
        "line 148, so it runs after the response has been sent.", 6.2)
    p("The portfolio endpoint is where asyncio.gather earns its place: one "
      "verification call per distinct account, all in flight together, then a "
      "single vectorised percentile over every amount.")
    fig("fig-code-gather.png",
        "GET /v1/analytics/batch-risk-matrix. The list of coroutines on line "
        "176 is awaited as one unit on line 177.", 6.2)

    # -------------------------------------------------------------- running it
    h("Running the Service")
    p("The service is started with uvicorn. The first attempt on the "
      "development machine failed, and it is worth recording because the "
      "message is not self-explanatory:")
    fig("fig-user-pycharm.png",
        "The submitted PyCharm session. The terminal at the bottom shows "
        "uvicorn exiting with \u201cError: Missing argument 'APP'\u201d rather than "
        "starting.", 6.4)
    p("uvicorn needs to be told which object to serve, in module:attribute "
      "form. Invoked bare it has nothing to import, so it prints its usage and "
      "exits. The fix is to name the module and the FastAPI instance inside "
      "it \u2014 here app.py and the variable app, hence app:app. Adding --reload "
      "restarts the server when the file changes, which is what makes it "
      "convenient during development.")
    fig("fig-uvicorn-error-fix.png",
        "The same failure reproduced, and the command that works beneath it.",
        6.4)
    p("With the argument supplied, the server starts and reports the address it "
      "is listening on. This is the state the rest of this document exercises.")
    fig("fig-uvicorn-start.png",
        "uvicorn running and serving the application on port 8000.", 6.2)

    # ---------------------------------------------------------------- evidence
    h("Exercising the API")
    p("The four calls below were issued from PowerShell against the running "
      "service: two transactions, then both analytics endpoints. The first "
      "transaction is an ordinary grocery purchase; the second is a large "
      "jewellery purchase on the same account, which is the case the fraud "
      "check exists for.")
    fig("fig-user-powershell.png",
        "The submitted PowerShell session. Invoke-RestMethod formats the "
        "response as a table, which is why the wider fields are truncated.",
        6.4)
    p("Invoke-RestMethod clips wide output to the console width, so "
      "spend_by_category ends in \u201cgro\u2026\u201d and the flagged transaction in "
      "\u201camount=4\u2026\u201d. Replaying the identical calls and printing the JSON in "
      "full completes the picture. Every figure in the capture below matched "
      "the session above exactly, which is asserted by the script rather than "
      "checked by eye.")
    fig("fig-session-transactions.png",
        "The two transactions with their complete response bodies.", 5.8)
    p("The second response is the one to read closely. The Z-score of 40.69 "
      "says the amount sits forty standard deviations above what this account "
      "normally spends, and is_anomaly is true. The status field says "
      "APPROVED. That combination is the subject of the first finding below.")
    fig("fig-session-analytics.png",
        "The account summary and the portfolio risk matrix, in full. "
        "spend_by_category has four entries, not the three the console showed.",
        5.4)
    p("The server side of the same session shows the ordering that makes the "
      "background task worthwhile: the alert for tx_202 is printed after the "
      "response to the following request had already been served. The customer "
      "was not kept waiting for the fraud operations centre to be notified.")
    fig("fig-uvicorn-access.png",
        "The server log. The alert appears after the summary request, not "
        "between the POST and its response.", 6.2)

    h("Generated Documentation")
    p("No OpenAPI document was written by hand. FastAPI produces one from the "
      "route signatures and the Pydantic model, and serves Swagger UI from it, "
      "which means the documentation cannot drift from the code the way a "
      "hand-maintained specification can.")
    fig("fig-swagger-overview.png",
        "The three endpoints and the generated schema list at /docs.", 6.4)
    p("Expanding the POST shows the request schema derived from the Transaction "
      "model, the example values declared on each field, and both the success "
      "and validation-error responses.")
    fig("fig-swagger-post.png",
        "POST /v1/transactions expanded, with the schema and examples taken "
        "from the Pydantic model.", 5.2)
    fig("fig-swagger-schema.png",
        "The Transaction schema as generated \u2014 the model, not a copy of it.",
        6.0)
    p("The documentation is also a working client. Executing the portfolio "
      "endpoint from the browser returns a live response from the running "
      "server, headers included.")
    fig("fig-swagger-tryit.png",
        "A real execution against the running service, with the response "
        "headers it returned.", 5.2)
    p("The figures in this execution differ from the PowerShell session \u2014 a "
      "p95 threshold of 1822 against 3810, and tx_105 flagged rather than "
      "tx_202. Nothing is inconsistent: this was a freshly started server, so "
      "it held only the five seeded transactions and had no memory of the two "
      "that had been posted earlier. That is a demonstration of the storage "
      "limitation discussed below, and it is the reason it is listed as a "
      "finding rather than a footnote.")

    # ------------------------------------------------------------ verification
    h("Verification")
    p("Seventeen tests pin the behaviour down. They are not written to show "
      "the service works; several exist specifically to record where it "
      "behaves differently from what the design intends, so that those gaps "
      "are reproducible rather than asserted. One reproduces the entire "
      "PowerShell session and asserts all four responses.")
    fig("fig-pytest.png",
        "The test suite. The names are readable as a list of the behaviours "
        "that were confirmed.", 6.2)
    p("Two details worth drawing out. The suite restores the in-memory table "
      "before and after every test, because the module-level list is shared "
      "and every write mutates it \u2014 without that, tests affect one another. "
      "And the Z-score of the jewellery transaction is 38.95 in the test but "
      "40.69 in the session, because the session posted the smaller "
      "transaction first and moved the baseline. The score depends on the "
      "order transactions arrive in, which is expected for a running mean but "
      "worth knowing before treating any single score as absolute.")

    # ------------------------------------------------------------ performance
    h("Performance Analysis")
    p("The design rests on two performance claims. Both were measured.")

    h("Claim 1: outbound calls run concurrently")
    p(f"Three mainframe checks, 150 ms of latency each. Awaited one at a time "
      f"they cost the sum; gathered they cost the slowest.")
    fig("fig-measure-gather.png",
        "Sequential against concurrent, calling the coroutines directly.", 6.0)
    p(f"{SEQ_MS:.0f} ms becomes {CON_MS:.0f} ms, a factor of "
      f"{GATHER_X:.2f}. The claim holds, and it holds for the reason intended: "
      f"the concurrent time is the cost of one check rather than three, so the "
      f"figure would improve further with more accounts. This is AsyncIO doing "
      f"exactly what it was chosen for.")

    h("Claim 2: the request path never blocks")
    p(f"This one does not hold. The NumPy and Pandas work is called directly "
      f"from inside the async handlers, which means it runs on the event loop. "
      f"A coroutine that never awaits cannot be interleaved with anything, so "
      f"while one request is building a DataFrame every other request waits.")
    p(f"The test: hold 50,000 transactions in memory and issue twenty summary "
      f"requests simultaneously. A single request takes {ONE_MS:.1f} ms, of "
      f"which {SLEEP_MS:.0f} ms is an awaited sleep and {CPU_MS:.1f} ms is "
      f"Pandas. If nothing blocked, twenty at once would still cost about "
      f"{ONE_MS:.1f} ms. If the CPU work serialises, they would cost about "
      f"{SERIAL_MS:.0f} ms.")
    fig("fig-measure-blocking.png",
        "Twenty concurrent requests, against both predictions.", 5.6)
    p(f"Measured: {WALL_MS:.0f} ms, within "
      f"{abs(WALL_MS - SERIAL_MS) / SERIAL_MS * 100:.0f}% of the serialised "
      f"prediction and more than ten times the parallel one. The awaited sleep "
      f"does overlap across requests, which is why the result is slightly "
      f"under the prediction rather than over it. The Pandas work does not "
      f"overlap at all.")
    p("The fix is not a redesign. FastAPI will run a handler declared with def "
      "rather than async def in a thread pool automatically, and "
      "asyncio.to_thread will move a specific call off the loop. Either keeps "
      "the event loop free while the CPU work proceeds.")

    h("How it scales with stored data")
    p("The account summary rebuilds a DataFrame from the entire transaction "
      "table on every request and only then filters to one account, so its "
      "cost is driven by how much data exists rather than how much is "
      "returned. Combined with the blocking above, that sets a hard ceiling on "
      "a single worker.")
    fig("fig-measure-scaling.png",
        "Latency and single-worker throughput against rows held in memory.",
        6.0)
    b.append(("table", [["Rows in memory", "Median latency",
                         "Throughput, one worker"]]
                       + [[r, ms, rps] for r, ms, rps in SCALING],
              [1.8, 1.8, 2.2]))
    p(f"At the seeded size the endpoint serves {SMALLEST_RPS}. At "
      f"{LARGEST_ROWS} rows it serves {LARGEST_RPS}, with latency at "
      f"{LARGEST_MS}. Set against the stated goal of thousands of "
      f"transactions per second, that is short by roughly two to three orders "
      f"of magnitude, and adding workers multiplies it by the number of cores "
      f"rather than solving it \u2014 each worker would also hold its own separate "
      f"copy of the in-memory table.")

    # -------------------------------------------------------------- findings
    h("Findings")
    p("What works as designed:")
    b.append(("bullets", [
        f"asyncio.gather delivers genuine concurrency on outbound calls, "
        f"measured at {GATHER_X:.2f}x for three accounts.",
        "The background task defers the fraud alert correctly \u2014 visible in "
        "the server log, where the alert is printed after a later request was "
        "already served.",
        "The baseline excludes the transaction being assessed, so a large "
        "amount does not dilute the very statistic used to judge it.",
        "Pydantic rejects non-positive amounts with a 422 before any handler "
        "runs, and an unknown account returns 404 rather than an empty "
        "summary.",
        "The OpenAPI document and Swagger UI are generated from the code, so "
        "they cannot fall out of step with it.",
    ]))
    p("What does not, in the order it would be worth addressing:")
    b.append(("table", [
        ["#", "Finding", "Impact"],
        ["1", "A flagged transaction is still APPROVED. The response status is "
              "a constant; nothing in the request path can decline. The stated "
              "goal is to catch fraud before authorisation.",
         "High"],
        ["2", "NumPy and Pandas run on the event loop, so concurrent requests "
              "serialise behind one another.", "High"],
        ["3", "Throughput ceiling of a few tens of requests per second against "
              "a goal of thousands, because every summary copies the whole "
              "table.", "High"],
        ["4", "State is a module-level list. A restart loses every "
              "transaction, and multiple workers would each hold a different "
              "one.", "High"],
        ["5", "An account with fewer than two prior transactions cannot be "
              "flagged at all, so a large first transaction on a fresh "
              "account always passes.", "Medium"],
        ["6", "An account whose history is a constant amount has a standard "
              "deviation of zero, which the code turns into a Z-score of 0.0 "
              "regardless of the new amount.", "Medium"],
        ["7", "No idempotency check on transaction_id, so a retried payment is "
              "stored and counted twice.", "Medium"],
        ["8", "Any string beginning acc_ is accepted as a valid account and "
              "implicitly created by the write.", "Medium"],
        ["9", "np.std defaults to a population deviation. On a three-point "
              "baseline the sample deviation is about 36% larger, so every "
              "Z-score is inflated relative to the statistical convention.",
         "Low"],
        ["10", "Field(..., example=...) is deprecated in Pydantic v2 in favour "
               "of json_schema_extra.", "Low"],
    ], [0.35, 4.75, 0.75]))
    p("Findings 5 and 6 deserve emphasis together, because they are the two "
      "cases where the fraud engine silently does nothing rather than "
      "reporting that it cannot decide. Both return is_anomaly false, which is "
      "indistinguishable from a considered judgement that the transaction is "
      "fine. A new account receiving one very large payment, and an account "
      "with a flat regular payment pattern, are both ordinary situations and "
      "both are exactly where an attacker would prefer to operate. A third "
      "state \u2014 insufficient history to assess \u2014 would let the caller route "
      "those to a different control instead of treating them as cleared.")

    # -------------------------------------------------------- recommendations
    h("Recommendations")
    b.append(("bullets", [
        "Separate the fraud verdict from the HTTP response. Return DECLINED "
        "or REVIEW when the score is beyond the threshold, and make the "
        "threshold configurable per account tier. This is the smallest change "
        "with the largest effect, and finding 1 is the reason.",
        "Move the NumPy and Pandas work off the event loop. Declaring the "
        "computational helpers as ordinary def handlers, or wrapping them in "
        "asyncio.to_thread, is enough for FastAPI to run them in a thread "
        "pool and restore real concurrency.",
        "Replace the in-memory list with PostgreSQL. Push the aggregation "
        "into SQL so the summary reads one account rather than copying the "
        "whole table, which addresses findings 3 and 4 together and removes "
        "the per-request DataFrame construction entirely.",
        "Maintain the per-account statistics incrementally rather than "
        "recomputing them. A running count, sum and sum of squares gives the "
        "mean and deviation in constant time per transaction, so the fraud "
        "check stops depending on history length.",
        "Introduce an explicit insufficient-history verdict, and use the "
        "sample deviation (ddof=1) once a baseline is large enough to be "
        "meaningful. Findings 5, 6 and 9 are all consequences of treating a "
        "three-point baseline as if it were a distribution.",
        "Make transaction_id a unique key and reject duplicates, so a client "
        "retry cannot double-count a payment.",
        "Validate accounts against the account store rather than against a "
        "string prefix.",
    ]))
    p("The persistence recommendation is already underway. The schema below "
      "was being modelled in pgAdmin alongside this work, with account_id as a "
      "UUID primary key, a customer reference, a currency code, a numeric "
      "balance and an account_status. A numeric balance rather than a float is "
      "the right instinct for money, and it is worth carrying the same choice "
      "into the transaction amounts, which are currently Python floats and so "
      "subject to binary rounding.")
    fig("fig-user-pgadmin.png",
        "The accounts table being modelled in pgAdmin. The submitted API does "
        "not yet connect to it \u2014 this is the direction, not the current "
        "state.", 6.4)

    # ------------------------------------------------------------- conclusion
    h("Conclusion")
    p("The service does what it was built to demonstrate. Four technologies "
      "are each used for the thing it is genuinely good at: FastAPI for "
      "declarative validation and generated documentation, AsyncIO for "
      "overlapping outbound latency, NumPy for a decision cheap enough to make "
      "inside a request, and Pandas for aggregation that would be tedious to "
      "write by hand. The transaction ingestion path is correct in the detail "
      "that is easiest to get wrong, which is excluding the transaction under "
      "assessment from its own baseline.")
    p(f"The gap between the prototype and the stated business problem is "
      f"narrower than the throughput numbers suggest, because the two large "
      f"problems have the same cause. The CPU work sits on the event loop and "
      f"the data sits in a Python list; both are resolved by moving storage "
      f"into a database and aggregation into SQL, after which the "
      f"{LARGEST_RPS} ceiling stops being a property of the design. The fraud "
      f"logic itself needs one change of a different kind \u2014 the authority to "
      f"decline \u2014 and until it has that, what has been built is an accurate "
      f"fraud detector attached to an endpoint that approves everything.")
    p("A note on the figures: the three screenshots taken on the development "
      "machine are reproduced exactly as supplied. The rest were captured by "
      "running the same code again, with shell prompts shown as PowerShell to "
      "match. The one place where captured output was altered is that JSON "
      "response bodies are indented and long PowerShell commands are wrapped "
      "onto continuation lines, since the API answers on a single line and the "
      "commands run past 200 characters.")

    return b
