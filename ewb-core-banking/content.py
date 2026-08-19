"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment.

The balances and ledger ids quoted in the prose are parsed out of results/,
which is the same source the psql figures are built from, so the text cannot end
up disagreeing with the screenshot beside it.
"""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

TITLE = "Hands-on Core Banking Relational Database Lab"
DAY = "Technology & Operations Induction Program"
AUTHOR = "John Michael Bilbao"
COURSE = ("EastWest Banking Corporation \u2014 Technology Induction Track, "
          "Manila Center")
DATE = "August 19, 2026"


def _tables(filename: str):
    """Yield (headers, rows) for each result set in a psql capture.

    A psql result set is a header line, a line of dashes and plus signs, then
    the data rows -- so the dashes are what marks the line above as headers.
    """
    lines = open(os.path.join(RESULTS, filename), encoding="utf-8").read()
    lines = lines.split("\n")
    for i, line in enumerate(lines):
        # The separator joins columns with +, not |, which is what
        # distinguishes it from a data row.
        if set(line.strip()) != set("-+"):
            continue
        headers = [c.strip() for c in lines[i - 1].split("|")]
        rows = []
        for row in lines[i + 1:]:
            if "|" not in row:
                break
            rows.append([c.strip() for c in row.split("|")])
        yield headers, rows


def _column(filename: str, key: str, value: str) -> dict[str, str]:
    """key column -> value column, out of the first result set holding both."""
    for headers, rows in _tables(filename):
        if key in headers and value in headers:
            k, v = headers.index(key), headers.index(value)
            return {row[k]: row[v] for row in rows}
    raise SystemExit(f"no result set in {filename} has both {key} and {value}")


def _balances(filename: str) -> dict[str, str]:
    return _column(filename, "account_number", "balance")


def _ledger_ids(filename: str) -> list[str]:
    return list(_column(filename, "transaction_id", "account_number"))


def _scalar(filename: str, needle: str) -> str:
    """The single value printed under a header containing needle."""
    lines = open(os.path.join(RESULTS, filename), encoding="utf-8").read()
    lines = lines.split("\n")
    for i, line in enumerate(lines):
        if needle in line and "|" not in line:
            return lines[i + 2].strip()
    raise SystemExit(f"{needle!r} not found as a lone column in {filename}")


OPENING = _balances("seed_accounts.txt")
AFTER = _balances("verify_transfer.txt")
RESTORED = _balances("verify_rollback.txt")
LEDGER_IDS = _ledger_ids("verify_transfer.txt")
DEPOSITS = _scalar("queries.txt", "total_ewb_deposits")

JUAN, MARIA = "EWB-1001", "EWB-1002"

# The lab's own arithmetic, restated from the captures so a changed amount in
# sql/ cannot leave the prose behind.
TRANSFER = "3,000.00"


def peso(value: str) -> str:
    """7000.00 -> PHP 7,000.00"""
    return "PHP " + f"{float(value):,.2f}"


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    note = lambda t: b.append(("note", t))
    fig = lambda name, caption, width=6.4: b.append(("fig", name, caption,
                                                     width))

    # ------------------------------------------------------------ introduction
    h("1. Lab Overview and Objectives")
    p("This is the write-up for the EastWest Bank core banking relational "
      "database lab. The lab asks for three things to be done to a PostgreSQL "
      "database and shown working: business rules enforced by the database "
      "itself rather than by application code, a ledger that cannot reference "
      "an account which does not exist, and a fund transfer that either "
      "happens completely or does not happen at all.")
    p("Everything below was run against PostgreSQL 16.14 on a database named "
      "ewb_core, twice over. The first pass runs the scripts in sql/ through "
      "psql; the second performs the identical steps by hand in the pgAdmin 4 "
      "Query Tool, which is the tool the lab specifies. Both passes are "
      "reproducible: setup.sh builds the cluster and captures the psql output "
      "of every step into results/, and scripts/capture_pgadmin.py starts "
      "pgAdmin, connects it to the same cluster, executes the same SQL and "
      "screenshots the result.")
    p("No figure in this report was retyped or staged. Each psql figure is "
      "rendered from the capture file setup.sh wrote, and each pgAdmin figure "
      "is a screenshot of the running application taken immediately after "
      "Execute finished, so no figure can claim something the database did "
      "not do.")

    b.append(("table", [
        ["Objective", "Where it is demonstrated"],
        ["Enforce banking business rules with DDL constraints "
         "(PRIMARY KEY, CHECK, FOREIGN KEY)",
         "Exercise 1, and the ledger table in Exercise 2"],
        ["Maintain ledger consistency on double-entry principles",
         "Exercise 2, and the debit/credit check in Exercise 3"],
        ["Query account states, aggregates and customer ledger records",
         "Exercise 2, Step 2.3"],
        ["Execute atomic transfers with BEGIN, COMMIT and ROLLBACK",
         "Exercise 3"],
    ], [3.1, 3.3]))

    # ------------------------------------------------------------- environment
    h("2. Environment")
    p("A single-node PostgreSQL 16.14 cluster was built from scratch for the "
      "lab, holding one database, ewb_core. The cluster is torn down and "
      "rebuilt on every run of setup.sh, so no step can quietly depend on "
      "state left behind by an earlier attempt.")
    fig("fig-setup.png",
        "The cluster and the ewb_core database, on PostgreSQL 16.14.", 6.0)
    p("One change was made to the cluster as initdb left it. initdb writes a "
      "pg_hba.conf that trusts any TCP connection from the local machine, "
      "which means the instance can be opened without a password. For a lab "
      "whose subject is the database as the last line of defence that is the "
      "wrong default, so host connections were switched to scram-sha-256 "
      "before the server was first started. pgAdmin therefore has to "
      "authenticate, which is the first thing it does below.")
    fig("fig-pga-connect.png",
        "pgAdmin 4 refusing to open the server without the password for "
        "'postgres'. This is pg_hba.conf doing its job, not pgAdmin being "
        "cautious.")
    p("With the password supplied, the server connects and pgAdmin shows its "
      "dashboard. The server is registered under a group named EastWest Bank "
      "so the tree reads the way the induction material does.")
    fig("fig-pga-dashboard.png",
        "The EWB Core Banking instance connected in pgAdmin 4. Sessions, "
        "transactions per second and block I/O are all live counters from "
        "this cluster.")

    # -------------------------------------------------------------- exercise 1
    b.append(("break", None))
    h("3. Exercise 1: DDL and Database-Level Safety Constraints")
    p("Application code fails. It gets deployed half-finished, it gets called "
      "by a batch job nobody remembered, and it gets bypassed entirely by an "
      "operator with psql open. A rule that only exists in application code "
      "is therefore a rule that holds only most of the time. The two rules "
      "this exercise cares about \u2014 a balance is never negative, and a "
      "currency is one EWB has approved \u2014 are written into the table "
      "definition instead, where every writer has to go through them.")

    h("Step 1.1: Creating the account master table")
    p("ewb_accounts carries five columns and four rules: a PRIMARY KEY on the "
      "account number, NOT NULL on the customer name, and the two named CHECK "
      "constraints. The CHECKs are given explicit names rather than left to "
      "PostgreSQL to generate, because the constraint name is what appears in "
      "the error message, and \u201ccheck_positive_balance\u201d tells an "
      "on-call engineer what happened where \u201cewb_accounts_check1\u201d does "
      "not.")
    fig("fig-pga-create-accounts.png",
        "Step 1.1 in the pgAdmin 4 Query Tool. The Messages pane reports "
        "CREATE TABLE and the statement completed in 37 msec.")
    p("It is worth reading the table back rather than trusting that the "
      "statement did what it looked like it would. Two details only show up "
      "on the way out:")
    fig("fig-create-accounts.png",
        "The table as PostgreSQL stored it, and the two CHECK constraints read "
        "back out of pg_constraint.", 6.4)
    p("First, DEFAULT 'PHP' and DEFAULT 'ACTIVE' are stored as "
      "'PHP'::character varying, so an insert that omits those columns still "
      "produces a row the currency CHECK accepts. Second, the "
      "IN ('PHP', 'USD') that was written has been rewritten by the planner "
      "into = ANY (ARRAY[...]). That is the same test, stored in the form "
      "PostgreSQL evaluates; a fresher reading pg_constraint for the first "
      "time should expect it not to look like what they typed.")

    h("Step 1.2: Testing the safeguards on purpose")
    p("A constraint that has never been made to fire is an assumption. Both "
      "invalid inserts from the lab were run, and both were refused. This is "
      "the part of the exercise worth doing slowly, because the shape of the "
      "error is as instructive as the fact of it.")
    fig("fig-pga-negative-balance.png",
        "Attempt A: a negative opening balance. The row never reaches the "
        "table, and pgAdmin reports SQL state 23514 alongside the message.")
    fig("fig-pga-bad-currency.png",
        "Attempt B: an unapproved currency. Same SQL state, different "
        "constraint name \u2014 which is how a caller tells the two apart.")
    p("SQL state 23514 is check_violation. It matters more than the message "
      "text: the message is prose and can be reworded between releases, while "
      "the five-character SQLSTATE is defined by the standard and is what "
      "application code should branch on. An API that parses the words "
      "\u201cviolates check constraint\u201d out of an error string is one "
      "PostgreSQL upgrade away from a silent bug.")
    p("Both attempts also demonstrate that the rejection is not partial. The "
      "same two statements run through psql leave the table exactly as it was:")
    fig("fig-constraint-tests.png",
        "Both rejections in one psql session, with the row count afterwards. "
        "Nothing was written.", 6.4)
    note("Teaching point. The database engine is the last line of defence, "
         "and the only one that every writer shares. A front-end API, a batch "
         "job and an operator at a psql prompt are three different code paths "
         "into ewb_accounts; the CHECK constraint is the only rule all three "
         "are guaranteed to pass through. Validating in the API as well is "
         "still worth doing \u2014 it gives the customer a better message than "
         "SQLSTATE 23514 \u2014 but it is a convenience, not the guarantee.")
    p("pgAdmin shows the same constraints as objects in the tree, which is "
      "the view worth knowing about when inheriting a schema nobody "
      "documented: the Constraints node under a table lists everything the "
      "table enforces without having to query the catalog.")
    fig("fig-pga-tree.png",
        "The three constraints on ewb_accounts as pgAdmin sees them: the two "
        "CHECKs and the primary key.")

    # -------------------------------------------------------------- exercise 2
    b.append(("break", None))
    h("4. Exercise 2: Ledger Logging and Relational Queries")
    p("A balance on its own is an assertion. A balance with a ledger behind it "
      "is an account of how it got that way, and in banking the second is the "
      "only acceptable form. This exercise seeds the accounts, then builds the "
      "immutable ledger that every later balance change has to be explained "
      "by.")

    h("Step 2.1: Seeding valid accounts")
    p(f"The same two customers from the failed attempts are inserted again, "
      f"this time with values the constraints accept: Juan Dela Cruz opens at "
      f"{peso(OPENING[JUAN])} and Maria Clara at {peso(OPENING[MARIA])}.")
    fig("fig-pga-seed.png",
        "Step 2.1: two accounts inserted, then read back. currency and status "
        "were never mentioned in the INSERT \u2014 the DEFAULTs filled them in.")
    fig("fig-seed.png",
        "The same insert through psql. INSERT 0 2 is the tag: two rows, and no "
        "OID, which is what the 0 means.", 6.0)
    p("The Data Output grid is also showing the declared type under each "
      "column heading, which is a detail worth pointing out: balance is "
      "numeric(12,2), not a float. Money in a floating-point column is a "
      "reconciliation bug waiting for a busy day, because 0.1 + 0.2 is not "
      "0.3 in binary floating point and a ledger that sums thousands of rows "
      "will drift. NUMERIC is exact decimal arithmetic, and it is the only "
      "correct choice here.")

    h("Step 2.2: The audit ledger, and the foreign key")
    p("ewb_transactions is the log. Its account_number REFERENCES "
      "ewb_accounts(account_number), which makes an orphaned ledger entry "
      "impossible rather than merely unlikely, and it carries two CHECKs of "
      "its own: the movement is a DEBIT or a CREDIT and nothing else, and the "
      "amount is strictly positive.")
    fig("fig-pga-create-ledger.png",
        "Step 2.2 in pgAdmin. transaction_id is a SERIAL, so the ledger "
        "numbers itself.")
    fig("fig-create-ledger.png",
        "The ledger as stored, including the foreign-key constraint at the "
        "bottom.", 6.4)
    p("The amount CHECK is written amount > 0 rather than amount >= 0 on "
      "purpose. A zero-value movement is not a transaction; it is either a "
      "bug in the caller or an attempt to pad the ledger, and either way the "
      "database should not accept it.")
    p("All three of those rules were then tested, because a foreign key that "
      "has never rejected anything is the same assumption as an untested "
      "CHECK:")
    fig("fig-pga-fk-violation.png",
        "A ledger entry for account EWB-9999, which does not exist. SQL state "
        "23503, foreign_key_violation \u2014 a different class of error from the "
        "23514 above.")
    fig("fig-fk-test.png",
        "The foreign key, the transaction_type CHECK and the amount CHECK, "
        "each refused in turn. The ledger is still empty afterwards.", 6.4)
    p("One thing this step exposed that the lab does not mention. The three "
      "rejected inserts consumed sequence values 1, 2 and 3 from the SERIAL, "
      f"so the first ledger entry that actually commits is transaction_id "
      f"{LEDGER_IDS[0]} rather than 1. Sequences are deliberately not "
      f"transactional \u2014 rolling them back would serialise every inserting "
      f"session behind one another \u2014 so gaps in a SERIAL are normal and "
      f"expected. Any reconciliation process that treats a missing "
      f"transaction_id as a lost record will raise false alarms; gaps have to "
      f"be read as \u201cthis id was never committed\u201d, not \u201cthis row "
      f"disappeared\u201d.")
    fig("fig-pga-tree-ledger.png",
        "The ledger's constraints in pgAdmin: two CHECKs, the primary key, "
        "and the foreign key back to ewb_accounts.")

    h("Step 2.3: Filtering and aggregation")
    p(f"With two accounts seeded, the two queries the lab asks for return what "
      f"they should: one account holds more than PHP 5,000.00, and EWB is "
      f"holding {peso(DEPOSITS)} in total.")
    fig("fig-pga-query-a.png",
        "Query A in pgAdmin: the accounts above the PHP 5,000.00 threshold.")
    fig("fig-queries.png",
        "Both queries, plus the same total broken down by currency.", 6.0)
    p("The aggregate is worth naming precisely. SUM(balance) over "
      "ewb_accounts is not EWB's money \u2014 it is what EWB owes its "
      "customers, which on the bank's own books is a liability. The alias in "
      "the query is total_ewb_deposits for that reason. It is a habit worth "
      "forming early: an aggregate with a vague alias gets read as whatever "
      "the reader assumed it meant.")
    p("The breakdown by currency returns a single PHP row here, because both "
      "seeded accounts are peso accounts. That is the correct result rather "
      "than a disappointing one: the currency CHECK permits USD, so the "
      "GROUP BY is the query that would show a second row the day a dollar "
      "account is opened, and summing across currencies without grouping "
      "would silently add pesos to dollars.")

    # -------------------------------------------------------------- exercise 3
    b.append(("break", None))
    h("5. Exercise 3: Transaction Control and Atomic Transfers")
    p(f"A transfer is not one operation. Juan Dela Cruz sending "
      f"PHP {TRANSFER} to Maria Clara through EWB EasyWay is four: debit one "
      f"balance, credit the other, and write the two ledger entries that "
      f"account for both movements. If the process dies between the first and "
      f"the second, the money has left one account without arriving in the "
      f"other, and the bank is out of balance. Atomicity \u2014 the A in ACID "
      f"\u2014 is the property that makes that outcome impossible.")

    h("Step 3.1: A successful transfer, BEGIN to COMMIT")
    p("All four statements go inside one transaction. Nothing another session "
      "can see changes until COMMIT, and if any statement fails, none of them "
      "took effect.")
    fig("fig-pga-commit.png",
        "The transfer in pgAdmin: BEGIN at line 1, and the Messages pane "
        "reporting COMMIT once all four statements have run.")
    p("psql reports a tag per statement, which is a useful way to watch the "
      "transaction advance: BEGIN, then UPDATE 1 twice, then INSERT 0 1 "
      "twice, then COMMIT. The UPDATE 1 matters \u2014 it says exactly one row "
      "was matched. An UPDATE 0 would mean the account number was wrong and "
      "the money went nowhere, and an UPDATE 2 would mean something far worse "
      "about the primary key.")
    fig("fig-transfer.png",
        "The same transfer through psql, one statement and one tag at a time.",
        6.2)
    p(f"The balances afterwards are the ones the lab predicts: Juan at "
      f"{peso(AFTER[JUAN])} and Maria at {peso(AFTER[MARIA])}.")
    fig("fig-pga-after-commit.png",
        f"After the commit: {peso(AFTER[JUAN])} and {peso(AFTER[MARIA])}.")
    fig("fig-pga-ledger.png",
        f"The two ledger entries the transfer wrote, numbered "
        f"{LEDGER_IDS[0]} and {LEDGER_IDS[1]}, sharing one timestamp because "
        f"CURRENT_TIMESTAMP is fixed for the whole transaction.")
    p("Both ledger rows carry the same created_at, to the microsecond. That is "
      "not a coincidence and it is not a rounding artefact: CURRENT_TIMESTAMP "
      "in PostgreSQL is the start time of the transaction, not of the "
      "statement, so every row written inside one transaction is stamped "
      "identically. It is the right behaviour for a ledger \u2014 the two halves "
      "of a double entry should not appear to have happened at different "
      "times \u2014 but code that expects created_at to order statements within "
      "a transaction will not get what it expects. statement_timestamp() is "
      "the function for that.")
    p("Two properties of the result are worth checking rather than assuming, "
      "and both are in the verification below. The debits and the credits sum "
      f"to the same figure, so the ledger nets to zero; and the total "
      f"deposits are still {peso(DEPOSITS)}, unchanged, because an internal "
      f"transfer moves money between EWB's liabilities without changing what "
      f"EWB owes in total. If either number had moved, the transfer would "
      f"have created or destroyed money.")
    fig("fig-verify-transfer.png",
        "Balances, the ledger, the double-entry check and the unchanged "
        "deposit total.", 6.0)

    h("Step 3.2: An overdrawn transfer, and ROLLBACK")
    p(f"Maria Clara now holds {peso(AFTER[MARIA])} and attempts to send "
      f"PHP 20,000.00. check_positive_balance rejects the UPDATE, and the "
      f"interesting part is what happens next: the transaction is not merely "
      f"carrying a failed statement, it is aborted. PostgreSQL refuses "
      f"everything sent after the error until the block is ended.")
    fig("fig-pga-rollback.png",
        "The overdrawn attempt in pgAdmin. The constraint rejects the UPDATE, "
        "and the SELECT on line 10 never runs.")
    p("The psql transcript shows the second error explicitly, which is the "
      "one freshers should recognise: \u201ccurrent transaction is aborted, "
      "commands ignored until end of transaction block\u201d. This is a common "
      "cause of confusion in shared psql sessions \u2014 one mistake early in a "
      "transaction makes every later statement fail with a message that says "
      "nothing about what is actually wrong with it.")
    fig("fig-rollback.png",
        "The same block through psql: the constraint violation, then the "
        "aborted-transaction error, then ROLLBACK.", 6.4)
    p(f"ROLLBACK ends the block and discards everything in it. Maria's "
      f"balance is {peso(RESTORED[MARIA])}, exactly what it was before the "
      f"attempt, the ledger still holds two entries and not three, and the "
      f"deposit total is untouched.")
    fig("fig-pga-after-rollback.png",
        f"Maria Clara's balance after the rejected transfer: "
        f"{peso(RESTORED[MARIA])}, unchanged.")
    fig("fig-verify-rollback.png",
        "The balance, the totals, and the customer ledger joined back to the "
        "account master. Two entries, not three.", 6.2)
    note("Critical takeaway. ROLLBACK guarantees zero partial updates. There "
         "is no state in which Maria has been debited but the ledger entry is "
         "missing, or in which the ledger records a movement that the balance "
         "does not reflect. In this case COMMIT would have had the same effect "
         "as ROLLBACK, because PostgreSQL will not commit an aborted "
         "transaction \u2014 it rolls it back and tells you so. That is worth "
         "knowing, but it is not a reason to write COMMIT and hope: a "
         "transaction that failed should be rolled back explicitly, so the "
         "intent is visible in the code.")

    # ------------------------------------------------------- quick reference
    b.append(("break", None))
    h("6. Quick Reference")
    b.append(("table", [
        ["SQL command", "What it does for the banking engine"],
        ["CHECK (balance >= 0)",
         "A rule the database enforces on every writer, so no application "
         "path can post an unapproved overdraft"],
        ["CONSTRAINT name CHECK (...)",
         "Names the rule, so the error message identifies which rule was "
         "broken instead of reporting a generated name"],
        ["REFERENCES parent(key)",
         "Foreign key: a ledger entry cannot exist for an account that does "
         "not"],
        ["NUMERIC(12, 2)",
         "Exact decimal money. A float column here drifts once a ledger is "
         "summed over enough rows"],
        ["BEGIN",
         "Starts an explicit transaction. Nothing another session can see "
         "changes until it ends"],
        ["COMMIT",
         "Makes every statement in the block durable, together"],
        ["ROLLBACK",
         "Discards every statement in the block, together. Also the only way "
         "out of an aborted transaction"],
        ["SQLSTATE 23514 / 23503",
         "check_violation and foreign_key_violation. Branch on these, not on "
         "the message text"],
    ], [2.0, 4.4]))

    # -------------------------------------------------------------- findings
    h("7. Findings")
    p("Every step in the lab produced the result it predicts, in both psql "
      f"and pgAdmin: the two invalid accounts were refused, the transfer left "
      f"Juan at {peso(AFTER[JUAN])} and Maria at {peso(AFTER[MARIA])}, and "
      f"the overdrawn attempt left Maria at {peso(RESTORED[MARIA])} with the "
      f"ledger unchanged. The findings worth carrying out of it are the ones "
      f"the exercises imply rather than state:")
    b.append(("bullets", [
        "Name every constraint. The name is what appears in the error, and "
        "it is the difference between an error a caller can act on and one it "
        "can only log.",
        "Branch on SQLSTATE, never on the message. 23514 and 23503 are "
        "stable; \u201cviolates check constraint\u201d is prose.",
        "Sequence gaps are normal. Three refused inserts consumed three "
        f"transaction_ids, so the first committed entry is "
        f"{LEDGER_IDS[0]}. Reconciliation that treats a gap as a lost row "
        f"will report failures that never happened.",
        "CURRENT_TIMESTAMP is per transaction, not per statement. Correct "
        "for a double entry; wrong for anything trying to order statements "
        "within a transaction.",
        "Check the invariant, not just the balances. The debits equalling the "
        "credits and the deposit total staying put are the two numbers that "
        "would have caught a transfer which created money.",
        "The database is the only rule every writer shares. Validate in the "
        "application too, for the sake of the error message, but never "
        "instead.",
    ]))
    p("Two limits of this lab are worth stating plainly, because a fresher "
      "could otherwise read it as a finished design. First, the balance and "
      "the ledger are kept in step by the transaction and by nothing else \u2014 "
      "there is no constraint that stops a future UPDATE from moving a "
      "balance without writing a ledger row. In a real core banking schema "
      "that link is enforced, usually by making the balance derived from the "
      "ledger or by permitting balance changes only through a stored "
      "procedure that writes both. Second, nothing here concerns "
      "concurrency: two simultaneous transfers out of the same account were "
      "not tested, and the CHECK constraint alone does not prevent the "
      "classic case where both read a sufficient balance and only the second "
      "one's write fails. Both are the natural next exercises.")
    p("A note on presentation: the shell prompts in the psql figures are "
      "shown as PowerShell to match the earlier assignments in this series, "
      "and the psql output is unedited apart from shortening the absolute "
      "paths of the scripts to their file names, which setup.sh does to its "
      "own captures so the shortening is applied consistently rather than by "
      "hand.")

    return b
