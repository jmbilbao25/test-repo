"""The add-task code as it stood before the CodeWhisperer review.

Kept in the repository so the before and after in the write-up can actually be
run and measured instead of just described. This module is deliberately not
fixed: every problem listed in the review is still in here.
"""
from __future__ import annotations

import json
import os
from datetime import datetime


def load_tasks(path):
    """Read the whole file and hand back a list of dicts."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as fh:
        return json.load(fh)


def save_tasks(path, tasks):
    """Write the list straight over the top of the existing file."""
    with open(path, "w") as fh:
        json.dump(tasks, fh, indent=2)


def add_task(path, title):
    """Add a task to the list stored at path.

    Problems, all of which the review picked up:

    1. max() over an empty sequence raises ValueError, so the very first task
       cannot be added.
    2. The id comes from the highest id currently present, so deleting the last
       task makes the next task reuse its id.
    3. The whole file is read and written on every single call, which makes
       adding n tasks O(n^2) work.
    4. The duplicate check compares raw strings, so "Buy milk" and "buy milk "
       are treated as different tasks.
    5. json.dump writes directly onto the real file, so an interruption part way
       through leaves a truncated file that can no longer be parsed.
    """
    tasks = load_tasks(path)

    if title == "":
        raise ValueError("Task title cannot be empty.")

    for task in tasks:
        if task["title"] == title:
            raise ValueError("Task already exists.")

    new_id = max(task["id"] for task in tasks) + 1

    tasks.append({
        "id": new_id,
        "title": title,
        "done": False,
        "created_at": datetime.now().isoformat(),
    })
    save_tasks(path, tasks)
    return tasks[-1]
