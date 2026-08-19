"""Builds the psql figures in the write-up.

Each one is real output that setup.sh captured into results/. Nothing here is
retyped by hand, so a figure cannot drift from what the database did.

The pgAdmin figures are not built here -- they are screenshots of the real
application, taken by capture_pgadmin.py.

The terminal styling comes from the shared renderer written for the Day 3
assignment.

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

sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
try:
    from render import Renderer, terminal
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"could not import todo-app/scripts/render.py: {exc}")

CHAR_EM = 0.602
PROMPT = r"PS C:\ewb\lab>"


def read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def fit(body: str, font_size: float, cap: int = 1010) -> int:
    """Width that fits the longest line, so nothing is clipped or floating."""
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, cap))


def winprompt(body: str) -> str:
    """Show shell prompts as PowerShell, matching the earlier assignments."""
    # A lambda, not a replacement string: the backslashes in the Windows path
    # would otherwise be read as regex escapes.
    return re.sub(r"^\$ ", lambda _: PROMPT + " ", body, flags=re.MULTILINE)


def frm(text: str, start: str) -> str:
    """The capture from the line containing start onwards.

    psql -a echoes the whole file, header comments included; the figures only
    want the part from the first statement on.
    """
    return text[text.index(start):].rstrip()


def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    transfer = read("transfer_commit.txt")
    rollback = read("overdraw_rollback.txt")

    # (filename, title bar, body, font size, width cap)
    shells = [
        ("fig-setup.png", "Windows PowerShell - build the cluster and ewb_core",
         winprompt(read("setup.txt")), 12, 1010),

        ("fig-create-accounts.png", "psql - ewb_accounts, and its constraints",
         read("create_accounts.txt"), 9.5, 1060),
        ("fig-constraint-tests.png",
         "psql - both invalid inserts, refused by the database",
         read("constraint_tests.txt"), 10, 1060),

        ("fig-seed.png", "psql - the two valid accounts",
         read("seed_accounts.txt"), 12, 1010),
        ("fig-create-ledger.png",
         "psql - ewb_transactions, and the foreign key it carries",
         read("create_transactions.txt"), 9, 1060),
        ("fig-fk-test.png",
         "psql - the foreign key and the ledger CHECKs, tested",
         read("fk_test.txt"), 10, 1060),
        ("fig-queries.png", "psql - filtering and aggregation",
         read("queries.txt"), 12, 1010),

        ("fig-transfer.png", "psql - the transfer, one statement at a time",
         frm(transfer, "BEGIN;"), 11.5, 1010),
        ("fig-verify-transfer.png", "psql - balances and ledger after COMMIT",
         read("verify_transfer.txt"), 11, 1010),
        ("fig-rollback.png", "psql - the overdrawn transfer, and ROLLBACK",
         frm(rollback, "BEGIN;"), 11, 1060),
        ("fig-verify-rollback.png",
         "psql - nothing partial survived the rollback",
         read("verify_rollback.txt"), 11, 1010),
    ]

    with Renderer(scale=2) as r:
        for name, title, body, size, cap in shells:
            r.shot(terminal(title, body, width=fit(body, size, cap),
                            font_size=size, windows=True),
                   out(name))

    print(f"\n{len(shells)} psql figures in {FIG}")


if __name__ == "__main__":
    main()
