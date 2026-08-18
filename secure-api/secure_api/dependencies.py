"""Authentication and authorisation, as FastAPI dependencies.

OAuth2PasswordBearer is what tells FastAPI this API uses the OAuth2 password
flow. It gives Swagger UI the Authorize dialog, with the scopes listed as
checkboxes, and it is what pulls the bearer token out of the Authorization
header.

The distinction the two functions below draw is the one worth remembering:
current_user answers "who is this", and require_scopes answers "may they do
this". Failing the first is a 401, failing the second is a 403.
"""
from __future__ import annotations

from typing import List

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from .security import TokenError, decode_token
from .users import SCOPES, USERS, User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    scopes=SCOPES,
    description="Sign in with one of the demo accounts and tick the scopes to "
                "request. The token is sent as an Authorization header.",
)


def unauthorised(message: str) -> HTTPException:
    """401 with the WWW-Authenticate header the spec asks for."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "invalid_token", "message": message},
        headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
    )


def current_user(token: str = Depends(oauth2_scheme)) -> User:
    """The user the access token belongs to, or a 401."""
    try:
        payload = decode_token(token, expected_type="access")
    except TokenError as exc:
        raise unauthorised(str(exc))

    user = USERS.get(payload["sub"])
    if user is None:
        raise unauthorised("The account on this token no longer exists.")
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "account_disabled",
                    "message": "This account has been disabled."},
        )

    # Carry the scopes granted at sign-in, which may be fewer than the account
    # is entitled to, since the client chooses what to ask for.
    user = User(username=user.username, full_name=user.full_name,
                role=user.role, password_hash="", disabled=user.disabled,
                scopes=list(payload.get("scopes", [])))
    return user


def require_scopes(security_scopes: SecurityScopes,
                   user: User = Security(current_user)) -> User:
    """Reject the request unless the token carries every scope required.

    SecurityScopes is populated from the scopes listed on the endpoint, so the
    requirement is declared where the endpoint is defined rather than repeated
    here.
    """
    missing: List[str] = [s for s in security_scopes.scopes
                          if s not in user.scopes]
    if missing:
        needed = ", ".join(f"'{s}'" for s in missing)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_scope",
                "message": f"This endpoint requires the {needed} scope. "
                           f"This token carries: "
                           f"{', '.join(user.scopes) or 'no scopes'}.",
            },
            headers={"WWW-Authenticate":
                     f'Bearer error="insufficient_scope", '
                     f'scope="{" ".join(security_scopes.scopes)}"'},
        )
    return user
