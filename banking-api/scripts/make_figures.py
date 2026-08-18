"""Builds the terminal and code figures.

Every terminal figure is rendered from a file in results/, which holds real
captured output. Every code figure is sliced out of app.py, which is the
submitted application byte-for-byte. The Swagger figures come from
capture_swagger.py and the submitted screenshots are used as they are.

Terminal figures use the Windows Terminal styling in the shared renderer, since
the app was run from PowerShell.

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

CHAR_EM = 0.602

# Screenshots taken on the submitting machine, used exactly as supplied.
SUBMITTED = {
    "user-powershell-session.png": "fig-user-powershell.png",
    "user-pycharm-uvicorn-error.png": "fig-user-pycharm.png",
    "user-pgadmin-accounts.png": "fig-user-pgadmin.png",
}


def read(name: str, folder: str = RESULTS) -> str:
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def fit(body: str, font_size: float, cap: int = 1010) -> int:
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, cap))


def upto(text: str, marker: str) -> str:
    return text[:text.index(marker)].rstrip()


def frm(text: str, marker: str) -> str:
    return text[text.index(marker):].rstrip()


def excerpt(first: str, last: str, filename: str = "app.py") -> tuple[str, int]:
    """Lines of a source file between two markers, with the real start line."""
    lines = read(filename, ROOT).split("\n")
    a = next(i for i, l in enumerate(lines) if first in l)
    b = next(i for i, l in enumerate(lines) if last in l and i >= a)
    return "\n".join(lines[a:b + 1]), a + 1


def code_figure(r: Renderer, name: str, first: str, last: str,
                width: int = 980) -> None:
    code, start = excerpt(first, last)
    r.shot(f"""
<div class="win" style="width:{width}px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>app.py</div>
  </div>
  <div class="ebody">{numbered(code, "python", start=start)}</div>
  <div class="sbar">
    <span>app.py</span><span>Python</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
""", out(name))


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    session = read("session.txt")
    # The transcript's third call is the account summary; split the transcript
    # there so it becomes two figures that each fit a page.
    third = session.index("/v1/accounts/acc_1/summary")
    boundary = session.rindex("PS C:", 0, third)

    shells = [
        ("fig-uvicorn-error-fix.png",
         "Windows PowerShell - starting the server",
         read("uvicorn_error_and_fix.txt"), 11.5, 1010),
        ("fig-uvicorn-start.png",
         "Windows PowerShell - uvicorn running",
         read("uvicorn_start.txt"), 12.5, 1010),
        ("fig-uvicorn-access.png",
         "Windows PowerShell - server log during the session",
         read("uvicorn_access.txt"), 12, 1010),

        ("fig-session-transactions.png",
         "Windows PowerShell - POST /v1/transactions",
         session[:boundary].rstrip(), 11, 1010),
        ("fig-session-analytics.png",
         "Windows PowerShell - the two analytics endpoints",
         session[boundary:].rstrip(), 11, 1010),

        ("fig-measure-gather.png",
         "Windows PowerShell - concurrent vs sequential I/O",
         read("measure_gather.txt"), 12, 1010),
        ("fig-measure-blocking.png",
         "Windows PowerShell - 20 requests at once",
         read("measure_blocking.txt"), 12, 1010),
        ("fig-measure-scaling.png",
         "Windows PowerShell - latency against rows held in memory",
         read("measure_scaling.txt"), 12, 1010),
        ("fig-pytest.png", "Windows PowerShell - pytest",
         read("pytest.txt"), 11, 1010),
    ]

    codes = [
        ("fig-code-schema.png", "class Transaction(BaseModel)", "    )"),
        ("fig-code-async.png", "async def simulate_mainframe_check",
         'print(f"\u26a0\ufe0f [ALERT]'),
        ("fig-code-numpy.png", "def run_numpy_fraud_detection",
         '"std_dev": round(std, 2)'),
        ("fig-code-pandas.png", "def run_pandas_account_analytics",
         '"spend_by_category": category_breakdown'),
        ("fig-code-endpoint.png", '@app.post("/v1/transactions"',
         '"fraud_assessment": fraud_eval'),
        ("fig-code-gather.png", '@app.get("/v1/analytics/batch-risk-matrix"',
         'df[df["amount"] >= p95_threshold]'),
    ]

    with Renderer(scale=2) as r:
        for name, title, body, size, cap in shells:
            r.shot(terminal(title, body, width=fit(body, size, cap),
                            font_size=size, windows=True),
                   out(name))
        for name, first, last in codes:
            code_figure(r, name, first, last)

    # The submitted screenshots are used unmodified. They are copied into
    # figures/ only so the build has a single input directory; screenshots/
    # stays the untouched original set.
    copied = 0
    for src, dest in SUBMITTED.items():
        with open(os.path.join(ROOT, "screenshots", src), "rb") as fh:
            data = fh.read()
        with open(out(dest), "wb") as fh:
            fh.write(data)
        print("  copied", dest)
        copied += 1

    print(f"\n{len(shells) + len(codes)} rendered + {copied} submitted "
          f"= {len(shells) + len(codes) + copied} figures in {FIG}")


if __name__ == "__main__":
    main()
