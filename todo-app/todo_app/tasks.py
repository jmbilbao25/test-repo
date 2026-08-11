"""The operations the app performs on the list.

add_task started as the function ChatGPT wrote. The validation rules and the
error type are still its idea; the parts that changed after the CodeWhisperer
review are noted in the write-up.
"""
from __future__ import annotations

from typing import List

from .models import Task
from .storage import TaskStore

MAX_TITLE_LENGTH = 120


class TaskError(ValueError):
    """Raised when a task cannot be added, so the view can show the reason."""


def add_task(store: TaskStore, title: str) -> Task:
    """Add a task to the list and return it.

    The title has to be non-empty, no longer than MAX_TITLE_LENGTH, and not
    already on the list. Comparison ignores case and surrounding spaces, so
    "Buy milk" and "  buy milk " count as the same task.
    """
    if title is None:
        raise TaskError("Task title is required.")

    cleaned = " ".join(title.split())
    if not cleaned:
        raise TaskError("Task title cannot be empty.")
    if len(cleaned) > MAX_TITLE_LENGTH:
        raise TaskError(
            f"Task title cannot be longer than {MAX_TITLE_LENGTH} characters."
        )
    if store.has_title(cleaned):
        raise TaskError(f"'{cleaned}' is already on the list.")

    task = Task(id=store.take_id(), title=cleaned)
    store.put(task)
    store.save()
    return task


def toggle_task(store: TaskStore, task_id: int) -> Task:
    task = store.get(task_id)
    if task is None:
        raise TaskError(f"No task with id {task_id}.")
    task.done = not task.done
    store.save()
    return task


def delete_task(store: TaskStore, task_id: int) -> None:
    if not store.remove(task_id):
        raise TaskError(f"No task with id {task_id}.")
    store.save()


def clear_completed(store: TaskStore) -> int:
    done_ids = [t.id for t in store if t.done]
    for task_id in done_ids:
        store.remove(task_id)
    if done_ids:
        store.save()
    return len(done_ids)


def visible_tasks(store: TaskStore, view: str = "all") -> List[Task]:
    """The tasks the chosen tab should show."""
    if view == "active":
        return [t for t in store if not t.done]
    if view == "done":
        return [t for t in store if t.done]
    return store.all()


def counts(store: TaskStore) -> dict:
    total = len(store)
    done = sum(1 for t in store if t.done)
    return {"total": total, "done": done, "active": total - done}
