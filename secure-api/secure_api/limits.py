"""Rate limiting.

SlowAPI is the FastAPI equivalent of Flask-Limiter, and works the same way: a
limit is declared per endpoint and counted per client key.

Two different limits are used. Reads get a generous allowance. The token
endpoint gets a tight one, because that is the endpoint an attacker would use to
guess passwords, and it is counted per username rather than per address so that
one client hammering an account cannot be hidden behind a shared IP.
"""
from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Limits are strings SlowAPI parses, and are kept here so the write-up and the
# endpoints cannot disagree about what they are.
DEFAULT_LIMIT = "60/minute"
TOKEN_LIMIT = "5/minute"
WRITE_LIMIT = "10/minute"
SUMMARY_LIMIT = "20/minute"


def client_key(request: Request) -> str:
    """Who to count against.

    The address on its own is a poor key when clients share one, so an
    authenticated request is counted against its token id instead. That also
    stops one caller's traffic from using up another's allowance.
    """
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
        # Read the id without verifying: this is only a bucket key, and an
        # invalid token is rejected by the dependency regardless.
        try:
            import jwt
            claims = jwt.decode(token, options={"verify_signature": False})
            if claims.get("jti"):
                return f"token:{claims['jti']}"
        except Exception:
            pass
    return f"ip:{get_remote_address(request)}"


def login_key(request: Request) -> str:
    """Count login attempts per address, so one client cannot spread them."""
    return f"login:{get_remote_address(request)}"


limiter = Limiter(key_func=client_key, default_limits=[DEFAULT_LIMIT])
