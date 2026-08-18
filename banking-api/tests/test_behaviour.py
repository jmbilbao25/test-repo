"""What the submitted API actually does.

These tests are not here to show the code works. They are here to pin down its
behaviour precisely, including the places where the behaviour and the case
study's stated intent do not line up. Each one that documents a gap says so.

    python3 -m pytest tests -v
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as application
from app import app, run_numpy_fraud_detection

SEED = list(application.db_transactions)


@pytest.fixture(autouse=True)
def isolate():
    """db_transactions is module-level and every handler mutates it, so each
    test has to put it back or the tests affect one another."""
    application.db_transactions[:] = [dict(t) for t in SEED]
    yield
    application.db_transactions[:] = [dict(t) for t in SEED]


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def post(client, txid: str, account: str, amount: float,
         category: str = "groceries"):
    return client.post("/v1/transactions", json={
        "transaction_id": txid, "account_id": account,
        "amount": amount, "category": category})


# --------------------------------------------------------- the happy path

def test_normal_transaction_is_approved_and_not_flagged(client):
    r = post(client, "tx_201", "acc_1", 50.00)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "APPROVED"
    assert body["fraud_assessment"]["is_anomaly"] is False
    assert body["fraud_assessment"]["z_score"] == -0.97


def test_reproduces_the_submitted_session(client):
    """The exact two calls from the submitted PowerShell screenshot."""
    first = post(client, "tx_201", "acc_1", 50.00).json()["fraud_assessment"]
    assert first == {"is_anomaly": False, "z_score": -0.97,
                     "mean_spend": 158.5, "std_dev": 111.47}

    second = post(client, "tx_202", "acc_1", 4500.00,
                  "jewelry").json()["fraud_assessment"]
    assert second == {"is_anomaly": True, "z_score": 40.69,
                      "mean_spend": 131.38, "std_dev": 107.36}

    summary = client.get("/v1/accounts/acc_1/summary").json()
    assert summary["metrics"] == {"total_spent": 5025.5,
                                  "avg_transaction": 1005.1,
                                  "total_transactions": 5}

    matrix = client.get("/v1/analytics/batch-risk-matrix").json()
    assert matrix["accounts_checked"] == 3
    assert matrix["portfolio_p95_threshold"] == 3810.0
    assert matrix["portfolio_total_volume"] == 7240.5


def test_account_summary_shape(client):
    body = client.get("/v1/accounts/acc_1/summary").json()
    assert body["account_id"] == "acc_1"
    assert body["metrics"]["total_transactions"] == 3
    assert body["spend_by_category"] == {"groceries": 120.5, "dining": 45.0,
                                         "electronics": 310.0}


def test_unknown_account_summary_is_404(client):
    assert client.get("/v1/accounts/acc_nope/summary").status_code == 404


def test_rejects_account_the_mainframe_does_not_recognise(client):
    r = post(client, "tx_900", "not_an_account", 10.0)
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid account ID"


@pytest.mark.parametrize("amount", [0, -1, -100.5])
def test_rejects_non_positive_amounts(client, amount):
    assert post(client, "tx_901", "acc_1", amount).status_code == 422


def test_gather_checks_every_distinct_account(client):
    body = client.get("/v1/analytics/batch-risk-matrix").json()
    assert body["accounts_checked"] == 3
    assert body["portfolio_total_volume"] == 2690.5


# ------------------------------------------- gaps between intent and behaviour

def test_flagged_transaction_is_still_approved(client):
    """The case study says fraud is caught "before authorization". It is not.

    A transaction 40 standard deviations from the account's mean is flagged,
    an alert is dispatched, and the API still answers APPROVED. Nothing in the
    request path can decline.
    """
    body = post(client, "tx_202", "acc_1", 4500.00, "jewelry").json()
    assert body["fraud_assessment"]["is_anomaly"] is True
    # 38.95 here rather than the 40.69 in the screenshot: this test posts
    # tx_202 against the seed data alone, whereas that session posted tx_201
    # first, which moved the baseline. The score depends on arrival order.
    assert body["fraud_assessment"]["z_score"] == 38.95
    assert body["status"] == "APPROVED"          # the gap


def test_a_new_account_cannot_be_flagged_at_all(client):
    """With fewer than two prior transactions the check returns early, so the
    first two transactions on a fresh account are unflaggable regardless of
    amount. A large first transaction is the common fraud pattern."""
    first = post(client, "tx_first", "acc_new", 999_999.0).json()
    assert first["status"] == "APPROVED"
    assert first["fraud_assessment"]["is_anomaly"] is False
    assert first["fraud_assessment"]["z_score"] == 0.0

    second = post(client, "tx_second", "acc_new", 999_999.0).json()
    assert second["fraud_assessment"]["is_anomaly"] is False


def test_any_acc_prefixed_string_is_a_valid_account(client):
    """simulate_mainframe_check only tests the prefix, so an account that has
    never existed is accepted and silently created by the write."""
    assert post(client, "tx_ghost", "acc_does_not_exist", 500.0).status_code == 201
    assert client.get("/v1/accounts/acc_does_not_exist/summary").status_code == 200


def test_duplicate_transaction_id_is_accepted_twice(client):
    """There is no idempotency check, so a retried payment is stored twice and
    counted twice in the totals."""
    assert post(client, "tx_dup", "acc_2", 100.0).status_code == 201
    assert post(client, "tx_dup", "acc_2", 100.0).status_code == 201

    stored = [t for t in application.db_transactions
              if t["transaction_id"] == "tx_dup"]
    assert len(stored) == 2
    assert client.get("/v1/accounts/acc_2/summary").json()[
        "metrics"]["total_spent"] == 215.0


def test_the_transaction_being_assessed_is_excluded_from_its_own_baseline(client):
    """Worth stating because it is correct, and easy to get wrong: history is
    read before the new record is appended, so the mean it is compared against
    does not include it."""
    body = post(client, "tx_x", "acc_1", 1000.0).json()
    assert body["fraud_assessment"]["mean_spend"] == 158.5   # the seed's mean


def test_z_score_uses_population_not_sample_deviation():
    """np.std defaults to ddof=0. On three observations the sample deviation
    (ddof=1) is 36% larger, so the divisor is smaller than a statistician would
    use and every z-score is correspondingly inflated."""
    history = [120.50, 45.00, 310.00]
    got = run_numpy_fraud_detection(4500.0, history)

    population = float(np.std(history))
    sample = float(np.std(history, ddof=1))

    assert got["std_dev"] == round(population, 2)
    assert sample > population
    inflated = (4500.0 - np.mean(history)) / population
    corrected = (4500.0 - np.mean(history)) / sample
    assert inflated > corrected


def test_an_account_with_constant_history_can_never_be_flagged():
    """If every prior amount is identical the deviation is zero, and the code
    takes its `if std == 0` branch and returns a z-score of 0.0. The size of
    the new transaction is not considered at all.

    A subscription-like account paying the same amount each cycle therefore has
    no working fraud check, and one extra differing amount is enough to restore
    it.
    """
    identical = [100.0, 100.0, 100.0]
    verdict = run_numpy_fraud_detection(10_000_000.0, identical)
    assert verdict["std_dev"] == 0.0
    assert verdict["z_score"] == 0.0
    assert verdict["is_anomaly"] is False

    # Vary one amount by 50 cents and the same transaction is caught.
    assert run_numpy_fraud_detection(
        10_000_000.0, [100.0, 100.0, 100.5])["is_anomaly"] is True


def test_the_threshold_is_reachable_on_a_three_point_baseline():
    """Stated because the opposite is a tempting assumption: a new amount is
    scored against the baseline's own mean and deviation, so its z-score has no
    upper bound and three prior transactions are enough to flag a fourth."""
    history = [120.50, 45.00, 310.00]
    assert run_numpy_fraud_detection(4500.0, history)["z_score"] == 38.95
    assert run_numpy_fraud_detection(4500.0, history)["is_anomaly"] is True
