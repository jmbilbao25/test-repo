"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment.

The measured numbers are parsed out of results/, which is the same source the
figures are built from, so the prose cannot end up disagreeing with the
screenshot beside it.
"""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

TITLE = ("Optimizing PostgreSQL Performance: Indexing, Stored Procedures "
         "and Replication")
DAY = "Day 8 Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 18, 2026"


def _benchmark(filename: str) -> dict[str, dict[str, float]]:
    """Pull the per-query means out of a benchmark capture.

    The rows look like:
        Q1 (date range)  |   200 |  0.7548 |   150.97 |   128.0
    """
    stats: dict[str, dict[str, float]] = {}
    with open(os.path.join(RESULTS, filename), encoding="utf-8") as fh:
        for line in fh:
            cells = [c.strip() for c in line.split("|")]
            if len(cells) == 5 and cells[0].startswith("Q"):
                stats[cells[0][:2]] = {
                    "mean": float(cells[2]),
                    "blocks": float(cells[4]),
                }
    if {"Q1", "Q2"} - stats.keys():
        raise SystemExit(f"could not parse both queries out of {filename}")
    return stats


BEFORE = _benchmark("benchmark_before.txt")
AFTER = _benchmark("benchmark_after.txt")


def _line_of(filename: str, needle: str) -> int:
    """Line number of the first line containing needle, so a caption that cites
    a line cannot drift when the file is edited."""
    with open(os.path.join(HERE, "sql", filename), encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if needle in line:
                return n
    raise SystemExit(f"{needle!r} not found in sql/{filename}")


COMMIT_LINE = _line_of("07_functions.sql", "COMMIT;")


def _speedup(key: str) -> str:
    return f"{BEFORE[key]['mean'] / AFTER[key]['mean']:.1f}x"


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    fig = lambda name, caption, width: b.append(("fig", name, caption, width))

    q1_before, q1_after = BEFORE["Q1"], AFTER["Q1"]
    q2_before, q2_after = BEFORE["Q2"], AFTER["Q2"]

    # ------------------------------------------------------------ introduction
    h("Introduction")
    p("This assignment asks for five things done to a PostgreSQL database: a "
      "sample dataset restored, indexes added on the strength of EXPLAIN "
      "output, a stored procedure written, streaming replication configured "
      "with pg_basebackup, and the server's memory parameters tuned using the "
      "pg_stat views as evidence.")
    p("Everything below was run against PostgreSQL 16.14. Two clusters were "
      "built: a primary on port 5432 and a replica on 5433, streaming from it. "
      "The sample database is dvdrental, restored into a database named "
      "exampledb.")
    p("Every screenshot in this report is output captured from those two "
      "servers. A single script, setup.sh, performs all five steps in order "
      "and writes the output of each into results/, and the figures are "
      "rendered from those files rather than retyped, so no figure can claim "
      "something the database did not do. The script tears both clusters down "
      "and rebuilds them from scratch on each run, so all of it is repeatable.")

    # ----------------------------------------------------------------- step 1
    h("Step 1: Setup and Preparation")
    p("The sample archive is the dvdrental.zip the assignment links to. "
      "postgresqltutorial.com serves it but refuses non-browser clients, so "
      "the script pulls the identical archive from a mirror. It is a "
      "pg_restore custom-format dump, not plain SQL, so it is loaded with "
      "pg_restore rather than psql.")
    fig("fig-setup.png",
        "PostgreSQL 16.14, and exampledb after the restore.", 6.0)
    p("The restore produces fifteen tables. The four this report touches are "
      "listed with their row counts, because the size of a table decides "
      "whether an index on it is worth having at all.")
    fig("fig-schema.png",
        "The fifteen tables of the dvdrental schema, and the row counts of the "
        "four used below. payment, at 14,596 rows, is the largest.", 4.5)
    p("payment is the table both test queries read. It is worth looking at "
      "what it already has, because dvdrental ships with indexes on its "
      "foreign keys, and an index that already exists changes what a new one "
      "can be credited with.")
    fig("fig-payment-table.png",
        "The payment table. Note idx_fk_customer_id, which already exists \u2014 "
        "this matters for Q2 below.", 6.4)

    # ----------------------------------------------------------------- step 2
    h("Step 2: Indexing Strategies")
    p("The assignment asks for the most frequently used queries to be "
      "identified. Rather than guess, the server was asked. "
      "pg_stat_statements was loaded at startup; it records every statement "
      "executed along with a call count and total time, which is what makes "
      "\u201cfrequently used\u201d a measurable claim rather than an assumption. "
      "pg_stat_user_tables was used alongside it, because a large "
      "seq_tup_read relative to seq_scan is the symptom of a filter with no "
      "index behind it.")
    fig("fig-candidates.png",
        "Where the time goes, and the sequential-scan evidence. payment is "
        "read end to end on every call, roughly 14,600 rows returned to find "
        "a few hundred.", 6.4)
    p("Two queries came out of that, and they were chosen because they fail "
      "for different reasons:")
    b.append(("table", [
        ["", "Query", "Why it is slow"],
        ["Q1", "Payments taken on one particular day "
               "(a range over payment_date)",
         "No index on payment_date at all, so the whole table is scanned"],
        ["Q2", "The ten most recent payments for one customer "
               "(filter, then sort)",
         "An index on customer_id exists, but the sort by date is done "
         "afterwards in memory"],
    ], [0.4, 2.55, 3.35]))

    h("The plans before indexing")
    p(f"Q1 is a plain sequential scan. The line worth reading is Rows Removed "
      f"by Filter: 14,288 \u2014 PostgreSQL examined every row in the table and "
      f"discarded all but 308 of them, touching "
      f"{q1_before['blocks']:.0f} buffers to do it.")
    fig("fig-explain-before-q1.png",
        "Q1 with no index: Seq Scan, and 14,288 rows read only to be thrown "
        "away.", 6.4)
    p("Q2 is more interesting, and it is the reason it was included. It is "
      "already using an index \u2014 idx_fk_customer_id, which shipped with the "
      "sample database \u2014 so the filter is not the problem. The problem is "
      "the two nodes above it: the rows come back in no particular order, so a "
      "Sort has to run before the Limit can take ten of them.")
    fig("fig-explain-before-q2.png",
        "Q2 with no composite index. The filter is already indexed; the "
        "top-N heapsort above it is the avoidable work.", 5.6)

    h("The indexes")
    p("One index per query, each shaped to the query's problem. Q1 needs "
      "nothing more than a B-tree on the column it filters. Q2 needs a "
      "composite index whose leading column is the one being filtered and "
      "whose second column is stored in the direction the query asks to sort "
      "in \u2014 that way the index can satisfy the filter and the ordering at "
      "once, and the sort becomes unnecessary.")
    fig("fig-code-indexes.png",
        "The two CREATE INDEX statements. Column order in a composite index "
        "is not arbitrary; it is what decides whether the sort can be skipped.",
        6.2)
    fig("fig-indexes.png",
        "The indexes on payment afterwards. The two new ones cost 336 kB and "
        "464 kB.", 5.4)

    h("The plans after indexing")
    p(f"Q1 no longer reads the table. It finds the matching rows through "
      f"idx_payment_payment_date and fetches only the pages that contain "
      f"them, cutting buffers from {q1_before['blocks']:.0f} to "
      f"{q1_after['blocks']:.0f}.")
    fig("fig-explain-after-q1.png",
        "Q1 indexed: Bitmap Index Scan, 15 heap blocks instead of the whole "
        "table.", 6.4)
    p("Q2's plan is now four lines instead of nine. The Sort and the Bitmap "
      "Heap Scan are both gone, replaced by a single Index Scan: because the "
      "index already holds the rows for that customer in descending date "
      "order, the Limit takes the first ten and stops.")
    fig("fig-explain-after-q2.png",
        "Q2 indexed. The Sort node has disappeared entirely \u2014 the index "
        "supplies the order.", 5.8)

    h("Measuring it properly")
    p("A single EXPLAIN ANALYZE of a query that runs in well under a "
      "millisecond is mostly noise; running the same statements repeatedly "
      "during this work produced execution times that varied by a factor of "
      "three in both directions. So each query was run 200 times and the mean "
      "that pg_stat_statements recorded was compared instead.")
    fig("fig-benchmark.png",
        "200 runs of each query, before and after. The block counts are "
        "deterministic; the means are stable enough to compare.", 6.2)
    b.append(("table", [
        ["", "Mean before", "Mean after", "Improvement", "Blocks per call"],
        ["Q1", f"{q1_before['mean']:.4f} ms", f"{q1_after['mean']:.4f} ms",
         _speedup("Q1") + " faster",
         f"{q1_before['blocks']:.0f} \u2192 {q1_after['blocks']:.0f}"],
        ["Q2", f"{q2_before['mean']:.4f} ms", f"{q2_after['mean']:.4f} ms",
         _speedup("Q2") + " faster",
         f"{q2_before['blocks']:.0f} \u2192 {q2_after['blocks']:.0f}"],
    ], [0.4, 1.4, 1.4, 1.5, 1.6]))
    p(f"Q1 is the large win, at {_speedup('Q1')}, because it went from having "
      f"no usable index to having one. Q2's {_speedup('Q2')} is the smaller "
      f"number and the more honest one: an index was already helping it, so "
      f"the composite index only removed the sort. On 14,596 rows that saves "
      f"very little wall-clock time. The reason it is still worth doing is "
      f"that the sort's cost grows with the number of rows matching the "
      f"customer while the index scan's does not, so the gap widens as the "
      f"table grows \u2014 and this table is the one that grows fastest in a "
      f"rental business.")

    # ----------------------------------------------------------------- step 3
    h("Step 3: Stored Procedures")
    p("Two objects were written, deliberately one of each kind, because the "
      "distinction is the interesting part of this step. PostgreSQL has had "
      "both CREATE FUNCTION and CREATE PROCEDURE since version 11, and they "
      "are not interchangeable.")
    p("add_customer is a FUNCTION. It inserts a customer and returns the "
      "generated customer_id, which is what a caller needs. Before inserting "
      "it checks two things: that the address looks like an email at all, and "
      "that it is not already registered. Both checks raise with a specific "
      "SQLSTATE rather than a bare error, so a caller can tell a duplicate "
      "from a malformed input without parsing the message text.")
    fig("fig-code-function.png",
        "add_customer. The validation is in the database, so it holds no "
        "matter which application does the inserting.", 5.8)
    p("deactivate_customer is a PROCEDURE. It returns nothing, and it commits "
      "its own transaction. That is the capability a procedure has and a "
      "function does not: a function runs inside the caller's transaction and "
      "cannot commit. It also checks ROW_COUNT after the UPDATE and raises if "
      "nothing matched, so asking to deactivate a customer who is already "
      "inactive is an error rather than a silent no-op.")
    fig("fig-code-procedure.png",
        f"deactivate_customer. The COMMIT on line {COMMIT_LINE} is the reason "
        f"this is a procedure.", 6.0)
    fig("fig-functions.png",
        "Both objects as PostgreSQL sees them. Note the empty returns column "
        "for the procedure.", 5.4)
    p("Both were then tested with five calls, three of which are supposed to "
      "fail. Testing only the path that works would not show that the "
      "validation does anything.")
    fig("fig-functions-test.png",
        "All five calls. The successes report through RAISE NOTICE; the three "
        "rejections each carry the SQLSTATE they were raised with.", 5.5)
    p("The results are as designed: the first call returns customer_id 600; "
      "the same address in different case is rejected as a duplicate, which "
      "confirms the comparison is case-insensitive; a string with no @ is "
      "rejected; the deactivation commits; and repeating it is refused "
      "because no active customer with that id remains. The final row shows "
      "activebool has flipped to f, so the procedure's work was committed and "
      "not rolled back.")
    p("One thing this step ran into: CALL will not accept a subquery as an "
      "argument, so fetching the id with CALL deactivate_customer((SELECT "
      "...)) fails to parse. The id is fetched into a psql variable with "
      "\\gset first and the variable passed in.")

    # ----------------------------------------------------------------- step 4
    h("Step 4: Replication Setup")
    p("The replica is a second cluster on the same host, listening on port "
      "5433 and streaming from the primary on 5432. pg_basebackup was run "
      "with -R, which writes standby.signal and the primary_conninfo into the "
      "new data directory so the copy comes up as a standby without any "
      "further configuration, and with -C -S replica1 to create a replication "
      "slot. The slot is the part worth having: it makes the primary retain "
      "WAL the replica has not consumed yet, so a replica that falls behind "
      "or disconnects can catch up instead of being unrecoverable.")
    fig("fig-basebackup.png",
        "pg_basebackup copying the cluster and creating the slot. 39,980 kB, "
        "one tablespace.", 6.2)
    p("Because the copy is byte-for-byte, it includes the primary's "
      "postgresql.conf and therefore its port. Starting it unchanged would "
      "collide with the primary, so the replica's port is overridden to 5433 "
      "afterwards.")
    fig("fig-replica-state.png",
        "The replica confirms it is in recovery \u2014 which is what a streaming "
        "standby is permanently in.", 5.4)
    fig("fig-replication.png",
        "pg_stat_replication on the primary: streaming, asynchronous, and "
        "caught up to the byte.", 6.2)
    p("sent_lsn and replay_lsn are equal, so the replica has replayed "
      "everything sent to it. sync_state is async, which is the default: the "
      "primary commits without waiting for the replica to confirm. That is "
      "the right trade for a read replica and the wrong one for zero-loss "
      "failover, which would need synchronous_commit and a synchronous "
      "standby, at the cost of every commit on the primary waiting for a "
      "network round trip.")
    p("A status view showing streaming is not by itself proof that data "
      "arrives, so it was tested directly: insert on the primary, read on the "
      "replica, then attempt a write on the replica.")
    fig("fig-replication-test.png",
        "The row inserted on 5432 read back from 5433, and the replica "
        "refusing to be written to.", 5.8)
    p("The row appears on the replica, and the attempted insert there is "
      "refused with \u201ccannot execute INSERT in a read-only transaction\u201d. "
      "Both halves matter: the first shows replication works, the second "
      "shows the replica is genuinely read-only and cannot silently diverge "
      "from the primary.")

    # ----------------------------------------------------------------- step 5
    h("Step 5: Performance Tuning")
    p("The two views the assignment names answer different questions. "
      "pg_stat_user_tables says whether a table is being read sequentially or "
      "through an index; pg_stat_user_indexes says whether each index is "
      "actually earning its place.")
    fig("fig-stats-tables.png",
        "pg_stat_user_tables. payment now has more index scans than "
        "sequential ones.", 6.2)
    fig("fig-stats-indexes.png",
        "pg_stat_user_indexes. Both new indexes are being used \u2014 and three "
        "others are not.", 6.2)
    p("The second view produced the most useful finding in this report, and "
      "it is not about the queries that were optimised. Both new indexes are "
      "being used, roughly 200 scans each, which confirms the planner chose "
      "them rather than merely being able to. But three indexes on payment "
      "have zero scans: idx_fk_rental_id, idx_fk_staff_id, and payment_pkey. "
      "An unused index is not free \u2014 every INSERT, UPDATE and DELETE on the "
      "table has to maintain it, and it occupies cache that could hold table "
      "data. Together those three hold 792 kB doing nothing for this "
      "workload.")
    p("They should not be dropped on this evidence, though. The counters were "
      "reset at the start of this exercise, so \u201czero scans\u201d means zero "
      "during a short synthetic workload of two queries, not zero in "
      "production; and payment_pkey enforces the primary key, so it earns its "
      "place regardless of whether anything reads it. The correct conclusion "
      "is that these are the candidates to watch over a representative "
      "period, not that they are dead weight.")
    fig("fig-cache.png",
        "pg_statio_user_tables: every read was served from shared_buffers.",
        6.2)
    p("The cache hit ratio is 100%, which is worth interpreting rather than "
      "celebrating. exampledb is 16 MB and the default shared_buffers is 128 "
      "MB, so the entire database fits in memory several times over. It also "
      "explains why the improvements in Step 2 are measured in microseconds: "
      "no query in this exercise ever waited on a disk. On a database larger "
      "than RAM the same index changes would show much larger gains, because "
      "the buffer reduction of 128 blocks to 17 would be 111 fewer trips to "
      "storage rather than 111 fewer memory lookups.")

    h("Configuration")
    fig("fig-tuning-before.png",
        "The defaults. shared_buffers of 128 MB on a machine with 31 GB.",
        5.6)
    p("The defaults are deliberately conservative so that PostgreSQL starts "
      "on almost anything, which means they are wrong for any real server. "
      "The values below were sized from the machine actually being used \u2014 "
      "31,560 MB of RAM across 8 cores \u2014 rather than copied from a guide.")
    b.append(("table", [
        ["Parameter", "Default", "Set to", "Reasoning"],
        ["shared_buffers", "128 MB", "7890 MB",
         "25% of RAM, the conventional starting point; PostgreSQL relies on "
         "the OS page cache for the rest"],
        ["effective_cache_size", "4 GB", "23 GB",
         "75% of RAM. Allocates nothing \u2014 it tells the planner how much "
         "caching to assume, which makes it favour index scans"],
        ["work_mem", "4 MB", "32 MB",
         "Per sort or hash, not per connection, so it multiplies; raised "
         "modestly to keep sorts out of temporary files"],
        ["maintenance_work_mem", "512 MB", "512 MB",
         "Used by CREATE INDEX and VACUUM, which run few at a time, so it can "
         "be far larger than work_mem"],
        ["random_page_cost", "4", "1.1",
         "The default assumes spinning disks. On SSD a random read costs "
         "nearly what a sequential one does, and leaving it at 4 makes the "
         "planner avoid indexes it should use"],
    ], [1.5, 0.75, 0.75, 3.3]))
    p("shared_buffers is the one that needs a restart rather than a reload, "
      "because it allocates a shared memory segment at startup. The other "
      "four would have taken a reload.")
    fig("fig-tuning-after.png",
        "The five parameters in effect after the restart, and the replica "
        "back in streaming state.", 6.2)
    p("The second half of that screenshot is there on purpose. Restarting the "
      "primary drops the replica's connection, and it reconnects on its own "
      "when it next retries \u2014 the interval is wal_retrieve_retry_interval, "
      "5 seconds by default. Querying pg_stat_replication sooner than that "
      "returns no rows and looks exactly like replication having broken, "
      "which is what happened on the first attempt at this capture.")

    # -------------------------------------------------------------- conclusion
    h("Findings and Recommendations")
    p(f"The indexes did what they were meant to. Q1 went from reading all "
      f"14,596 rows to reading 308, {_speedup('Q1')} faster over 200 runs "
      f"with buffer reads down from {q1_before['blocks']:.0f} to "
      f"{q1_after['blocks']:.0f}. Q2 kept the same speed to within a "
      f"microsecond or two but lost a Sort node, which is the change that "
      f"will matter as the table grows.")
    p("The clearer lesson is about what the numbers do and do not show. This "
      "database is 16 MB and fits entirely in cache, so every measurement "
      "here is of CPU and memory work, never of disk. That makes the "
      "millisecond figures the least transferable thing in this report and "
      "the buffer counts and plan shapes the most: those are deterministic, "
      "and on a database that does not fit in RAM they are what turns into "
      "real time.")
    p("Recommendations, in the order worth acting on:")
    b.append(("bullets", [
        "Leave pg_stat_statements enabled permanently. Every indexing "
        "decision in this report came out of it, and it costs very little.",
        "Re-check pg_stat_user_indexes after a representative period, not "
        "after a synthetic workload. Three indexes on payment show zero "
        "scans here, which is a question to investigate rather than an answer.",
        "Apply the same configuration to the replica. It was cloned before "
        "the parameters were changed, so it is still running the defaults \u2014 "
        "which is a problem the moment it is promoted or used to serve reads.",
        "Consider making the replica synchronous only if losing recently "
        "committed transactions on failover is unacceptable, and accept that "
        "every commit on the primary then waits for it.",
        "Do the indexing work again against production-sized data. The "
        "plans chosen here are correct, but the planner's choices depend on "
        "table statistics, and 14,596 rows is small enough that it will "
        "sometimes prefer a sequential scan on principle.",
    ]))
    p("A note on presentation: the shell prompts in the figures are shown as "
      "PowerShell to match the earlier assignments in this series. The psql "
      "output is unedited apart from shortening the absolute cluster paths to "
      "the short names used in this report, which setup.sh does to its own "
      "captures so that the shortening is applied consistently rather than by "
      "hand.")

    return b
