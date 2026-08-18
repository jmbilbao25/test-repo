"""Tokens and password checking.

Two token types are issued. The access token is short lived and carries the
scopes the caller may use; the refresh token lives longer, carries no scopes at
all and is only good for getting a new access token. Both are JWTs signed with
HS256, and the type is written into the payload so a refresh token cannot be
presented as an access token.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

import bcrypt
import jwt

# In a deployed service this comes from the environment and is never committed.
# The fallback exists so the project runs after a clone.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-do-not-use-in-production")
ALGORITHM = "HS256"

ACCESS_TOKEN_MINUTES = int(os.environ.get("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_HOURS = int(os.environ.get("REFRESH_TOKEN_HOURS", "24"))

ISSUER = "secure-api"
AUDIENCE = "secure-api-clients"


class TokenError(Exception):
    """The token is missing, malformed, expired or the wrong type."""


# ------------------------------------------------------------------ passwords
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Check a password against its hash.

    bcrypt takes the same amount of time whether or not the password is right,
    which is the point: a fast rejection would leak which usernames exist.
    """
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------- tokens
def _encode(subject: str, token_type: str, lifetime: timedelta,
            scopes: Iterable[str] = ()) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "scopes": list(scopes),
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "iss": ISSUER,
        "aud": AUDIENCE,
        # A unique id per token, so a specific one could be revoked later.
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: str, scopes: Iterable[str],
                        minutes: Optional[int] = None) -> str:
    return _encode(subject, "access",
                   timedelta(minutes=minutes if minutes is not None
                             else ACCESS_TOKEN_MINUTES),
                   scopes)


def create_refresh_token(subject: str) -> str:
    # No scopes: this token cannot be used to reach a protected endpoint.
    return _encode(subject, "refresh", timedelta(hours=REFRESH_TOKEN_HOURS))


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Verify a token and return its payload.

    Every failure raises TokenError with a message safe to send to the client.
    The signature, the expiry, the issuer and the audience are all checked, and
    then the type, so an access token and a refresh token are not
    interchangeable.
    """
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            audience=AUDIENCE, issuer=ISSUER,
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("The token has expired.")
    except jwt.InvalidAudienceError:
        raise TokenError("The token was not issued for this API.")
    except jwt.InvalidIssuerError:
        raise TokenError("The token was not issued by this API.")
    except jwt.InvalidSignatureError:
        raise TokenError("The token signature does not match.")
    except jwt.InvalidTokenError as exc:
        raise TokenError(f"The token could not be read: {exc}")

    if payload.get("type") != expected_type:
        raise TokenError(
            f"Expected a {expected_type} token, got a "
            f"{payload.get('type')} token.")

    return payload
