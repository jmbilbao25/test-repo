"""Builds every figure in the write-up.

Each one is either real output that setup.sh captured into results/, or a slice
of an actual .sql file in sql/. Nothing here is retyped by hand, so a figure
cannot drift from what the database did.

The terminal styling and the SQL highlighting come from the shared renderer
written for the Day 3 assignment.

    python3 scripts/make_figures.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
FIG = os.path.join(ROOT, "figures")
RESULTS = os.path.join(ROOT, "results")
SQL = os.path.join(ROOT, "sql")

sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
try:
    from render import Renderer, numbered, terminal
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"could not import todo-app/scripts/render.py: {exc}")

CHAR_EM = 0.602
PROMPT = r"PS C:\pg\day8>"


def read(name: str, folder: str = RESULTS) -> str:
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def fit(body: str, font_size: float, cap: int = 1010) -> int:
    """Width that fits the longest line, so nothing is clipped or floating."""
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, cap))


def winprompt(body: str) -> str:
    """Show shell prompts as PowerShell, matching the Day 6 and 7 figures."""
    # A lambda, not a replacement string: the backslashes in the Windows path
    # would otherwise be read as regex escapes.
    return re.sub(r"^\$ ", lambda _: PROMPT + " ", body, flags=re.MULTILINE)


def section(text: str, start: str, end: str | None = None) -> str:
    """The part of a capture between two === markers."""
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j].rstrip()


def sql_slice(filename: str, first: str, last: str) -> tuple[str, int]:
    """Lines of a .sql file from the one containing first to the one containing
    last, with the real line number the slice starts at."""
    lines = read(filename, SQL).split("\n")
    a = next(i for i, l in enumerate(lines) if first in l)
    b = next(i for i, l in enumerate(lines) if last in l and i >= a)
    return "\n".join(lines[a:b + 1]), a + 1


def code_figure(r: Renderer, name: str, filename: str, first: str, last: str,
                width: int = 940) -> None:
    """A .sql excerpt in an editor window, with its real line numbers."""
    code, start = sql_slice(filename, first, last)
    r.shot(f"""
<div class="win" style="width:{width}px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>{filename}</div>
  </div>
  <div class="ebody">{numbered(code, "sql", start=start)}</div>
  <div class="sbar">
    <span>sql\\{filename}</span><span>PostgreSQL</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
""", out(name))


# --------------------------------------------------------------------- figures

def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    before = read("explain_before.txt")
    after = read("explain_after.txt")
    stats = read("stats.txt")

    # Terminal figures: (filename, title bar, body, font size, width cap)
    shells = [
        ("fig-setup.png", "Windows PowerShell - restore the sample database",
         winprompt(read("setup.txt")), 12, 1010),
        ("fig-schema.png", "psql - exampledb schema",
         read("schema.txt"), 12, 1010),
        ("fig-payment-table.png", "psql - \\d payment",
         read("payment_table.txt"), 11, 1010),

        ("fig-candidates.png", "psql - finding the queries worth indexing",
         read("candidates.txt"), 11.5, 1010),
        ("fig-explain-before-q1.png", "psql - EXPLAIN Q1, no index",
         section(before, "=== Q1", "=== Q2"), 10, 1060),
        ("fig-explain-before-q2.png", "psql - EXPLAIN Q2, no composite index",
         section(before, "=== Q2"), 10.5, 1060),
        ("fig-indexes.png", "psql - the two indexes, and what they cost",
         read("indexes.txt"), 12, 1010),
        ("fig-explain-after-q1.png", "psql - EXPLAIN Q1, indexed",
         section(after, "=== Q1", "=== Q2"), 10, 1060),
        ("fig-explain-after-q2.png", "psql - EXPLAIN Q2, indexed",
         section(after, "=== Q2"), 10.5, 1060),
        ("fig-benchmark.png", "psql - 200 runs of each query, before and after",
         "--- BEFORE the indexes ---\n"
         + section(read("benchmark_before.txt"), "=== mean")
         + "\n\n--- AFTER the indexes ---\n"
         + section(read("benchmark_after.txt"), "=== mean"), 11.5, 1010),

        ("fig-functions.png", "psql - the function and the procedure exist",
         read("functions.txt"), 12, 1010),
        ("fig-functions-test.png", "psql - exercising both, failures included",
         read("functions_test.txt"), 11, 1010),

        ("fig-basebackup.png", "Windows PowerShell - pg_basebackup",
         winprompt(read("basebackup.txt")), 11.5, 1010),
        ("fig-replica-state.png", "psql - the replica identifies as a replica",
         winprompt(read("replica_state.txt")), 12, 1010),
        ("fig-replication.png", "psql - pg_stat_replication on the primary",
         read("replication.txt"), 11.5, 1010),
        ("fig-replication-test.png", "psql - the replica streams, and refuses writes",
         read("replication_test.txt"), 12, 1010),

        ("fig-stats-tables.png", "psql - pg_stat_user_tables",
         section(stats, "=== pg_stat_user_tables", "=== pg_stat_user_indexes"),
         12, 1010),
        ("fig-stats-indexes.png", "psql - pg_stat_user_indexes",
         section(stats, "=== pg_stat_user_indexes", "=== cache hit"), 12, 1010),
        ("fig-cache.png", "psql - cache hit ratio",
         section(stats, "=== cache hit"), 12, 1010),
        ("fig-tuning-before.png", "psql - configuration as installed",
         read("tuning_before.txt"), 12, 1010),
        ("fig-tuning-after.png", "Windows PowerShell - after tuning and restart",
         winprompt(read("tuning_after.txt")), 12, 1010),
    ]

    # Code figures: (filename, sql file, first line, last line)
    codes = [
        ("fig-code-indexes.png", "05_indexes.sql",
         "-- Q1 filters", "ANALYZE payment;"),
        ("fig-code-function.png", "07_functions.sql",
         "CREATE OR REPLACE FUNCTION add_customer", "$$;"),
        ("fig-code-procedure.png", "07_functions.sql",
         "-- deactivate_customer is a PROCEDURE", "$$;"),
    ]

    with Renderer(scale=2) as r:
        for name, title, body, size, cap in shells:
            r.shot(terminal(title, body, width=fit(body, size, cap),
                            font_size=size, windows=True),
                   out(name))

        for name, filename, first, last in codes:
            code_figure(r, name, filename, first, last)

    print(f"\n{len(shells) + len(codes)} figures in {FIG}")


if __name__ == "__main__":
    main()
