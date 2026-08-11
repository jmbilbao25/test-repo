"""Writes the same blocks out as a PDF.

LibreOffice is not available on this machine, so the PDF is built directly rather
than converted from the .docx. Both come from the same blocks, so the wording and
the figures cannot drift apart; only the typesetting differs, since Word and
ReportLab do not break pages in the same places.
"""
from __future__ import annotations

import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                               SimpleDocTemplate, Spacer, Table, TableStyle)

FONT_DIR = "/usr/share/fonts"
SANS = "LiberationSans"
MONO = "LiberationMono"

PRINTABLE = 6.5 * inch


def _register_fonts() -> None:
    faces = [
        (SANS, "liberation-sans/LiberationSans-Regular.ttf"),
        (SANS + "-Bold", "liberation-sans/LiberationSans-Bold.ttf"),
        (SANS + "-Italic", "liberation-sans/LiberationSans-Italic.ttf"),
        (MONO, "liberation-mono/LiberationMono-Regular.ttf"),
    ]
    for name, rel in faces:
        path = os.path.join(FONT_DIR, rel)
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily(
        SANS, normal=SANS, bold=SANS + "-Bold", italic=SANS + "-Italic")


def _styles() -> dict:
    body = ParagraphStyle(
        "body", fontName=SANS, fontSize=10.5, leading=14.5, spaceAfter=8,
        textColor=colors.HexColor("#1a1a1a"))
    return {
        "body": body,
        "h1": ParagraphStyle(
            "h1", parent=body, fontName=SANS + "-Bold", fontSize=14,
            leading=18, spaceBefore=14, spaceAfter=7,
            textColor=colors.HexColor("#1f3864")),
        "day": ParagraphStyle(
            "day", parent=body, fontName=SANS + "-Bold", fontSize=11.5,
            alignment=TA_CENTER, spaceAfter=2),
        "title": ParagraphStyle(
            "title", parent=body, fontName=SANS + "-Bold", fontSize=17,
            leading=21, alignment=TA_CENTER, spaceAfter=6),
        "sub": ParagraphStyle(
            "sub", parent=body, fontSize=10, leading=14, alignment=TA_CENTER,
            spaceAfter=16),
        "caption": ParagraphStyle(
            "caption", parent=body, fontName=SANS + "-Italic", fontSize=8.5,
            leading=11, alignment=TA_CENTER, spaceBefore=3, spaceAfter=13,
            textColor=colors.HexColor("#595959")),
        "code": ParagraphStyle(
            "code", parent=body, fontName=MONO, fontSize=8.5, leading=11.5,
            leftIndent=10, spaceAfter=0, spaceBefore=0,
            backColor=colors.HexColor("#F2F2F2")),
        "cell": ParagraphStyle(
            "cell", parent=body, fontSize=9.5, leading=12.5, spaceAfter=0),
        "cellhead": ParagraphStyle(
            "cellhead", parent=body, fontName=SANS + "-Bold", fontSize=9.5,
            leading=12.5, spaceAfter=0),
        "note": ParagraphStyle(
            "note", parent=body, fontSize=9.5, leading=13,
            leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4,
            borderWidth=0.6, borderColor=colors.HexColor("#C9CEDA"),
            borderPadding=7, backColor=colors.HexColor("#F4F6FA")),
    }


def write(blocks, out_path: str, fig_dir: str, meta) -> int:
    _register_fonts()
    st = _styles()

    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
        title=meta.TITLE, author=meta.AUTHOR,
    )

    story: list = [
        Paragraph(meta.DAY, st["day"]),
        Paragraph(meta.TITLE, st["title"]),
        Paragraph(f"{meta.AUTHOR}<br/>{meta.COURSE}<br/>{meta.DATE}",
                  st["sub"]),
    ]

    fig_no = 0

    for block in blocks:
        kind = block[0]

        if kind == "h1":
            story.append(Paragraph(block[1], st["h1"]))

        elif kind == "p":
            story.append(Paragraph(block[1], st["body"]))

        elif kind == "code":
            for line in block[1]:
                story.append(Paragraph(
                    (line or " ").replace(" ", "&nbsp;"), st["code"]))
            story.append(Spacer(1, 10))

        elif kind == "fig":
            _, filename, caption, width_in = block
            path = os.path.join(fig_dir, filename)
            with PILImage.open(path) as im:
                ratio = im.height / im.width
            width = min(width_in * inch, PRINTABLE)
            fig_no += 1
            # Keep the picture and its caption on the same page.
            story.append(KeepTogether([
                Image(path, width=width, height=width * ratio),
                Paragraph(f"Figure {fig_no}: {caption}", st["caption"]),
            ]))

        elif kind == "table":
            rows, widths = block[1], block[2]
            data = [[Paragraph(c, st["cellhead"]) for c in rows[0]]]
            data += [[Paragraph(str(c), st["cell"]) for c in row]
                     for row in rows[1:]]
            table = Table(data, colWidths=[w * inch for w in widths],
                          repeatRows=1)
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5,
                 colors.HexColor("#9AA3B2")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF1F6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
            story.append(Spacer(1, 12))

        elif kind == "bullets":
            for item in block[1]:
                story.append(Paragraph(
                    item, ParagraphStyle("b", parent=st["body"],
                                         leftIndent=16, bulletIndent=5,
                                         spaceAfter=4),
                    bulletText="\u2022"))
            story.append(Spacer(1, 6))

        elif kind == "note":
            story.append(Paragraph(block[1], st["note"]))
            story.append(Spacer(1, 10))

        elif kind == "break":
            story.append(PageBreak())

        else:
            raise ValueError(f"unknown block: {kind}")

    # A spacer left at the very end can spill onto a page of its own, which
    # shows up as a blank final page.
    while story and isinstance(story[-1], Spacer):
        story.pop()

    doc.build(story)
    return fig_no
