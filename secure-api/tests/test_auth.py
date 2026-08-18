"""Signing in, and what the tokens are and are not good for."""
from __future__ import annotations

import time

import jwt
import pytest

from secure_api.security import (ALGORITHM, AUDIENCE, SECRET_KEY,
                                 create_access_token, decode_token)
from tests.conftest import auth_header, sign_in


# ------------------------------------------------------------------ signing in
def test_token_endpoint_returns_both_tokens(client):
    body = sign_in(client, "manager", "manager-password")
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["access_token"] and body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


def test_scopes_default_to_everything_the_account_has(client):
    assert sign_in(client, "analyst", "analyst-password")["scope"] == \
        "reports:read"
    assert sign_in(client, "admin", "admin-password")["scope"] == \
        "reports:read reports:write reports:delete"


def test_a_client_can_ask_for_fewer_scopes(client):
    body = sign_in(client, "admin", "admin-password", scope="reports:read")
    assert body["scope"] == "reports:read"
    assert decode_token(body["access_token"])["scopes"] == ["reports:read"]


def test_asking_for_a_scope_the_account_lacks_is_refused(client):
    response = client.post("/auth/token", data={
        "username": "analyst", "password": "analyst-password",
        "scope": "reports:delete"})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_scope"


def test_wrong_password_is_401(client):
    response = client.post("/auth/token", data={
        "username": "manager", "password": "not-the-password"})
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_unknown_user_gives_the_same_message_as_a_wrong_password(client):
    """Different messages would reveal which usernames exist."""
    missing = client.post("/auth/token", data={
        "username": "nobody", "password": "x"})
    wrong = client.post("/auth/token", data={
        "username": "manager", "password": "x"})
    assert missing.status_code == wrong.status_code == 401
    assert missing.json() == wrong.json()


def test_a_disabled_account_cannot_sign_in(client):
    response = client.post("/auth/token", data={
        "username": "retired", "password": "retired-password"})
    assert response.status_code == 403
    assert response.json()["error"] == "account_disabled"


def test_401_carries_the_www_authenticate_header(client):
    response = client.post("/auth/token", data={
        "username": "manager", "password": "wrong"})
    assert "WWW-Authenticate" in response.headers


# --------------------------------------------------------------- the payload
def test_the_access_token_says_what_it_is(client):
    body = sign_in(client, "manager", "manager-password")
    claims = jwt.decode(body["access_token"], SECRET_KEY,
                        algorithms=[ALGORITHM], audience=AUDIENCE)
    assert claims["sub"] == "manager"
    assert claims["type"] == "access"
    assert claims["scopes"] == ["reports:read", "reports:write"]
    assert claims["iss"] == "secure-api"
    assert claims["exp"] > claims["iat"]
    assert claims["jti"]


def test_the_refresh_token_carries_no_scopes(client):
    body = sign_in(client, "admin", "admin-password")
    claims = decode_token(body["refresh_token"], expected_type="refresh")
    assert claims["type"] == "refresh"
    assert claims["scopes"] == []


def test_two_sign_ins_give_different_token_ids(client):
    first = decode_token(sign_in(client, "manager",
                                 "manager-password")["access_token"])
    second = decode_token(sign_in(client, "manager",
                                  "manager-password")["access_token"])
    assert first["jti"] != second["jti"]


def test_the_password_is_never_in_the_token(client):
    body = sign_in(client, "manager", "manager-password")
    assert "manager-password" not in body["access_token"]


# ----------------------------------------------------------- rejecting tokens
def test_no_token_is_401(client):
    response = client.get("/reports")
    assert response.status_code == 401


def test_a_tampered_signature_is_rejected(client, manager):
    """Change one character of the signature and it must not be accepted."""
    token = manager["Authorization"].split()[1]
    head, payload, signature = token.split(".")
    swapped = "B" if signature[0] != "B" else "C"
    broken = f"{head}.{payload}.{swapped}{signature[1:]}"
    response = client.get("/reports",
                          headers={"Authorization": f"Bearer {broken}"})
    assert response.status_code == 401
    assert "signature" in response.json()["message"].lower()


def test_editing_the_payload_invalidates_the_token(client, analyst):
    """Escalating the scopes inside the payload must not work.

    The claims are only base64, so anyone can read and rewrite them. What stops
    this is that the signature no longer matches.
    """
    import base64
    import json
    token = analyst["Authorization"].split()[1]
    head, payload, signature = token.split(".")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    assert claims["scopes"] == ["reports:read"]

    claims["scopes"] = ["reports:read", "reports:write", "reports:delete"]
    forged = base64.urlsafe_b64encode(
        json.dumps(claims).encode()).decode().rstrip("=")
    response = client.post("/reports",
                           headers={"Authorization":
                                    f"Bearer {head}.{forged}.{signature}"},
                           json={"title": "Forged", "category": "meals",
                                 "amount": 1.0})
    assert response.status_code == 401


def test_a_token_signed_with_another_key_is_rejected(client):
    """The API must only trust tokens it signed itself."""
    outsider = jwt.encode(
        {"sub": "admin", "type": "access",
         "scopes": ["reports:read", "reports:delete"],
         "iat": int(time.time()), "exp": int(time.time()) + 600,
         "iss": "secure-api", "aud": AUDIENCE},
        # Long enough not to trigger PyJWT's short-key warning; the point is
        # that it is the wrong key, not a weak one.
        "a-different-secret-of-a-perfectly-respectable-length",
        algorithm=ALGORITHM)
    response = client.get("/reports",
                          headers={"Authorization": f"Bearer {outsider}"})
    assert response.status_code == 401


def test_an_expired_token_is_rejected(client):
    expired = create_access_token("manager", ["reports:read"], minutes=-1)
    response = client.get("/reports",
                          headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert "expired" in response.json()["message"].lower()


def test_nonsense_instead_of_a_token_is_rejected(client):
    for value in ["Bearer not-a-jwt", "Bearer a.b.c", "Basic dXNlcjpwYXNz",
                  "Bearer "]:
        assert client.get("/reports",
                          headers={"Authorization": value}).status_code == 401


def test_a_refresh_token_cannot_be_used_as_an_access_token(client):
    """The type claim is what keeps the two apart."""
    refresh = sign_in(client, "manager", "manager-password")["refresh_token"]
    response = client.get("/reports",
                          headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 401
    assert "access token" in response.json()["message"]


# -------------------------------------------------------------------- refresh
def test_refresh_returns_a_new_access_token(client):
    refresh = sign_in(client, "manager", "manager-password")["refresh_token"]
    response = client.post("/auth/refresh",
                           headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 200
    assert response.json()["scope"] == "reports:read reports:write"
    new_token = response.json()["access_token"]
    assert client.get("/reports", headers={
        "Authorization": f"Bearer {new_token}"}).status_code == 200


def test_an_access_token_is_refused_at_the_refresh_endpoint(client, manager):
    response = client.post("/auth/refresh", headers=manager)
    assert response.status_code == 401
    assert "refresh token" in response.json()["message"]


# ----------------------------------------------------------------- /auth/me
def test_me_describes_the_token(client, analyst):
    body = client.get("/auth/me", headers=analyst).json()
    assert body["username"] == "analyst"
    assert body["role"] == "analyst"
    assert body["scopes"] == ["reports:read"]
    assert body["token_expires_at"] > body["token_issued_at"]
    assert body["token_id"]


def test_me_needs_a_token(client):
    assert client.get("/auth/me").status_code == 401
