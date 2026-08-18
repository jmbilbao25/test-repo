"""Rate limiting.

These are the only tests that run with the limiter switched on, so the counters
belong to the test that is looking at them.
"""
from __future__ import annotations

from secure_api.limits import TOKEN_LIMIT, WRITE_LIMIT
from tests.conftest import auth_header


def test_the_sixth_login_attempt_in_a_minute_is_refused(client, limits_on):
    """5/minute on the token endpoint, so the sixth call is a 429."""
    for attempt in range(5):
        response = client.post("/auth/token", data={
            "username": "manager", "password": "manager-password"})
        assert response.status_code == 200, f"attempt {attempt + 1}"

    blocked = client.post("/auth/token", data={
        "username": "manager", "password": "manager-password"})
    assert blocked.status_code == 429
    assert blocked.json()["error"] == "rate_limit_exceeded"


def test_the_429_says_what_the_limit_was_and_when_to_retry(client, limits_on):
    for _ in range(5):
        client.post("/auth/token", data={"username": "manager",
                                         "password": "manager-password"})
    blocked = client.post("/auth/token", data={"username": "manager",
                                              "password": "manager-password"})
    body = blocked.json()
    assert body["limit"] == TOKEN_LIMIT.replace("/", " per 1 ")
    assert body["retry_after_seconds"] == 60
    assert blocked.headers["Retry-After"] == "60"


def test_failed_logins_count_towards_the_limit(client, limits_on):
    """Otherwise the limit would not slow a password guesser down at all."""
    for _ in range(5):
        assert client.post("/auth/token", data={
            "username": "manager", "password": "wrong"}).status_code == 401

    blocked = client.post("/auth/token", data={
        "username": "manager", "password": "manager-password"})
    assert blocked.status_code == 429


def test_the_login_limit_does_not_block_reading(client, limits_on):
    """Different limits, counted separately."""
    header = auth_header(client, "manager")
    for _ in range(4):
        client.post("/auth/token", data={"username": "manager",
                                         "password": "wrong"})
    assert client.get("/reports", headers=header).status_code == 200


def test_writes_have_a_tighter_limit_than_reads(client, limits_on):
    header = auth_header(client, "manager")
    allowed = int(WRITE_LIMIT.split("/")[0])

    for i in range(allowed):
        response = client.post("/reports", headers=header, json={
            "title": f"Item {i}", "category": "meals", "amount": 100.0})
        assert response.status_code == 201, f"write {i + 1}"

    blocked = client.post("/reports", headers=header, json={
        "title": "One too many", "category": "meals", "amount": 100.0})
    assert blocked.status_code == 429
    # The write was refused, so the report was not created.
    assert client.get("/reports", headers=header).json()["count"] == \
        6 + allowed


def test_reads_are_still_allowed_after_writes_are_limited(client, limits_on):
    header = auth_header(client, "manager")
    for i in range(int(WRITE_LIMIT.split("/")[0]) + 1):
        client.post("/reports", headers=header, json={
            "title": f"Item {i}", "category": "meals", "amount": 100.0})
    assert client.get("/reports", headers=header).status_code == 200


def test_two_tokens_get_separate_allowances(client, limits_on):
    """Reads are counted per token, so one caller cannot exhaust another's."""
    first = auth_header(client, "manager")
    second = auth_header(client, "admin")

    for i in range(int(WRITE_LIMIT.split("/")[0])):
        assert client.post("/reports", headers=first, json={
            "title": f"First {i}", "category": "meals",
            "amount": 100.0}).status_code == 201
    assert client.post("/reports", headers=first, json={
        "title": "over", "category": "meals", "amount": 1.0}).status_code == 429

    # The other token has not spent anything.
    assert client.post("/reports", headers=second, json={
        "title": "Second client", "category": "meals",
        "amount": 100.0}).status_code == 201


def test_the_summary_limit_is_tighter_than_the_default(client, limits_on):
    header = auth_header(client, "analyst")
    for i in range(20):
        assert client.get("/reports/summary",
                          headers=header).status_code == 200, i
    assert client.get("/reports/summary", headers=header).status_code == 429
    # The plain list is on the default limit and still answers.
    assert client.get("/reports", headers=header).status_code == 200
