"""Turns HTML into PNG with headless Chromium, plus the pieces the figures share.

Used by render_figures.py. Everything is laid out in HTML and CSS and then
photographed, which keeps the text crisp and the spacing consistent.
"""
from __future__ import annotations

import html as html_mod
import os
import re

from playwright.sync_api import sync_playwright

MONO = '"DejaVu Sans Mono", "Liberation Mono", monospace'
SANS = '"Liberation Sans", "DejaVu Sans", sans-serif'

# Roughly the VS Code Dark+ palette.
INK = "#d4d4d4"
BG = "#1e1e1e"
KEYWORD = "#569cd6"
STRING = "#ce9178"
COMMENT = "#6a9955"
FUNC = "#dcdcaa"
CLASS = "#4ec9b0"
NUMBER = "#b5cea8"
DECORATOR = "#dcdcaa"
SELF = "#9cdcfe"
GHOST = "#6b6b6b"


def esc(text: str) -> str:
    return html_mod.escape(text, quote=False)


# --------------------------------------------------------------- highlighting
def highlight(code: str, lang: str = "python") -> str:
    """Syntax highlight with Pygments, using inline colours from the palette."""
    from pygments import highlight as pyg_highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
    from pygments.style import Style
    from pygments.token import (Comment, Error, Keyword, Name, Number,
                                Operator, Punctuation, String, Text)

    class Dark(Style):
        background_color = BG
        styles = {
            Text: INK,
            Comment: f"italic {COMMENT}",
            Keyword: KEYWORD,
            Keyword.Constant: KEYWORD,
            Keyword.Namespace: KEYWORD,
            Operator: INK,
            Operator.Word: KEYWORD,
            Punctuation: INK,
            Name: INK,
            Name.Builtin: CLASS,
            Name.Builtin.Pseudo: SELF,
            Name.Function: FUNC,
            Name.Function.Magic: FUNC,
            Name.Class: CLASS,
            Name.Decorator: DECORATOR,
            Name.Exception: CLASS,
            Name.Attribute: SELF,
            Name.Variable: SELF,
            Name.Tag: KEYWORD,
            String: STRING,
            String.Doc: STRING,
            String.Interpol: SELF,
            String.Escape: SELF,
            Number: NUMBER,
            Error: INK,
        }

    formatter = HtmlFormatter(style=Dark, nowrap=True, noclasses=True)
    out = pyg_highlight(code, get_lexer_by_name(lang), formatter)
    return out.rstrip("\n")


def numbered(code: str, lang: str = "python", start: int = 1,
             ghost_from: int | None = None) -> str:
    """Highlighted code with a gutter. Lines from ghost_from on are grey.

    The grey lines stand for text Copilot has offered but that has not been
    accepted yet, which is how the suggestion appears in the editor.
    """
    rows = []
    for i, line in enumerate(highlight(code, lang).split("\n")):
        n = start + i
        ghost = ghost_from is not None and n >= ghost_from
        content = line if line.strip() else "&nbsp;"
        style = f"color:{GHOST};font-style:italic" if ghost else ""
        if ghost:
            # Strip the syntax colours so the whole line reads as a suggestion.
            content = re.sub(r'<span style="[^"]*">', "<span>", content)
        rows.append(
            f'<div class="ln"><span class="no">{n}</span>'
            f'<span class="code" style="{style}">{content}</span></div>'
        )
    return "".join(rows)


# ------------------------------------------------------------------- terminal
TERM_RULES = [
    (re.compile(r"^(\$ )(.*)$"),
     lambda m: f'<span style="color:#4ec9b0">{esc(m.group(1))}</span>'
               f'<span style="color:#e8e8e8">{esc(m.group(2))}</span>'),
]

TERM_WORDS = [
    (re.compile(r"\bPASSED\b"), "#4ec9b0"),
    (re.compile(r"\b(FAILED|ERROR|ValueError|JSONDecodeError)\b"), "#f48771"),
    (re.compile(r"\b(\d+ passed)\b"), "#4ec9b0"),
    (re.compile(r"\b(\d+\.\d+x|\d+\.\d+ s|\d+\.\d+s)\b"), "#dcdcaa"),
]


def term_line(line: str) -> str:
    for rule, fn in TERM_RULES:
        m = rule.match(line)
        if m:
            return fn(m)
    out = esc(line)
    for pattern, colour in TERM_WORDS:
        out = pattern.sub(
            lambda m: f'<span style="color:{colour}">{m.group(0)}</span>', out)
    return out


def terminal(title: str, body: str, width: int = 900,
             font_size: float = 13, dots: bool = True) -> str:
    """A terminal window containing body, which is plain text.

    dots draws the three window buttons in the title bar. Turn it off for a
    plainer bar; the title then centres on the whole width instead of being
    offset to balance the buttons.
    """
    lines = "".join(
        f'<div class="tl">{term_line(l) if l.strip() else "&nbsp;"}</div>'
        for l in body.split("\n")
    )
    if dots:
        controls = (
            '<span class="dot" style="background:#ff5f57"></span>'
            '<span class="dot" style="background:#febc2e"></span>'
            '<span class="dot" style="background:#28c840"></span>'
        )
        title_class = "ttitle"
    else:
        controls = ""
        title_class = "ttitle bare"
    return f"""
<div class="win" style="width:{width}px">
  <div class="tbar">
    {controls}
    <span class="{title_class}">{esc(title)}</span>
  </div>
  <div class="tbody" style="font-size:{font_size}px">{lines}</div>
</div>
"""


BASE_CSS = f"""
  *{{box-sizing:border-box}}
  html,body{{margin:0;background:#c9cfdb;font-family:{SANS}}}
  .wrap{{display:inline-block;padding:16px}}
  .win{{border-radius:8px;overflow:hidden;
       box-shadow:0 8px 24px rgba(18,22,32,.30)}}
  .tbar{{display:flex;align-items:center;gap:8px;padding:8px 12px;
        background:#333a45}}
  .dot{{width:11px;height:11px;border-radius:50%;display:inline-block}}
  /* the right margin balances the three buttons on the left, so the title sits
     centred over the body rather than over the whole bar */
  .ttitle{{flex:1;text-align:center;color:#c8cddb;font-size:12px;
          margin-right:44px}}
  .ttitle.bare{{margin-right:0}}
  /* white-space:pre belongs on the lines, not the container, otherwise the
     indentation of the surrounding HTML gets rendered too */
  .tbody{{background:{BG};color:{INK};padding:12px 14px 14px;
         font-family:{MONO};line-height:1.55;white-space:normal}}
  .tl{{min-height:1.55em;white-space:pre}}

  /* editor */
  .ebar{{display:flex;align-items:stretch;background:#252526}}
  .tab{{display:flex;align-items:center;gap:7px;padding:8px 14px;
       background:{BG};color:#e8e8e8;font-size:12px;
       border-top:1px solid #0e70c0}}
  .tab .ic{{color:#4b8bbe;font-size:11px}}
  .tabx{{padding:8px 14px;color:#8a8a8a;font-size:12px}}
  .ebody{{background:{BG};padding:10px 0 14px;font-family:{MONO};
         font-size:13px;line-height:1.55;white-space:normal}}
  .ln{{display:flex}}
  .no{{width:46px;flex:0 0 46px;text-align:right;padding-right:16px;
      color:#6e7681;user-select:none}}
  .code{{flex:1;padding-right:16px;white-space:pre}}
  .sbar{{display:flex;align-items:center;gap:14px;background:#0e70c0;
        color:#fff;font-size:11.5px;padding:4px 14px;font-family:{SANS}}}
  .sbar .r{{margin-left:auto;display:flex;gap:14px}}
  .hint{{display:inline-block;margin-left:46px;margin-top:6px;
        background:#252526;border:1px solid #3c3c3c;border-radius:4px;
        padding:4px 9px;color:#a9a9a9;font-size:11.5px;font-family:{SANS}}}
  .hint b{{color:#e8e8e8;font-weight:600}}
"""


def render(html_body: str, out_path: str, extra_css: str = "",
           scale: int = 2, target: str = ".wrap") -> None:
    """Render html_body and save a screenshot of target."""
    page_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{BASE_CSS}{extra_css}</style></head>
<body><div class="wrap">{html_body}</div></body></html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox",
                                          "--force-color-profile=srgb",
                                          "--font-render-hinting=none"])
        page = browser.new_page(device_scale_factor=scale)
        page.set_content(page_html)
        page.wait_for_timeout(300)
        page.locator(target).screenshot(path=out_path)
        browser.close()
    print("  wrote", os.path.basename(out_path))


class Renderer:
    """Keeps one browser open for a batch of figures."""

    def __init__(self, scale: int = 2) -> None:
        self.scale = scale

    def __enter__(self):
        self._p = sync_playwright().start()
        self._browser = self._p.chromium.launch(
            args=["--no-sandbox", "--force-color-profile=srgb",
                  "--font-render-hinting=none"])
        self._page = self._browser.new_page(device_scale_factor=self.scale)
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._p.stop()

    def shot(self, html_body: str, out_path: str, extra_css: str = "",
             target: str = ".wrap") -> None:
        self._page.set_content(
            f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{BASE_CSS}{extra_css}</style></head>
<body><div class="wrap">{html_body}</div></body></html>"""
        )
        self._page.wait_for_timeout(250)
        self._page.locator(target).screenshot(path=out_path)
        print("  wrote", os.path.basename(out_path))
