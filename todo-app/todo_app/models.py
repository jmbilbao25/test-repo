"""The Task record."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Task:
    """One item on the list."""

    id: int
    title: str
    done: bool = False
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "Task":
        return cls(
            id=int(raw["id"]),
            title=str(raw["title"]),
            done=bool(raw.get("done", False)),
            created_at=str(raw.get("created_at", _now())),
        )
