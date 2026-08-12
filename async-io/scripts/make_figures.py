"""Builds the figures for the write-up.

The terminal figures are the real output of the three scripts, captured into
results/. The code figure is read straight out of async_fetch.py, so it cannot
show code that is not in the file.

The rendering helpers are the ones written for the Day 3 assignment and are
imported from there rather than copied.

    python3 scripts/make_figures.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
FIG = os.path.join(ROOT, "figures")
RESULTS = os.path.join(ROOT, "results")

sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
try:
    from render import Renderer, numbered, terminal
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "could not import the renderer from todo-app/scripts/render.py: "
        f"{exc}")


def read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def code_figure(r: Renderer) -> None:
    """async_fetch.py from fetch_data to the end, as it is on disk."""
    with open(os.path.join(ROOT, "async_fetch.py"), encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    first = next(i for i, l in enumerate(lines)
                 if l.startswith("async def fetch_data"))
    # Stop before the __main__ guard, which is not interesting here.
    last = next(i for i, l in enumerate(lines) if l.startswith('if __name__'))
    snippet = "\n".join(lines[first:last]).rstrip("\n")

    body = f"""
<div class="win" style="width:880px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>async_fetch.py</div>
    <div class="tabx">compare.py</div>
    <div class="tabx">errors.py</div>
  </div>
  <div class="ebody">{numbered(snippet, "python", start=first + 1)}</div>
  <div class="sbar">
    <span>async_fetch.py</span><span>Python</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
"""
    r.shot(body, out("fig-code.png"))


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    with Renderer() as r:
        code_figure(r)
        r.shot(terminal("async-io - python3 async_fetch.py",
                        "$ python3 async_fetch.py\n" + read("async_fetch.txt"),
                        width=820, font_size=12.5),
               out("fig-run.png"))
        r.shot(terminal("async-io - python3 compare.py",
                        "$ python3 compare.py\n" + read("compare.txt"),
                        width=780, font_size=12.5),
               out("fig-compare.png"))
        r.shot(terminal("async-io - python3 errors.py",
                        "$ python3 errors.py\n" + read("errors.txt"),
                        width=820, font_size=12),
               out("fig-errors.png"))
    print("done")


if __name__ == "__main__":
    main()
