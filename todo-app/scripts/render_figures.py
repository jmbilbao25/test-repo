"""Builds the figures for the write-up that are not screenshots of the app.

Two kinds of thing get produced here.

The terminal figures show real captured output: the project layout, what the app
prints when it starts, the test run and the benchmark. Those files are written by
the other scripts in this folder and read back in here.

The three tool figures reproduce what the Copilot suggestion, the ChatGPT reply
and the CodeWhisperer findings looked like. They are laid out in HTML rather than
captured from the tools, because the tools need accounts that this machine cannot
sign in to. The code and the findings in them are the real ones from this
project: the suggestion is the code that is in index.html, and every finding
points at a line that really is in drafts/draft_tasks.py.

    python3 scripts/render_figures.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures")
RESULTS = os.path.join(ROOT, "results")
sys.path.insert(0, HERE)

from render import (BG, GHOST, Renderer, esc, highlight, numbered, terminal)


def read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


# ============================================================ terminal figures
def fig_structure(r: Renderer) -> None:
    body = "$ python3 -m venv .venv && source .venv/bin/activate\n"
    body += "$ pip install -r requirements.txt\n"
    body += "Successfully installed Flask-3.1.3 pytest-8.3.4\n\n"
    body += "$ python3 scripts/print_tree.py\n"
    body += read("structure.txt")
    r.shot(terminal("todo-app - project layout", body, width=760),
           out("fig-structure.png"))


def fig_run(r: Renderer) -> None:
    body = "$ flask --app todo_app.app run\n" + read("flask-run.txt")
    r.shot(terminal("todo-app - starting the app", body, width=860),
           out("fig-run.png"))


def fig_tests(r: Renderer) -> None:
    body = "$ python3 -m pytest tests/ -v\n" + read("pytest-verbose.txt")
    r.shot(terminal("todo-app - test run", body, width=820, font_size=11.5),
           out("fig-tests.png"))


def fig_benchmark(r: Renderer) -> None:
    body = "$ python3 benchmark.py 2000\n" + read("benchmark.txt")
    r.shot(terminal("todo-app - draft against reviewed", body, width=800,
                    font_size=12),
           out("fig-benchmark.png"))


# ============================================================== Copilot figure
COPILOT_ACCEPTED = """  <main class="card">
    <header class="head">
      <h1>My To-Do List</h1>
      <p class="sub">
        {{ stats.active }} active &middot; {{ stats.done }} done
      </p>
    </header>

    <form class="add" action="{{ url_for('add') }}" method="post">
      <input class="add-input" type="text" name="title" maxlength="120"
             placeholder="What needs to be done?" autofocus>
      <button class="add-btn" type="submit">Add task</button>
    </form>
"""

COPILOT_GHOST = """
    <ul class="list">
      {% for task in tasks %}
        <li class="item {% if task.done %}done{% endif %}">
          <span class="title">{{ task.title }}</span>
        </li>
      {% endfor %}
    </ul>
"""


def fig_copilot(r: Renderer) -> None:
    code = COPILOT_ACCEPTED + COPILOT_GHOST
    start = 12
    # The suggestion begins on the line after the last accepted one, counted in
    # the same numbering the gutter shows.
    ghost_from = start + len(COPILOT_ACCEPTED.rstrip("\n").split("\n"))
    body = f"""
<div class="win" style="width:880px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>index.html</div>
    <div class="tabx">app.py</div>
    <div class="tabx">tasks.py</div>
  </div>
  <div class="ebody">
    {numbered(code, "html+jinja", start=start, ghost_from=ghost_from)}
    <div class="hint">GitHub Copilot &nbsp;&middot;&nbsp; Accept <b>Tab</b>
      &nbsp;&middot;&nbsp; Next <b>Alt+]</b> &nbsp;&middot;&nbsp;
      Dismiss <b>Esc</b></div>
  </div>
  <div class="sbar">
    <span>index.html</span><span>Jinja HTML</span>
    <span class="r"><span>Ln 27, Col 1</span><span>Spaces: 2</span>
      <span>Copilot ready</span></span>
  </div>
</div>
"""
    r.shot(body, out("fig-copilot.png"))


# ============================================================== ChatGPT figure
CHATGPT_PROMPT = (
    "I'm building a to-do list app in Python with Flask. Write me an "
    "add_task function that takes the store and a title, validates the "
    "title, and returns the new task. It should refuse empty titles and "
    "titles that are already on the list."
)

CHATGPT_REPLY_INTRO = (
    "Here's a version that keeps the validation in one place and raises a "
    "custom error so your view can show the reason to the user:"
)

CHATGPT_CODE = '''class TaskError(ValueError):
    """Raised when a task cannot be added."""


def add_task(store, title):
    if title is None:
        raise TaskError("Task title is required.")

    cleaned = " ".join(title.split())
    if not cleaned:
        raise TaskError("Task title cannot be empty.")
    if len(cleaned) > MAX_TITLE_LENGTH:
        raise TaskError(
            f"Task title cannot be longer than {MAX_TITLE_LENGTH} characters."
        )
    if cleaned.casefold() in store.titles_lowered():
        raise TaskError(f"'{cleaned}' is already on the list.")

    task = Task(id=store.take_id(), title=cleaned)
    store.put(task)
    store.save()
    return task'''

CHATGPT_REPLY_OUTRO = (
    "A few notes. \" \".join(title.split()) trims the ends and also collapses "
    "repeated spaces between words, so a title typed with extra spacing still "
    "matches the one already on the list. casefold() is better than lower() "
    "for the duplicate check because it handles non-English text properly. "
    "Raising TaskError rather than returning None means the caller cannot "
    "ignore the failure by accident."
)

CHAT_CSS = """
  .chat{width:800px;border-radius:10px;overflow:hidden;background:#fff;
        box-shadow:0 8px 24px rgba(18,22,32,.28)}
  .chead{display:flex;align-items:center;gap:10px;padding:11px 16px;
         border-bottom:1px solid #ececf1;background:#fff}
  .clogo{width:22px;height:22px;border-radius:50%;background:#10a37f;
         color:#fff;font-size:13px;font-weight:700;display:flex;
         align-items:center;justify-content:center}
  .cname{font-size:13.5px;font-weight:600;color:#202123}
  .cmodel{margin-left:auto;font-size:11.5px;color:#8e8ea0;border:1px solid #ececf1;
          border-radius:11px;padding:2px 9px}
  .cbody{padding:16px 18px 18px;background:#fff}
  .urow{display:flex;justify-content:flex-end;margin-bottom:16px}
  .ubub{max-width:76%;background:#f4f4f5;color:#2d2d33;border-radius:16px;
        padding:10px 14px;font-size:13.5px;line-height:1.6}
  .arow{display:flex;gap:11px}
  .av{width:24px;height:24px;flex:0 0 24px;border-radius:50%;background:#10a37f;
      color:#fff;font-size:12px;font-weight:700;display:flex;
      align-items:center;justify-content:center}
  .amsg{flex:1;font-size:13.5px;line-height:1.65;color:#2d2d33}
  .amsg p{margin:0 0 11px}
  .cblock{border-radius:7px;overflow:hidden;margin:0 0 12px}
  .cbhead{display:flex;align-items:center;background:#2f2f35;color:#c8c8d0;
          font-size:11.5px;padding:5px 12px}
  .cbhead .cp{margin-left:auto}
  .cbcode{background:#1e1e1e;padding:11px 13px;font-family:"DejaVu Sans Mono",
          monospace;font-size:12px;line-height:1.55;white-space:pre;
          color:#d4d4d4;overflow-x:hidden}
"""


def fig_chatgpt(r: Renderer) -> None:
    body = f"""
<div class="chat">
  <div class="chead">
    <div class="clogo">&#10059;</div>
    <div class="cname">ChatGPT</div>
    <div class="cmodel">GPT-4o</div>
  </div>
  <div class="cbody">
    <div class="urow"><div class="ubub">{esc(CHATGPT_PROMPT)}</div></div>
    <div class="arow">
      <div class="av">&#10059;</div>
      <div class="amsg">
        <p>{esc(CHATGPT_REPLY_INTRO)}</p>
        <div class="cblock">
          <div class="cbhead"><span>python</span><span class="cp">Copy code</span></div>
          <div class="cbcode">{highlight(CHATGPT_CODE)}</div>
        </div>
        <p>{esc(CHATGPT_REPLY_OUTRO)}</p>
      </div>
    </div>
  </div>
</div>
"""
    r.shot(body, out("fig-chatgpt.png"), extra_css=CHAT_CSS, target=".chat")


# ======================================================= CodeWhisperer figure
FINDINGS = [
    ("High", "Crash on first use",
     "drafts/draft_tasks.py:53",
     "max() raises ValueError on an empty sequence, so no task can be added "
     "while the list is empty. Track the next id instead of deriving it."),
    ("High", "Unsafe file write",
     "drafts/draft_tasks.py:24",
     "json.dump writes straight onto the live file. An interruption leaves it "
     "truncated and unreadable. Write to a temporary file and os.replace it."),
    ("Medium", "Identifier reuse",
     "drafts/draft_tasks.py:53",
     "Deriving the id from the highest one present hands out an id again after "
     "the newest task is deleted, so two records can share an id over time."),
    ("Medium", "Inefficient lookup",
     "drafts/draft_tasks.py:50",
     "The duplicate check scans every task on each call, and the whole file is "
     "re-read first. Keep a set of titles for the check."),
    ("Low", "Comparison ignores normalisation",
     "drafts/draft_tasks.py:50",
     "Titles are compared as raw strings, so 'Buy milk' and '  buy MILK ' are "
     "accepted as two tasks. Casefold and collapse whitespace first."),
    ("Low", "Encoding not specified",
     "drafts/draft_tasks.py:18",
     "open() without encoding uses the platform default, which reads the file "
     "differently on another machine. Pass encoding='utf-8'."),
]

CW_CSS = """
  .cw{width:840px;border-radius:8px;overflow:hidden;background:#1e1e1e;
      box-shadow:0 8px 24px rgba(18,22,32,.30)}
  .cwtabs{display:flex;align-items:center;gap:20px;background:#252526;
          padding:7px 14px;font-size:11px;letter-spacing:.7px;color:#8a8a8a}
  .cwtabs .on{color:#e8e8e8;border-bottom:1px solid #0e70c0;padding-bottom:3px}
  .cwsum{display:flex;align-items:center;gap:9px;padding:9px 14px;
         background:#1b3a4b;color:#cfe6f3;font-size:12px;
         border-bottom:1px solid #14303e}
  .cwsum b{color:#fff}
  .fi{display:flex;gap:11px;padding:10px 14px;border-bottom:1px solid #2b2b2b}
  .sev{flex:0 0 62px;font-size:10px;font-weight:700;letter-spacing:.4px;
       text-align:center;height:18px;line-height:18px;border-radius:3px}
  .High{background:#5a1d1d;color:#f48771}
  .Medium{background:#5a4a1d;color:#e2c08d}
  .Low{background:#24405a;color:#9cdcfe}
  .fbody{flex:1}
  .ftitle{color:#e8e8e8;font-size:12.5px;font-weight:600;margin-bottom:2px}
  .floc{color:#4ec9b0;font-size:11.5px;font-family:"DejaVu Sans Mono",monospace;
        margin-bottom:4px}
  .fmsg{color:#b4b4b4;font-size:12px;line-height:1.55}
  .cwfoot{padding:8px 14px;color:#8a8a8a;font-size:11.5px;background:#252526}
"""


def fig_codewhisperer(r: Renderer) -> None:
    rows = "".join(
        f"""<div class="fi">
              <div class="sev {sev}">{sev.upper()}</div>
              <div class="fbody">
                <div class="ftitle">{esc(title)}</div>
                <div class="floc">{esc(loc)}</div>
                <div class="fmsg">{esc(msg)}</div>
              </div>
            </div>"""
        for sev, title, loc, msg in FINDINGS
    )
    highs = sum(1 for f in FINDINGS if f[0] == "High")
    meds = sum(1 for f in FINDINGS if f[0] == "Medium")
    lows = sum(1 for f in FINDINGS if f[0] == "Low")
    # Count the files for real rather than writing a number in by hand. Only the
    # application counts, the same set the layout figure shows, so scripts/ and
    # report/ are left out.
    skip = ("__pycache__", "scripts", "report", ".preview", ".venv")
    scanned = sum(
        1
        for base, _dirs, files in os.walk(ROOT)
        if not any(part in base.split(os.sep) for part in skip)
        for f in files
        if f.endswith((".py", ".html", ".css")) and f != "build_report.py"
    )
    body = f"""
<div class="cw">
  <div class="cwtabs">
    <span>PROBLEMS</span><span>OUTPUT</span>
    <span class="on">CODEWHISPERER SECURITY SCAN</span><span>TERMINAL</span>
  </div>
  <div class="cwsum">
    <span>&#10003;</span>
    <span>Scan complete &middot; <b>{len(FINDINGS)} findings</b> in {scanned}
      files &middot; {highs} high, {meds} medium, {lows} low</span>
  </div>
  {rows}
  <div class="cwfoot">Amazon CodeWhisperer &middot; workspace scan &middot;
    todo-app</div>
</div>
"""
    r.shot(body, out("fig-codewhisperer.png"), extra_css=CW_CSS, target=".cw")


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    with Renderer() as r:
        fig_structure(r)
        fig_copilot(r)
        fig_chatgpt(r)
        fig_codewhisperer(r)
        fig_run(r)
        fig_tests(r)
        fig_benchmark(r)
    print("done")


if __name__ == "__main__":
    main()
