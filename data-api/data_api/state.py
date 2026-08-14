"""Holds the DataFrame between requests.

The dataset is loaded by POST /load_data and kept in memory, so every other
endpoint needs it to have been called first. Anything that reads the data raises
DataNotLoaded if it has not been, which the app turns into a 409.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd


class DataNotLoaded(RuntimeError):
    """The dataset has not been loaded yet."""


@dataclass
class Dataset:
    frame: pd.DataFrame
    source: str
    loaded_at: str


_dataset: Optional[Dataset] = None


def store(frame: pd.DataFrame, source: str) -> Dataset:
    global _dataset
    _dataset = Dataset(
        frame=frame,
        source=source,
        loaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return _dataset


def current() -> Dataset:
    if _dataset is None:
        raise DataNotLoaded(
            "No dataset is loaded. Call POST /load_data first.")
    return _dataset


def frame() -> pd.DataFrame:
    return current().frame


def is_loaded() -> bool:
    return _dataset is not None


def clear() -> None:
    """Used by the tests to get back to a clean state."""
    global _dataset
    _dataset = None
