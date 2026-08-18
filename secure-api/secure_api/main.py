"""A secured REST API: OAuth2 password flow, JWT bearer tokens, rate limiting.

    POST /auth/token       exchange username and password for tokens
    POST /auth/refresh     exchange a refresh token for a new access token
    GET  /auth/me          who the presented token belongs to
    GET  /reports          list reports            needs reports:read
    GET  /reports/{id}     one report              needs reports:read
    POST /reports          create a report         needs reports:write
    DELETE /reports/{id}   delete a report         needs reports:delete
    GET  /reports/summary  totals by category      needs reports:read
    GET  /health           public, no token needed

Swagger UI is at /docs, ReDoc at /redoc.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import (Depends, FastAPI, HTTPException, Path, Query, Request,
                     Security, status)
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from . import reports as reports_module
from .dependencies import current_user, oauth2_scheme, require_scopes
from .limits import (DEFAULT_LIMIT, SUMMARY_LIMIT, TOKEN_LIMIT, WRITE_LIMIT,
                     limiter, login_key)
from .schemas import (AccessToken, Error, Identity, NewReport, RateLimited,
                      Report, ReportList, Summary, TokenPair)
from .security import (ACCESS_TOKEN_MINUTES, TokenError, create_access_token,
                       create_refresh_token, decode_token)
from .users import SCOPES, USERS, User, authenticate

DESCRIPTION = f"""
An expense reports API, used here to demonstrate how the endpoints are secured
rather than for the reports themselves.

### Signing in
`POST /auth/token` takes a username and password as form fields, the OAuth2
password grant, and returns a short lived **access token** plus a longer lived
**refresh token**. Send the access token as `Authorization: Bearer <token>`.

Press **Authorize** to sign in from this page. The scopes are checkboxes: a token
only carries what was asked for, so requesting fewer scopes gives a token that
can do less.

### Accounts
| Username | Password | Scopes |
| --- | --- | --- |
| `analyst` | `analyst-password` | `reports:read` |
| `manager` | `manager-password` | `reports:read`, `reports:write` |
| `admin` | `admin-password` | all three |

### Rate limits
`{TOKEN_LIMIT}` on the token endpoint, counted per address, because that is the
endpoint a password guesser would use. `{WRITE_LIMIT}` on writes,
`{SUMMARY_LIMIT}` on the summary and `{DEFAULT_LIMIT}` everywhere else, counted
per token. Going over returns **429** with a `Retry-After` header.
"""

TAGS = [
    {"name": "auth", "description": "Getting and refreshing tokens."},
    {"name": "reports", "description": "The protected data. Every endpoint "
                                       "needs a scope."},
    {"name": "service", "description": "Open endpoints."},
]

UNAUTHORISED = {"model": Error, "description": "Missing, invalid or expired "
                                               "token."}
FORBIDDEN = {"model": Error, "description": "The token lacks the required "
                                            "scope."}
LIMITED = {"model": RateLimited, "description": "Rate limit exceeded."}

app = FastAPI(
    title="Secure Expense Reports API",
    version="1.0.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
    contact={"name": "John Michael Bilbao"},
)

app.state.limiter = limiter


# ------------------------------------------------------------- error shaping
@app.exception_handler(RateLimitExceeded)
async def rate_limited(request: Request, exc: RateLimitExceeded):
    """429 with a body in the same shape as every other error."""
    retry_after = 60
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Slow down and try again shortly.",
            "limit": str(exc.detail),
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException):
    """Keep every failure in the {error, message} shape.

    FastAPI puts whatever it is given into `detail`; the dependencies raise a
    dict in the right shape already, and anything else is wrapped here.
    """
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = detail
    else:
        body = {"error": "error", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=body,
                        headers=getattr(exc, "headers", None))


# -------------------------------------------------------------------- service
@app.get("/health", tags=["service"], summary="Open endpoint, no token needed")
@limiter.limit(DEFAULT_LIMIT)
def health(request: Request):
    return {"status": "ok", "authentication": "OAuth2 password flow, JWT bearer",
            "scopes_available": sorted(SCOPES)}


# ----------------------------------------------------------------------- auth
@app.post("/auth/token", response_model=TokenPair, tags=["auth"],
          summary="Exchange username and password for tokens",
          description="The OAuth2 password grant. Send `username`, `password` "
                      "and optionally `scope` as form fields. Scopes the "
                      "account is not entitled to are refused rather than "
                      "silently dropped.",
          responses={400: {"model": Error,
                           "description": "A scope the account cannot have."},
                     401: {"model": Error,
                           "description": "Wrong username or password."},
                     429: LIMITED})
@limiter.limit(TOKEN_LIMIT, key_func=login_key)
def issue_token(request: Request,
                form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(form.username, form.password)
    if user is None:
        # The same message either way, so it cannot be used to work out which
        # usernames exist.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials",
                    "message": "Incorrect username or password."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "account_disabled",
                    "message": "This account has been disabled."},
        )

    # No scope asked for means everything the account is entitled to.
    requested = form.scopes or list(user.scopes)
    refused = [s for s in requested if s not in user.scopes]
    if refused:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_scope",
                    "message": f"This account cannot be granted "
                               f"{', '.join(repr(s) for s in refused)}. "
                               f"It may have: "
                               f"{', '.join(user.scopes) or 'no scopes'}."},
        )

    return TokenPair(
        access_token=create_access_token(user.username, requested),
        refresh_token=create_refresh_token(user.username),
        token_type="bearer",
        expires_in=ACCESS_TOKEN_MINUTES * 60,
        scope=" ".join(requested),
    )


@app.post("/auth/refresh", response_model=AccessToken, tags=["auth"],
          summary="Trade a refresh token for a new access token",
          description="Send the refresh token in the `Authorization` header. An "
                      "access token is rejected here, and a refresh token is "
                      "rejected everywhere else.",
          responses={401: UNAUTHORISED, 429: LIMITED})
@limiter.limit(DEFAULT_LIMIT)
def refresh(request: Request, token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": str(exc)},
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    user = USERS.get(payload["sub"])
    if user is None or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token",
                    "message": "This account can no longer sign in."},
        )

    return AccessToken(
        access_token=create_access_token(user.username, user.scopes),
        token_type="bearer",
        expires_in=ACCESS_TOKEN_MINUTES * 60,
        scope=" ".join(user.scopes),
    )


@app.get("/auth/me", response_model=Identity, tags=["auth"],
         summary="Who this token belongs to",
         responses={401: UNAUTHORISED, 429: LIMITED})
@limiter.limit(DEFAULT_LIMIT)
def me(request: Request, token: str = Depends(oauth2_scheme),
       user: User = Depends(current_user)):
    claims = decode_token(token)
    when = lambda ts: datetime.fromtimestamp(ts, timezone.utc).isoformat(
        timespec="seconds")
    return Identity(
        username=user.username, full_name=user.full_name, role=user.role,
        scopes=user.scopes,
        token_issued_at=when(claims["iat"]),
        token_expires_at=when(claims["exp"]),
        token_id=claims["jti"],
    )


# -------------------------------------------------------------------- reports
@app.get("/reports/summary", response_model=Summary, tags=["reports"],
         summary="Totals by category",
         description="Needs the `reports:read` scope. Rate limited more tightly "
                     "than the plain list, since it does more work per call.",
         responses={401: UNAUTHORISED, 403: FORBIDDEN, 429: LIMITED})
@limiter.limit(SUMMARY_LIMIT)
def summary(request: Request,
            user: User = Security(require_scopes, scopes=["reports:read"])):
    return Summary(**reports_module.store.summary())


@app.get("/reports", response_model=ReportList, tags=["reports"],
         summary="List reports",
         description="Needs the `reports:read` scope.",
         responses={401: UNAUTHORISED, 403: FORBIDDEN, 429: LIMITED})
@limiter.limit(DEFAULT_LIMIT)
def list_reports(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category.",
                                    examples=["travel"]),
    user: User = Security(require_scopes, scopes=["reports:read"]),
):
    found = reports_module.store.all(category=category)
    return ReportList(
        count=len(found),
        total_amount=round(sum(r["amount"] for r in found), 2),
        reports=found,
    )


@app.get("/reports/{report_id}", response_model=Report, tags=["reports"],
         summary="One report by id",
         description="Needs the `reports:read` scope.",
         responses={401: UNAUTHORISED, 403: FORBIDDEN,
                    404: {"model": Error, "description": "No such report."},
                    429: LIMITED})
@limiter.limit(DEFAULT_LIMIT)
def get_report(request: Request, report_id: int = Path(ge=1, examples=[1]),
               user: User = Security(require_scopes, scopes=["reports:read"])):
    report = reports_module.store.get(report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found",
                    "message": f"No report with id {report_id}."})
    return report


@app.post("/reports", response_model=Report, status_code=201, tags=["reports"],
          summary="Create a report",
          description="Needs the `reports:write` scope, which the `analyst` "
                      "account does not have.",
          responses={401: UNAUTHORISED, 403: FORBIDDEN, 429: LIMITED})
@limiter.limit(WRITE_LIMIT)
def create_report(
    request: Request, body: NewReport,
    user: User = Security(require_scopes, scopes=["reports:write"]),
):
    return reports_module.store.add(body.title, body.category, body.amount,
                                    user.username)


@app.delete("/reports/{report_id}", status_code=204, tags=["reports"],
            summary="Delete a report",
            description="Needs the `reports:delete` scope, which only `admin` "
                        "has.",
            responses={401: UNAUTHORISED, 403: FORBIDDEN,
                       404: {"model": Error, "description": "No such report."},
                       429: LIMITED})
@limiter.limit(WRITE_LIMIT)
def delete_report(
    request: Request, report_id: int = Path(ge=1),
    user: User = Security(require_scopes, scopes=["reports:delete"]),
):
    if not reports_module.store.remove(report_id):
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found",
                    "message": f"No report with id {report_id}."})
    return JSONResponse(status_code=204, content=None)


# ------------------------------------------------------------- the demo client
# The practical use case: a page that signs in, keeps the token and calls the
# API. Mounted last so it cannot shadow an endpoint. The path is resolved from
# this file rather than the working directory, so it works from anywhere.
WEBAPP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "webapp")
if os.path.isdir(WEBAPP_DIR):
    app.mount("/app", StaticFiles(directory=WEBAPP_DIR, html=True),
              name="webapp")
