"""Builds the assignment write-up as a .docx and a .pdf.

Both come out of report/content.py, so the two files always say the same thing.

    python3 build_report.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FIG = os.path.join(HERE, "figures")
sys.path.insert(0, HERE)

from report import content, docx_writer, pdf_writer

NAME = "AI-Tools-ToDo-Assignment"


def main() -> None:
    blocks = content.blocks()

    missing = sorted({b[1] for b in blocks if b[0] == "fig"
                      if not os.path.exists(os.path.join(FIG, b[1]))})
    if missing:
        raise SystemExit(
            "missing figures: " + ", ".join(missing) +
            "\nrun scripts/capture_app.py and scripts/render_figures.py first")

    docx_path = os.path.join(REPO, NAME + ".docx")
    pdf_path = os.path.join(REPO, NAME + ".pdf")

    figures = docx_writer.write(blocks, docx_path, FIG, content)
    print(f"wrote {docx_path}  ({figures} figures)")

    figures = pdf_writer.write(blocks, pdf_path, FIG, content)
    print(f"wrote {pdf_path}  ({figures} figures)")


if __name__ == "__main__":
    main()
