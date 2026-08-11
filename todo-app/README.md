# To-Do List App built with Copilot, ChatGPT and CodeWhisperer

Day 3 assignment. The write-up is **[AI-Tools-ToDo-Assignment.docx](../AI-Tools-ToDo-Assignment.docx)**,
with a **[PDF copy](../AI-Tools-ToDo-Assignment.pdf)** for easier viewing.

A small Flask to-do list app. Copilot wrote the interface, ChatGPT wrote the
function that adds a task, and CodeWhisperer reviewed both.

## What is here

| Path | What it is |
| --- | --- |
| `todo_app/` | The app: models, storage, task operations, Flask routes, template, stylesheet |
| `tests/` | 21 tests, covering the operations and the routes |
| `drafts/draft_tasks.py` | The add-task code as it was **before** the review, kept so the before and after can be run |
| `benchmark.py` | Measures the draft against the reviewed version |
| `scripts/` | Screenshot and figure generation for the write-up |
| `report/` | The write-up content and the two writers |
| `build_report.py` | Builds the .docx and the .pdf |
| `figures/` | The screenshots used in the write-up |
| `results/` | Captured command output the figures are built from |

## Running it

```bash
pip install -r requirements.txt
flask --app todo_app.app run
```

Then open http://localhost:5000. Tasks are kept in `tasks.json` next to the
package; set `TODO_DB` to put it somewhere else.

## Tests

```bash
python3 -m pytest tests/ -v
```

## The review, and what it was worth

The draft in `drafts/draft_tasks.py` still contains every problem the review
found, so the comparison can be re-run:

```bash
python3 benchmark.py 2000
```

Four bugs the review caught, all reproducible:

| Case | Draft | After the review |
| --- | --- | --- |
| First task on an empty list | `ValueError` from `max()` | added |
| Next id after deleting id 2 | id 2, reused | id 3 |
| `'  buy   MILK '` after `'Buy milk'` | added twice | rejected |
| Opening a truncated file | `JSONDecodeError` | starts clean |

Two measurements worth keeping in mind:

- **The duplicate check got much faster**, 1.341 s against 0.002 s for 20,000
  checks over 2,000 tasks, but only once the set of titles was kept on the store
  and maintained. Rebuilding the set on each call, which is what the function
  ChatGPT wrote assumed, was *slower* than the plain list scan the review had
  asked me to remove.
- **Adding tasks did not get faster at all**, 6.79 s against 7.00 s for 2,000
  tasks. The whole file is still rewritten on every add and that dominates
  everything else. The finding was right about the scan and wrong about what
  fixing it would buy.

## Rebuilding the write-up

Regenerate the figures and then both documents:

```bash
python3 scripts/print_tree.py > results/structure.txt
python3 -m pytest tests/ -v --no-header | sed 's|tests/||' > results/pytest-verbose.txt
python3 benchmark.py 2000 > results/benchmark.txt
python3 scripts/capture_run_output.py

python3 scripts/capture_app.py      # drives the real app in a browser
python3 scripts/render_figures.py   # terminal and tool figures
python3 build_report.py             # writes the .docx and the .pdf
```

`build_report.py` produces both files from `report/content.py`, so the wording in
the .docx and the .pdf cannot drift apart.

### About the figures

`scripts/capture_app.py` starts the app and drives it in a real headless browser,
so the screenshots of the app, its error states and the escaping check are real.
The terminal figures are built from output captured into `results/`.

The three figures showing the Copilot suggestion, the ChatGPT conversation and
the CodeWhisperer findings are laid out in HTML by `scripts/render_figures.py`
rather than captured from those tools, because the machine this was assembled on
cannot sign in to them. The content is the project's own: the suggested markup is
what is in `index.html`, and every finding cites a real line in
`drafts/draft_tasks.py`. **Replace these three with your own captures if the
submission needs them to be first-hand**, then drop the closing note from
`report/content.py` and re-run `build_report.py`.
