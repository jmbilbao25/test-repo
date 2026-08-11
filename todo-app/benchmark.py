"""Compares the draft add_task with the version that came out of the review.

Three separate things get measured, because they do not all point the same way:

  1. Adding n tasks end to end, one save per task.
  2. The duplicate check on its own, with the file work taken out.
  3. What each version does in the cases the review flagged as bugs.

    python3 benchmark.py [count]
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drafts import draft_tasks
from todo_app.storage import TaskStore
from todo_app.tasks import add_task, delete_task

SEED = [{"id": 1, "title": "seed", "done": False, "created_at": "2026-08-11"}]


def _bar(title: str) -> None:
    print(title)
    print("-" * len(title))


# --------------------------------------------------------- 1. end to end add
def end_to_end(count: int) -> tuple[float, float]:
    workdir = tempfile.mkdtemp()
    try:
        draft_path = os.path.join(workdir, "draft.json")
        # The draft cannot add to an empty list at all, so it has to be seeded.
        draft_tasks.save_tasks(draft_path, list(SEED))
        start = time.perf_counter()
        for i in range(count):
            draft_tasks.add_task(draft_path, f"Task number {i}")
        draft = time.perf_counter() - start

        store = TaskStore(os.path.join(workdir, "reviewed.json"))
        add_task(store, "seed")
        start = time.perf_counter()
        for i in range(count):
            add_task(store, f"Task number {i}")
        reviewed = time.perf_counter() - start
        return draft, reviewed
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ------------------------------------------------- 2. duplicate check alone
def duplicate_check(count: int, probes: int = 20000) -> tuple[float, float]:
    """How long it takes to answer 'is this title already on the list?'.

    No file access on either side, so this isolates the linear scan over a list
    of dicts from the set lookup the reviewed version uses.
    """
    rows = [
        {"id": i + 1, "title": f"Task number {i}", "done": False,
         "created_at": "2026-08-11"}
        for i in range(count)
    ]
    workdir = tempfile.mkdtemp()
    try:
        path = os.path.join(workdir, "seeded.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"next_id": count + 1, "tasks": rows}, fh)
        store = TaskStore(path)

        needle = f"Task number {count - 1}"  # worst case: the last one

        start = time.perf_counter()
        for _ in range(probes):
            any(row["title"] == needle for row in rows)
        draft = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(probes):
            store.has_title(needle)
        reviewed = time.perf_counter() - start
        return draft, reviewed
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ------------------------------------------------------- 3. the bug cases
def bug_cases() -> list[tuple[str, str, str]]:
    workdir = tempfile.mkdtemp()
    rows = []
    try:
        # First task on an empty list.
        try:
            draft_tasks.add_task(os.path.join(workdir, "a.json"), "First task")
            draft = "added"
        except Exception as exc:
            draft = f"{type(exc).__name__}"
        store = TaskStore(os.path.join(workdir, "b.json"))
        add_task(store, "First task")
        rows.append(("First task on an empty list", draft, "added"))

        # Id reuse after deleting the newest task.
        dpath = os.path.join(workdir, "c.json")
        draft_tasks.save_tasks(dpath, list(SEED))
        draft_tasks.add_task(dpath, "second")
        rows_now = draft_tasks.load_tasks(dpath)
        draft_tasks.save_tasks(dpath, [r for r in rows_now if r["id"] != 2])
        reused = draft_tasks.add_task(dpath, "third")["id"]

        store = TaskStore(os.path.join(workdir, "d.json"))
        add_task(store, "seed")
        second = add_task(store, "second")
        delete_task(store, second.id)
        fresh = add_task(store, "third").id
        rows.append(("Next id after deleting id 2", f"id {reused} (reused)",
                     f"id {fresh}"))

        # Case and whitespace variant of an existing title.
        epath = os.path.join(workdir, "e.json")
        draft_tasks.save_tasks(epath, list(SEED))
        draft_tasks.add_task(epath, "Buy milk")
        try:
            draft_tasks.add_task(epath, "  buy   MILK ")
            draft = "added twice"
        except ValueError:
            draft = "rejected"
        store = TaskStore(os.path.join(workdir, "f.json"))
        add_task(store, "Buy milk")
        try:
            add_task(store, "  buy   MILK ")
            reviewed = "added twice"
        except Exception:
            reviewed = "rejected"
        rows.append(("'  buy   MILK ' after 'Buy milk'", draft, reviewed))

        # A file that was left half written.
        gpath = os.path.join(workdir, "g.json")
        with open(gpath, "w", encoding="utf-8") as fh:
            fh.write('{"next_id": 3, "tasks": [{"id": 1, "ti')
        try:
            draft_tasks.load_tasks(gpath)
            draft = "loaded"
        except Exception as exc:
            draft = f"{type(exc).__name__}"
        reviewed = f"{len(TaskStore(gpath))} tasks, starts clean"
        rows.append(("Opening a truncated file", draft, reviewed))
        return rows
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 2000

    _bar(f"1. Adding {count} tasks, one save per task")
    draft, reviewed = end_to_end(count)
    print(f"  draft       {draft:7.2f} s")
    print(f"  reviewed    {reviewed:7.2f} s")
    print(f"  ratio       {draft / reviewed:7.2f}x")
    print("  Rewriting the whole file on every add dominates both, so the")
    print("  review did not make this faster.")
    print()

    _bar(f"2. Duplicate check against {count} existing tasks, 20000 probes")
    draft, reviewed = duplicate_check(count)
    print(f"  list scan   {draft:7.3f} s")
    print(f"  set lookup  {reviewed:7.3f} s")
    print(f"  faster by   {draft / reviewed:7.1f}x")
    print()

    _bar("3. The cases the review flagged")
    print(f"  {'case':<34}{'draft':<18}reviewed")
    for case, d, r in bug_cases():
        print(f"  {case:<34}{d:<18}{r}")


if __name__ == "__main__":
    main()
