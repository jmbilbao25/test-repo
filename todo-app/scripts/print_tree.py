"""Prints the application layout for the figure in the write-up.

Only the app itself is listed. scripts/ and report/ are the tooling that builds
the write-up and its figures, so they are left out to keep the figure about the
project the assignment is asking for.

    python3 scripts/print_tree.py
"""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SKIP = {"__pycache__", ".pytest_cache", "figures", "results", ".git",
        "scripts", "report", ".preview", ".venv"}


def walk(directory: str, prefix: str = "") -> None:
    entries = sorted(
        e for e in os.listdir(directory)
        if e not in SKIP and not e.endswith((".pyc", ".json"))
    )
    dirs = [e for e in entries if os.path.isdir(os.path.join(directory, e))]
    files = [e for e in entries if not os.path.isdir(os.path.join(directory, e))]
    ordered = dirs + files
    for i, entry in enumerate(ordered):
        last = i == len(ordered) - 1
        print(prefix + ("`-- " if last else "|-- ") + entry)
        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            walk(path, prefix + ("    " if last else "|   "))


if __name__ == "__main__":
    print("todo-app/")
    walk(ROOT)
