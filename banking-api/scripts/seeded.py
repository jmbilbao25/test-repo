"""The submitted app, with its in-memory table pre-loaded to a chosen size.

app.py is the artifact under study and is left byte-for-byte as submitted, so
the seeding happens here instead. uvicorn is pointed at scripts.seeded:app and
reads the row count from SEED_ROWS.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db_transactions  # noqa: E402  the submitted application

CATEGORIES = ["groceries", "dining", "electronics", "transport", "travel"]


def seed(rows: int, accounts: int = 3) -> None:
    rng = random.Random(20260818)
    for i in range(rows):
        db_transactions.append({
            "transaction_id": f"seed_{i}",
            "account_id": f"acc_{i % accounts + 1}",
            "amount": round(rng.lognormvariate(4.0, 1.0), 2),
            "category": rng.choice(CATEGORIES),
            "timestamp": "2026-08-18T00:00:00Z",
        })


seed(int(os.environ.get("SEED_ROWS", "0")))

__all__ = ["app"]
