"""Builds the terminal and code figures.

The Swagger screenshots come from capture_swagger.py and the client screenshots
from capture_webapp.py. Everything here is built from the files in results/,
which hold the real output of the setup commands, curl, newman and pytest, and
from the source files themselves.

The terminal figures use the Windows Terminal styling in the shared renderer,
since the output was captured from a PowerShell session.

    python3 scripts/make_figures.py
"""
from __future__ import annotations

import json
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

CHAR_EM = 0.602
MAX_WIDTH = 1010


def read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def fit(body: str, font_size: float) -> int:
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, MAX_WIDTH))


def shell(r: Renderer, title: str, sources: list[str], name: str,
          font_size: float = 12) -> None:
    body = "\n\n".join(read(s) for s in sources)
    r.shot(terminal(title, body, width=fit(body, font_size),
                    font_size=font_size, windows=True),
           out(name))


SHELL_FIGURES = [
    ("fig-env.png", "Windows PowerShell", ["env.txt"], 12),
    ("fig-devserver.png", "Windows PowerShell - fastapi dev",
     ["devserver.txt"], 12),
    ("fig-hashing.png", "Windows PowerShell - password storage",
     ["hashing.txt"], 12),
    ("fig-token-anatomy.png", "Windows PowerShell - inside a JWT",
     ["token-anatomy.txt"], 11.5),

    ("fig-curl-health.png", "curl - open endpoint", ["curl-health.txt"], 12),
    ("fig-curl-token.png", "curl - POST /auth/token", ["curl-token.txt"], 11.5),
    ("fig-curl-me.png", "curl - GET /auth/me", ["curl-me.txt"], 11.5),
    ("fig-curl-reports.png", "curl - GET /reports", ["curl-reports.txt"], 11),
    ("fig-curl-summary.png", "curl - GET /reports/summary",
     ["curl-summary.txt"], 11),
    ("fig-curl-create.png", "curl - POST /reports", ["curl-create.txt"], 11.5),
    ("fig-curl-narrow-scope.png", "curl - asking for fewer scopes",
     ["curl-narrow-scope.txt"], 11.5),
    ("fig-curl-delete.png", "curl - DELETE as admin", ["curl-delete.txt"], 11.5),

    ("fig-curl-no-token.png", "curl - 401, no token", ["curl-no-token.txt"], 12),
    ("fig-curl-tampered.png", "curl - 401, edited signature",
     ["curl-tampered.txt"], 11),
    ("fig-curl-expired.png", "curl - 401, expired token",
     ["curl-expired.txt"], 11),
    ("fig-curl-refresh-misuse.png", "curl - 401, refresh token used for access",
     ["curl-refresh-misuse.txt"], 11),
    ("fig-curl-forbidden.png", "curl - 403, scope missing",
     ["curl-forbidden.txt"], 11),
    ("fig-curl-forbidden-delete.png", "curl - 403, write is not delete",
     ["curl-forbidden-delete.txt"], 11),
    ("fig-curl-bad-password.png", "curl - 401, wrong password",
     ["curl-bad-password.txt"], 11.5),
    ("fig-curl-bad-scope.png", "curl - 400, scope refused",
     ["curl-bad-scope.txt"], 11.5),
    ("fig-curl-rate-limit.png", "curl - 429, too many attempts",
     ["curl-rate-limit.txt"], 11.5),

    # The full run is 120 lines, so it is shown in two pieces.
    ("fig-newman-head.png", "Windows PowerShell - newman run",
     ["newman-head.txt"], 11),
    ("fig-newman-summary.png", "Windows PowerShell - newman totals",
     ["newman-summary.txt"], 11),
    ("fig-tests.png", "Windows PowerShell - pytest", ["pytest.txt"], 11),
]


# --------------------------------------------------------------- code figures
def excerpt(path: str, start_marker: str,
            end_marker: str | None = None) -> tuple[str, int]:
    """Lines between two markers, with the real line number of the first.

    end_marker may be None, or simply not present, for a function that runs to
    the end of the file.
    """
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    first = next(i for i, l in enumerate(lines) if start_marker in l)
    last = len(lines)
    if end_marker:
        last = next((i for i, l in enumerate(lines)
                     if i > first and end_marker in l), len(lines))
    return "\n".join(lines[first:last]).rstrip(), first + 1


def code_figure(r: Renderer, path: str, start: str, end: str | None, name: str,
                tabs: list[str], width: int = 930,
                language: str = "python") -> None:
    snippet, line_no = excerpt(path, start, end)
    others = "".join(f'<div class="tabx">{t}</div>' for t in tabs)
    body = f"""
<div class="win" style="width:{width}px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>{os.path.basename(path)}</div>
    {others}
  </div>
  <div class="ebody">{numbered(snippet, language, start=line_no)}</div>
  <div class="sbar">
    <span>{path}</span><span>{language.title()}</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
"""
    r.shot(body, out(name))


def postman_figure(r: Renderer) -> None:
    """The saved-token script from the collection, as it is in the file."""
    with open(os.path.join(ROOT, "postman",
                           "secure-api.postman_collection.json"),
              encoding="utf-8") as fh:
        collection = json.load(fh)

    sign_in = next(item for item in collection["item"]
                   if item["name"] == "Auth")["item"]
    sign_in = next(item for item in sign_in if item["name"] == "Sign in")
    script = "\n".join(sign_in["event"][0]["script"]["exec"])

    body = f"""
<div class="win" style="width:920px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>Sign in &mdash; Tests</div>
    <div class="tabx">Pre-request</div>
    <div class="tabx">Body</div>
  </div>
  <div class="ebody">{numbered(script, "javascript", start=1)}</div>
  <div class="sbar">
    <span>postman/secure-api.postman_collection.json</span>
    <span>JavaScript</span>
    <span class="r"><span>Postman test script</span></span>
  </div>
</div>
"""
    r.shot(body, out("fig-postman-script.png"))


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    with Renderer() as r:
        # Making a token.
        code_figure(r, "secure_api/security.py",
                    "def _encode", "def create_refresh_token",
                    "fig-code-jwt.png", ["dependencies.py", "limits.py"])
        # Checking one. This runs to the end of the file.
        code_figure(r, "secure_api/security.py",
                    "def decode_token", None, "fig-code-decode.png",
                    ["dependencies.py", "limits.py"])
        # Scope enforcement, also the last function in its file.
        code_figure(r, "secure_api/dependencies.py",
                    "def require_scopes", None, "fig-code-scopes.png",
                    ["security.py", "main.py"])
        # Rate limiting.
        code_figure(r, "secure_api/limits.py",
                    "def client_key", "limiter = Limiter",
                    "fig-code-limits.png", ["main.py", "security.py"])
        # A protected endpoint, showing how the scope is declared.
        code_figure(r, "secure_api/main.py",
                    '@app.post("/reports"', "@app.delete",
                    "fig-code-endpoint.png", ["dependencies.py", "limits.py"])

        postman_figure(r)

        for name, title, sources, size in SHELL_FIGURES:
            shell(r, title, sources, name, size)
    print("done")


if __name__ == "__main__":
    main()
