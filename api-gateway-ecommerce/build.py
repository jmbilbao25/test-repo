"""Builds the write-up as a .docx and a .pdf.

Both writers are the ones from the Day 3 assignment, imported rather than
copied, so every write-up in this repo keeps the same typography.

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

NAME = "API-Gateway-Service-Communication-Assignment"


def main() -> None:
    blocks = content.blocks()

    used = [b[1] for b in blocks if b[0] == "fig"]
    missing = sorted({name for name in used
                      if not os.path.exists(os.path.join(FIG, name))})
    if missing:
        raise SystemExit("missing figures: " + ", ".join(missing) +
                         "\nrun ./run.sh then scripts/make_figures.py first")

    on_disk = {f for f in os.listdir(FIG) if f.endswith(".png")}
    unused = sorted(on_disk - set(used))
    if unused:
        print("note: figures generated but not used:", ", ".join(unused))

    for writer, ext in ((docx_writer, "docx"), (pdf_writer, "pdf")):
        path = os.path.join(REPO, f"{NAME}.{ext}")
        figures = writer.write(blocks, path, FIG, content)
        print(f"wrote {path}  ({figures} figures)")


if __name__ == "__main__":
    main()
