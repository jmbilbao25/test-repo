"""Loading and saving the list.

The store keeps the tasks in memory and writes them to a JSON file. The write is
done to a temporary file first and then moved into place, so an interrupted save
cannot leave a half written file behind.
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Dict, Iterator, List, Optional

from .models import Task


class TaskStore:
    def __init__(self, path: str) -> None:
        self.path = path
        # id -> Task. A dict means lookup by id does not scan the whole list.
        self._tasks: Dict[int, Task] = {}
        # Casefolded titles of everything in _tasks, kept up to date as tasks go
        # in and out so the duplicate check is a set lookup rather than a scan.
        self._titles: set = set()
        # Highest id ever handed out, kept so ids are never reused even after a
        # delete.
        self._next_id: int = 1
        self.load()

    # ----------------------------------------------------------- persistence
    def load(self) -> None:
        self._tasks.clear()
        self._titles.clear()
        if not os.path.exists(self.path):
            self._next_id = 1
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (json.JSONDecodeError, OSError):
            # A corrupt or unreadable file should not stop the app from
            # starting; treat it as an empty list.
            self._next_id = 1
            return

        loaded = []
        for item in raw.get("tasks", []):
            try:
                loaded.append(Task.from_dict(item))
            except (KeyError, TypeError, ValueError):
                continue
        # Sorted once here, on load, rather than on every save. New tasks always
        # get a higher id than everything already in the dict, so inserting them
        # keeps the dict in id order from this point on.
        for task in sorted(loaded, key=lambda t: t.id):
            self._tasks[task.id] = task
            self._titles.add(task.title.casefold())

        highest = max(self._tasks, default=0)
        self._next_id = max(int(raw.get("next_id", 0)), highest + 1, 1)

    def save(self) -> None:
        payload = {
            "next_id": self._next_id,
            "tasks": [t.to_dict() for t in self],
        }
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # -------------------------------------------------------------- accessors
    def __iter__(self) -> Iterator[Task]:
        """Tasks in id order, which is the order they were created.

        The dict is built in id order on load and only ever grows at the end, so
        its own ordering is already the right one.
        """
        return iter(self._tasks.values())

    def __len__(self) -> int:
        return len(self._tasks)

    def get(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def has_title(self, title: str) -> bool:
        """Whether this title is already on the list, ignoring case.

        A set lookup, so the cost does not grow with the length of the list.
        """
        return title.casefold() in self._titles

    def take_id(self) -> int:
        task_id = self._next_id
        self._next_id += 1
        return task_id

    def put(self, task: Task) -> None:
        existing = self._tasks.get(task.id)
        if existing is not None:
            self._titles.discard(existing.title.casefold())
        self._tasks[task.id] = task
        self._titles.add(task.title.casefold())

    def remove(self, task_id: int) -> bool:
        task = self._tasks.pop(task_id, None)
        if task is None:
            return False
        self._titles.discard(task.title.casefold())
        return True

    def all(self) -> List[Task]:
        return list(self)
