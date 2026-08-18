"""The accounts, and the scopes each one is allowed to ask for.

Three accounts with different permissions, so the difference between being
authenticated and being authorised can actually be demonstrated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .security import hash_password, verify_password

# What each scope permits. Swagger UI lists these next to the checkboxes in the
# Authorize dialog.
SCOPES = {
    "reports:read": "Read expense reports",
    "reports:write": "Create and update expense reports",
    "reports:delete": "Delete expense reports",
}


@dataclass
class User:
    username: str
    full_name: str
    role: str
    password_hash: str
    scopes: List[str] = field(default_factory=list)
    disabled: bool = False


# Passwords are hashed at import, never stored in plain text. They are weak on
# purpose so the write-up can show the requests that use them.
_RAW = [
    ("analyst", "Ana Lyst", "analyst", "analyst-password",
     ["reports:read"]),
    ("manager", "Man Ager", "manager", "manager-password",
     ["reports:read", "reports:write"]),
    ("admin", "Ad Min", "admin", "admin-password",
     ["reports:read", "reports:write", "reports:delete"]),
    ("retired", "Rhett Ired", "analyst", "retired-password",
     ["reports:read"]),
]

USERS: Dict[str, User] = {
    username: User(username=username, full_name=full_name, role=role,
                   password_hash=hash_password(password), scopes=scopes,
                   disabled=(username == "retired"))
    for username, full_name, role, password, scopes in _RAW
}


def authenticate(username: str, password: str) -> Optional[User]:
    """Return the user if the credentials are right, otherwise None.

    The password is checked even when the username is unknown, against a hash
    that cannot match. Returning early would make a missing account measurably
    faster to reject than a wrong password, which tells an attacker which
    usernames are real.
    """
    user = USERS.get(username)
    reference = user.password_hash if user else hash_password("no-such-user")
    correct = verify_password(password, reference)
    if user is None or not correct:
        return None
    return user
