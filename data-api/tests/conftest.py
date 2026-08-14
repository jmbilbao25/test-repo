"""Fixtures for the API tests."""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_api import state
from data_api.main import app


@pytest.fixture(autouse=True)
def clean_state():
    """Each test starts with nothing loaded."""
    state.clear()
    yield
    state.clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def loaded(client: TestClient) -> TestClient:
    """A client with the dataset already loaded."""
    assert client.post("/load_data").status_code == 200
    return client
