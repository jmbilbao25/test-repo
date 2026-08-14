"""Builds the terminal and code figures.

The FastAPI documentation screenshots come from capture_swagger.py. Everything
here is built from the files in results/, which hold the real output of the setup
commands, curl and pytest, and from the source files themselves.

The terminal figures use the Windows Terminal styling in the shared renderer,
since the output was captured from a PowerShell session.

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
    raise SystemExit(f"could not import todo-app/scripts/render.py: {exc}")

# DejaVu Sans Mono advances 0.602 em per character.
CHAR_EM = 0.602
MAX_WIDTH = 1000


def read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def fit(body: str, font_size: float) -> int:
    """Width that holds the longest line without wrapping it."""
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, MAX_WIDTH))


def shell(r: Renderer, title: str, sources: list[str], name: str,
          font_size: float = 12) -> None:
    """A Windows Terminal window holding the given captured output."""
    body = "\n\n".join(read(s) for s in sources)
    r.shot(terminal(title, body, width=fit(body, font_size),
                    font_size=font_size, windows=True),
           out(name))


# name, tab title, source files, font size
SHELL_FIGURES = [
    ("fig-env.png", "Windows PowerShell", ["env.txt"], 12),
    ("fig-dataset.png", "Windows PowerShell", ["dataset.txt"], 12),
    ("fig-devserver.png", "Windows PowerShell - fastapi dev",
     ["devserver.txt"], 12),

    ("fig-curl-health.png", "curl - /health",
     ["curl-health-before.txt", "curl-health-after.txt"], 12),
    ("fig-curl-load.png", "curl - POST /load_data", ["curl-load.txt"], 11.5),
    ("fig-curl-columns.png", "curl - /columns", ["curl-columns.txt"], 11.5),
    ("fig-curl-describe.png", "curl - /describe_data", ["curl-describe.txt"],
     10.5),
    ("fig-curl-filter-text.png", "curl - /filter_data (text)",
     ["curl-filter-text.txt"], 11),
    ("fig-curl-filter-number.png", "curl - /filter_data (numeric)",
     ["curl-filter-number.txt"], 11),
    ("fig-curl-filter-contains.png", "curl - /filter_data (contains)",
     ["curl-filter-contains.txt"], 11),
    ("fig-curl-stats.png", "curl - /stats/petal_length", ["curl-stats.txt"],
     12),
    ("fig-curl-stats-outliers.png", "curl - /stats/sepal_width",
     ["curl-stats-outliers.txt"], 12),
    ("fig-curl-groupby.png", "curl - /group_by",
     ["curl-groupby.txt", "curl-groupby-max.txt"], 11.5),
    ("fig-curl-correlation.png", "curl - /correlation",
     ["curl-correlation.txt"], 12),

    ("fig-curl-errors-1.png", "curl - 409 and 404",
     ["curl-err-notloaded.txt", "curl-err-column.txt"], 11),
    ("fig-curl-errors-2.png", "curl - 400, 404 and 422",
     ["curl-err-value.txt", "curl-err-text-stats.txt",
      "curl-err-operator.txt"], 11),

    ("fig-tests.png", "Windows PowerShell - pytest", ["pytest.txt"], 11),
]


# --------------------------------------------------------------- code figures
def excerpt(path: str, start_marker: str, end_marker: str) -> tuple[str, int]:
    """The lines between two markers, with the real line number of the first."""
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    first = next(i for i, l in enumerate(lines) if start_marker in l)
    last = next(i for i, l in enumerate(lines)
                if i > first and end_marker in l)
    return "\n".join(lines[first:last]).rstrip(), first + 1


def code_figure(r: Renderer, path: str, start: str, end: str, name: str,
                tabs: list[str], width: int = 900) -> None:
    snippet, line_no = excerpt(path, start, end)
    others = "".join(f'<div class="tabx">{t}</div>' for t in tabs)
    body = f"""
<div class="win" style="width:{width}px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>{os.path.basename(path)}</div>
    {others}
  </div>
  <div class="ebody">{numbered(snippet, "python", start=line_no)}</div>
  <div class="sbar">
    <span>{path}</span><span>Python</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
"""
    r.shot(body, out(name))


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    with Renderer() as r:
        # The filter endpoint, which shows the FastAPI parameter declarations.
        code_figure(r, "data_api/main.py",
                    '@app.get("/filter_data"', "# ---", "fig-code-endpoint.png",
                    ["processing.py", "schemas.py"], width=930)

        # The NumPy statistics, which is where the assignment's NumPy work is.
        code_figure(r, "data_api/processing.py",
                    "def numeric_stats", "# ----", "fig-code-numpy.png",
                    ["main.py", "schemas.py"], width=900)

        for name, title, sources, size in SHELL_FIGURES:
            shell(r, title, sources, name, size)
    print("done")


if __name__ == "__main__":
    main()
