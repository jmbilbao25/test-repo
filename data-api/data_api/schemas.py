"""Response models.

FastAPI builds the OpenAPI document from these, so what appears in Swagger UI at
/docs is generated from the same classes the endpoints return. Describing the
fields here is what makes those docs worth reading.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Health(BaseModel):
    status: str = Field(examples=["ok"])
    data_loaded: bool = Field(description="Whether a dataset is in memory.")
    rows: Optional[int] = Field(None, description="Rows loaded, if any.")


class ColumnInfo(BaseModel):
    name: str = Field(examples=["petal_length"])
    dtype: str = Field(description="The pandas dtype.", examples=["float64"])
    numeric: bool = Field(description="Whether statistics can be run on it.")
    non_null: int
    nulls: int
    unique: int = Field(description="How many distinct values.")


class LoadResult(BaseModel):
    """What POST /load_data reports back."""
    source: str = Field(description="The file that was read.",
                        examples=["data/iris.csv"])
    loaded_at: str = Field(description="UTC timestamp of the load.")
    rows: int = Field(examples=[150])
    columns: int = Field(examples=[5])
    column_names: List[str]
    dtypes: Dict[str, str] = Field(description="Column name to pandas dtype.")
    memory_bytes: int = Field(description="What the DataFrame occupies.")
    preview: List[Dict[str, Any]] = Field(description="The first five rows.")


class ColumnsResult(BaseModel):
    rows: int
    columns: List[ColumnInfo]


class DescribeResult(BaseModel):
    """Pandas describe(), keyed by column and then by statistic."""
    rows: int
    statistics: List[str] = Field(
        description="The statistics present, in order.",
        examples=[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]])
    describe: Dict[str, Dict[str, Any]]


class FilterResult(BaseModel):
    column: str
    op: str = Field(description="The comparison that was applied.")
    value: str = Field(description="The value as it arrived in the query.")
    matched: int = Field(description="Rows that satisfied the condition.")
    total: int = Field(description="Rows in the dataset.")
    returned: int = Field(description="Rows in this response, after limit.")
    limit: int
    rows: List[Dict[str, Any]]


class OutlierBounds(BaseModel):
    lower: Optional[float]
    upper: Optional[float]


class StatsResult(BaseModel):
    """Computed with NumPy rather than pandas."""
    column: str
    count: int
    mean: Optional[float]
    median: Optional[float]
    std: Optional[float] = Field(None, description="Sample standard deviation.")
    variance: Optional[float]
    min: Optional[float]
    max: Optional[float]
    range: Optional[float]
    q1: Optional[float]
    q3: Optional[float]
    iqr: Optional[float]
    outlier_bounds: OutlierBounds = Field(
        description="Tukey fences, q1 - 1.5*iqr and q3 + 1.5*iqr.")
    outliers: List[float] = Field(description="Values outside those bounds.")


class GroupByResult(BaseModel):
    by: str
    column: str
    agg: str
    groups: List[Dict[str, Any]]


class CorrelationResult(BaseModel):
    columns: List[str]
    matrix: Dict[str, Dict[str, Optional[float]]] = Field(
        description="Pearson coefficients from numpy.corrcoef.")


class Error(BaseModel):
    """The shape every failure uses."""
    error: str = Field(description="A short machine-readable code.",
                       examples=["data_not_loaded"])
    message: str = Field(description="A sentence explaining what went wrong.",
                         examples=["No dataset is loaded. Call POST /load_data first."])
