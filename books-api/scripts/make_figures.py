"""Builds the terminal and code figures.

The Swagger UI screenshots come from capture_swagger.py. Everything here is built
from the files in results/, which hold the real output of curl and pytest, and
from openapi.yaml itself.

The rendering helpers are the ones written for the Day 3 assignment.

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
        f"could not import todo-app/scripts/render.py: {exc}")


def read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


# The five endpoints, one figure each, plus the query filter.
CURL_FIGURES = [
    ("fig-curl-post.png", "POST /books", ["curl-post.txt"], 12),
    ("fig-curl-get-all.png", "GET /books", ["curl-get-all.txt"], 11.5),
    ("fig-curl-get-filtered.png", "GET /books?author=orwell",
     ["curl-get-filtered.txt"], 12),
    ("fig-curl-get-one.png", "GET /books/{id}", ["curl-get-one.txt"], 12),
    ("fig-curl-put.png", "PUT /books/{id}", ["curl-put.txt"], 12),
    # Delete and the follow-up read belong together: the 204 only means
    # something next to the 404 that follows it.
    ("fig-curl-delete.png", "DELETE /books/{id}",
     ["curl-delete.txt", "curl-get-deleted.txt"], 12),
    ("fig-curl-errors.png", "The three error responses",
     ["curl-err-validation.txt", "curl-err-conflict.txt",
      "curl-err-notfound.txt"], 11.5),
]


def spec_figure(r: Renderer) -> None:
    """The POST /books operation, read out of openapi.yaml."""
    with open(os.path.join(ROOT, "openapi.yaml"), encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    first = next(i for i, l in enumerate(lines) if l.strip() == "post:")
    last = next(i for i, l in enumerate(lines)
                if i > first and l.startswith("  /books/{id}:"))
    snippet = "\n".join(lines[first:last]).rstrip()

    body = f"""
<div class="win" style="width:820px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>openapi.yaml</div>
    <div class="tabx">app.py</div>
    <div class="tabx">validation.py</div>
  </div>
  <div class="ebody">{numbered(snippet, "yaml", start=first + 1)}</div>
  <div class="sbar">
    <span>openapi.yaml</span><span>YAML</span>
    <span class="r"><span>OpenAPI 3.0.3</span><span>Spaces: 2</span></span>
  </div>
</div>
"""
    r.shot(body, out("fig-spec.png"))


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    with Renderer() as r:
        spec_figure(r)

        for name, title, sources, size in CURL_FIGURES:
            body = "\n\n".join(read(s) for s in sources)
            r.shot(terminal(f"books-api - {title}", body, width=820,
                            font_size=size, dots=False),
                   out(name))

        r.shot(terminal("books-api - test run", read("pytest.txt"),
                        width=860, font_size=11.5, dots=False),
               out("fig-tests.png"))
    print("done")


if __name__ == "__main__":
    main()
