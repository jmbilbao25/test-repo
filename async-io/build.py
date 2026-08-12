"""Builds the write-up as a .docx and a .pdf.

The two writers are the ones from the Day 3 assignment and are imported from
there rather than copied, so a fix to either format applies to both write-ups.

    python3 build.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FIG = os.path.join(HERE, "figures")

sys.path.insert(0, os.path.join(REPO, "todo-app"))
sys.path.insert(0, HERE)

import content
from report import docx_writer, pdf_writer  # todo-app/report

NAME = "Async-IO-Assignment"


def main() -> None:
    blocks = content.blocks()

    missing = sorted({b[1] for b in blocks if b[0] == "fig"
                      if not os.path.exists(os.path.join(FIG, b[1]))})
    if missing:
        raise SystemExit("missing figures: " + ", ".join(missing) +
                         "\nrun scripts/make_figures.py first")

    for writer, ext in ((docx_writer, "docx"), (pdf_writer, "pdf")):
        path = os.path.join(REPO, f"{NAME}.{ext}")
        figures = writer.write(blocks, path, FIG, content)
        print(f"wrote {path}  ({figures} figures)")


if __name__ == "__main__":
    main()
