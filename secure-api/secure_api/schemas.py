"""Request and response models. FastAPI builds the Swagger page from these."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    """The response from the token endpoint, in the shape OAuth2 defines."""
    access_token: str = Field(description="Send as: Authorization: Bearer ...")
    refresh_token: str = Field(description="Only good for /auth/refresh.")
    token_type: str = Field("bearer", examples=["bearer"])
    expires_in: int = Field(description="Access token lifetime in seconds.",
                            examples=[900])
    scope: str = Field(description="Space separated scopes that were granted.",
                       examples=["reports:read reports:write"])


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="A refresh token from /auth/token.")


class Identity(BaseModel):
    """Who the presented token belongs to."""
    username: str
    full_name: str
    role: str
    scopes: List[str] = Field(description="Scopes carried by this token.")
    token_issued_at: str
    token_expires_at: str
    token_id: str = Field(description="The jti claim.")


class Report(BaseModel):
    id: int
    title: str = Field(examples=["Client visit, Cebu"])
    category: str = Field(examples=["travel"])
    amount: float = Field(examples=[12450.0], description="In pesos.")
    submitted_by: str
    status: str = Field(examples=["approved"])
    created_at: str


class NewReport(BaseModel):
    title: str = Field(min_length=1, max_length=120,
                       examples=["Team lunch, Makati"])
    category: str = Field(examples=["meals"])
    amount: float = Field(gt=0, le=1_000_000, examples=[3200.0])


class ReportList(BaseModel):
    count: int
    total_amount: float = Field(description="Sum of the amounts returned.")
    reports: List[Report]


class Summary(BaseModel):
    """An aggregate, so there is something to read that is not a raw list."""
    report_count: int
    total_amount: float
    by_category: dict = Field(description="Category to total amount.")
    largest: Optional[Report]


class Error(BaseModel):
    """The shape every failure uses."""
    error: str = Field(description="A short machine-readable code.",
                       examples=["insufficient_scope"])
    message: str = Field(description="A sentence explaining the refusal.",
                         examples=["This endpoint requires the "
                                   "'reports:write' scope."])


class RateLimited(BaseModel):
    error: str = Field(examples=["rate_limit_exceeded"])
    message: str
    limit: str = Field(description="The limit that was hit.",
                       examples=["5 per 1 minute"])
    retry_after_seconds: int
