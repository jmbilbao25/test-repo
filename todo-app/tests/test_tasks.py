"""Tests for the list operations."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from todo_app.storage import TaskStore
from todo_app.tasks import (
    MAX_TITLE_LENGTH,
    TaskError,
    add_task,
    clear_completed,
    counts,
    delete_task,
    toggle_task,
    visible_tasks,
)


@pytest.fixture()
def store(tmp_path):
    return TaskStore(str(tmp_path / "tasks.json"))


def test_add_first_task_to_empty_list(store):
    task = add_task(store, "Buy milk")
    assert task.id == 1
    assert task.title == "Buy milk"
    assert task.done is False
    assert len(store) == 1


def test_title_is_tidied_up(store):
    task = add_task(store, "  water   the  plants  ")
    assert task.title == "water the plants"


def test_empty_title_is_rejected(store):
    for bad in ["", "   ", "\t\n"]:
        with pytest.raises(TaskError):
            add_task(store, bad)
    assert len(store) == 0


def test_duplicate_is_rejected_ignoring_case_and_spaces(store):
    add_task(store, "Buy milk")
    with pytest.raises(TaskError):
        add_task(store, "  buy   MILK ")
    assert len(store) == 1


def test_long_title_is_rejected(store):
    with pytest.raises(TaskError):
        add_task(store, "x" * (MAX_TITLE_LENGTH + 1))


def test_ids_are_not_reused_after_a_delete(store):
    add_task(store, "one")
    second = add_task(store, "two")
    delete_task(store, second.id)
    third = add_task(store, "three")
    assert third.id == 3


def test_toggle_flips_done(store):
    task = add_task(store, "Pay rent")
    assert toggle_task(store, task.id).done is True
    assert toggle_task(store, task.id).done is False


def test_toggle_unknown_id_raises(store):
    with pytest.raises(TaskError):
        toggle_task(store, 99)


def test_delete_removes_the_task(store):
    task = add_task(store, "Call the dentist")
    delete_task(store, task.id)
    assert len(store) == 0
    with pytest.raises(TaskError):
        delete_task(store, task.id)


def test_clear_completed_only_removes_done(store):
    a = add_task(store, "a")
    add_task(store, "b")
    toggle_task(store, a.id)
    assert clear_completed(store) == 1
    assert [t.title for t in store] == ["b"]


def test_views_and_counts(store):
    a = add_task(store, "a")
    add_task(store, "b")
    toggle_task(store, a.id)
    assert [t.title for t in visible_tasks(store, "active")] == ["b"]
    assert [t.title for t in visible_tasks(store, "done")] == ["a"]
    assert len(visible_tasks(store, "all")) == 2
    assert counts(store) == {"total": 2, "done": 1, "active": 1}


def test_tasks_survive_a_reload(tmp_path):
    path = str(tmp_path / "tasks.json")
    first = TaskStore(path)
    add_task(first, "Renew passport")
    add_task(first, "Book flights")

    second = TaskStore(path)
    assert [t.title for t in second] == ["Renew passport", "Book flights"]
    # The id counter has to come back too, or the next id collides.
    assert add_task(second, "Pack").id == 3


def test_corrupt_file_does_not_crash_the_store(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text("{not json at all")
    store = TaskStore(str(path))
    assert len(store) == 0
    assert add_task(store, "Start over").id == 1
