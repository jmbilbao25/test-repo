"""Fixtures.

The limiter counts across requests, which is the point of it, but it also means
one test's traffic would otherwise spend the next test's allowance. It is turned
off by default and switched on only for the tests that are about limiting.
"""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_api import reports as reports_module
from secure_api.limits import limiter
from secure_api.main import app


@pytest.fixture(autouse=True)
def isolate():
    reports_module.store.reset()
    limiter.reset()
    limiter.enabled = False
    yield
    limiter.reset()
    limiter.enabled = False


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def limits_on():
    """Turn the limiter back on for a test that is checking it."""
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.enabled = False


def sign_in(client: TestClient, username: str, password: str,
            scope: str | None = None) -> dict:
    data = {"username": username, "password": password}
    if scope is not None:
        data["scope"] = scope
    response = client.post("/auth/token", data=data)
    assert response.status_code == 200, response.text
    return response.json()


def auth_header(client: TestClient, username: str = "manager",
                password: str | None = None, scope: str | None = None) -> dict:
    tokens = sign_in(client, username, password or f"{username}-password",
                     scope)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def analyst(client):
    return auth_header(client, "analyst")


@pytest.fixture()
def manager(client):
    return auth_header(client, "manager")


@pytest.fixture()
def admin(client):
    return auth_header(client, "admin")
