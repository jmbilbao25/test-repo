"""The data the API protects: a small set of expense reports."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

SEED = [
    ("Client visit, Cebu", "travel", 12450.00, "manager", "approved"),
    ("Team lunch, Makati", "meals", 3200.00, "manager", "approved"),
    ("Laptop dock", "equipment", 4599.00, "analyst", "pending"),
    ("Conference ticket", "training", 18000.00, "analyst", "pending"),
    ("Taxi to airport", "travel", 850.00, "analyst", "approved"),
    ("Monitor stand", "equipment", 1750.00, "manager", "rejected"),
]


class ReportStore:
    def __init__(self) -> None:
        self._reports: Dict[int, dict] = {}
        self._next_id = 1
        self.reset()

    def reset(self) -> None:
        self._reports.clear()
        self._next_id = 1
        for title, category, amount, who, status in SEED:
            self.add(title, category, amount, who, status)

    def add(self, title: str, category: str, amount: float,
            submitted_by: str, status: str = "pending") -> dict:
        report = {
            "id": self._next_id,
            "title": title,
            "category": category,
            "amount": round(float(amount), 2),
            "submitted_by": submitted_by,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds"),
        }
        self._reports[report["id"]] = report
        self._next_id += 1
        return report

    def all(self, category: Optional[str] = None) -> List[dict]:
        reports = sorted(self._reports.values(), key=lambda r: r["id"])
        if category:
            needle = category.casefold()
            reports = [r for r in reports if r["category"].casefold() == needle]
        return reports

    def get(self, report_id: int) -> Optional[dict]:
        return self._reports.get(report_id)

    def remove(self, report_id: int) -> bool:
        return self._reports.pop(report_id, None) is not None

    def summary(self) -> dict:
        reports = self.all()
        by_category: Dict[str, float] = {}
        for report in reports:
            by_category[report["category"]] = round(
                by_category.get(report["category"], 0.0) + report["amount"], 2)
        return {
            "report_count": len(reports),
            "total_amount": round(sum(r["amount"] for r in reports), 2),
            "by_category": by_category,
            "largest": max(reports, key=lambda r: r["amount"], default=None),
        }


store = ReportStore()
