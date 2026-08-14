"""The Pandas and NumPy work behind the endpoints.

Kept out of main.py so the endpoint functions stay short enough to read and so
this can be tested without going through HTTP.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

# The comparisons /filter_data understands. Spelled out as words because a query
# string is a poor place for < and >.
OPERATORS = {
    "eq": lambda series, value: series == value,
    "ne": lambda series, value: series != value,
    "gt": lambda series, value: series > value,
    "gte": lambda series, value: series >= value,
    "lt": lambda series, value: series < value,
    "lte": lambda series, value: series <= value,
    "contains": lambda series, value: series.astype(str).str.contains(
        str(value), case=False, na=False),
}


class ColumnError(KeyError):
    """The column does not exist, or is the wrong type for the operation."""


class FilterError(ValueError):
    """The filter could not be applied as asked."""


# ------------------------------------------------------------------ utilities
def _clean(value: Any) -> Any:
    """Make a value safe to put in JSON.

    NumPy scalars are not JSON serialisable, and NaN and infinity are not valid
    JSON at all, so they become null.
    """
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if not np.isfinite(number) else round(number, 6)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    return value


def records(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    """Rows as a list of dicts, with the values cleaned for JSON."""
    return [{key: _clean(val) for key, val in row.items()}
            for row in frame.to_dict(orient="records")]


def require_column(frame: pd.DataFrame, column: str) -> None:
    if column not in frame.columns:
        raise ColumnError(
            f"No column named '{column}'. Available: "
            + ", ".join(frame.columns) + ".")


def require_numeric(frame: pd.DataFrame, column: str) -> None:
    require_column(frame, column)
    if not pd.api.types.is_numeric_dtype(frame[column]):
        raise ColumnError(f"Column '{column}' is not numeric.")


# --------------------------------------------------------------------- loading
def load_csv(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    # Normalise the headers so the query strings are predictable.
    frame.columns = [str(c).strip().lower().replace(" ", "_")
                     for c in frame.columns]
    return frame


def column_summary(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    """One entry per column: type, how many values, how many are missing."""
    out = []
    for name in frame.columns:
        series = frame[name]
        numeric = pd.api.types.is_numeric_dtype(series)
        out.append({
            "name": name,
            "dtype": str(series.dtype),
            "numeric": bool(numeric),
            "non_null": int(series.notna().sum()),
            "nulls": int(series.isna().sum()),
            "unique": int(series.nunique()),
        })
    return out


def preview(frame: pd.DataFrame, rows: int = 5) -> List[Dict[str, Any]]:
    return records(frame.head(rows))


# ------------------------------------------------------------------- describe
def describe(frame: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Pandas describe(), reshaped into column -> statistic -> value."""
    table = frame.describe(include="all").replace({np.nan: None})
    out: Dict[str, Dict[str, Any]] = {}
    for column in table.columns:
        out[str(column)] = {str(stat): _clean(table.loc[stat, column])
                            for stat in table.index}
    return out


# --------------------------------------------------------------------- filter
def coerce(value: str, series: pd.Series) -> Any:
    """Turn the query-string value into something comparable to the column.

    Everything arrives as text, so a numeric column needs the value converting
    before any comparison will mean anything.
    """
    if pd.api.types.is_numeric_dtype(series):
        try:
            return float(value)
        except (TypeError, ValueError):
            raise FilterError(
                f"'{value}' is not a number, and column '{series.name}' is "
                f"{series.dtype}.")
    return value


def filter_rows(frame: pd.DataFrame, column: str, op: str,
                value: str) -> pd.DataFrame:
    require_column(frame, column)
    if op not in OPERATORS:
        raise FilterError(
            f"Unknown operator '{op}'. Use one of: "
            + ", ".join(sorted(OPERATORS)) + ".")

    series = frame[column]
    if op == "contains" and pd.api.types.is_numeric_dtype(series):
        raise FilterError("'contains' only applies to text columns.")

    comparable = value if op == "contains" else coerce(value, series)
    return frame[OPERATORS[op](series, comparable)]


# ---------------------------------------------------------------------- stats
def numeric_stats(frame: pd.DataFrame, column: str) -> Dict[str, Any]:
    """Statistics for one numeric column, computed with NumPy.

    Pandas would give most of these directly; NumPy is used here because the
    assignment asks for it, and because the outlier bounds are easier to express
    as arithmetic on percentiles than as DataFrame operations.
    """
    require_numeric(frame, column)
    values = frame[column].to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ColumnError(f"Column '{column}' has no usable values.")

    q1, q2, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = values[(values < low) | (values > high)]

    return {
        "column": column,
        "count": int(values.size),
        "mean": _clean(np.mean(values)),
        "median": _clean(q2),
        # ddof=1 is the sample standard deviation, which is what pandas reports.
        "std": _clean(np.std(values, ddof=1)),
        "variance": _clean(np.var(values, ddof=1)),
        "min": _clean(np.min(values)),
        "max": _clean(np.max(values)),
        "range": _clean(np.ptp(values)),
        "q1": _clean(q1),
        "q3": _clean(q3),
        "iqr": _clean(iqr),
        "outlier_bounds": {"lower": _clean(low), "upper": _clean(high)},
        "outliers": [_clean(v) for v in np.sort(outliers)],
    }


# -------------------------------------------------------------------- grouping
AGGREGATIONS = ("mean", "median", "sum", "min", "max", "std", "count")


def group_by(frame: pd.DataFrame, by: str, column: str,
             agg: str = "mean") -> List[Dict[str, Any]]:
    require_column(frame, by)
    require_numeric(frame, column)
    if agg not in AGGREGATIONS:
        raise FilterError(
            f"Unknown aggregation '{agg}'. Use one of: "
            + ", ".join(AGGREGATIONS) + ".")

    grouped = frame.groupby(by)[column].agg(["count", agg]) \
        if agg != "count" else frame.groupby(by)[column].agg(["count"])

    out = []
    for key, row in grouped.iterrows():
        entry = {by: _clean(key), "count": int(row["count"])}
        entry[agg] = _clean(row[agg]) if agg in row else int(row["count"])
        out.append(entry)
    return out


# ----------------------------------------------------------------- correlation
def correlation(frame: pd.DataFrame) -> Dict[str, Any]:
    """Pearson correlation between the numeric columns, via NumPy."""
    numeric = frame.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        raise ColumnError("At least two numeric columns are needed.")

    matrix = np.corrcoef(numeric.to_numpy(dtype=float), rowvar=False)
    names = [str(c) for c in numeric.columns]
    return {
        "columns": names,
        "matrix": {
            row: {col: _clean(matrix[i][j]) for j, col in enumerate(names)}
            for i, row in enumerate(names)
        },
    }
