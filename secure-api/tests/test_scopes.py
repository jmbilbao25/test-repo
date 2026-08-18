"""Authorisation: having a valid token is not the same as being allowed."""
from __future__ import annotations

NEW = {"title": "Team lunch, BGC", "category": "meals", "amount": 2400.0}


def test_read_works_for_every_account(client, analyst, manager, admin):
    for header in (analyst, manager, admin):
        assert client.get("/reports", headers=header).status_code == 200


def test_the_list_is_the_seeded_reports(client, analyst):
    body = client.get("/reports", headers=analyst).json()
    assert body["count"] == 6
    assert body["total_amount"] == 40849.0


def test_filtering_by_category(client, analyst):
    body = client.get("/reports?category=travel", headers=analyst).json()
    assert body["count"] == 2
    assert {r["category"] for r in body["reports"]} == {"travel"}


def test_one_report_by_id(client, analyst):
    body = client.get("/reports/1", headers=analyst).json()
    assert body["id"] == 1
    assert body["title"] == "Client visit, Cebu"


def test_a_missing_report_is_404_not_403(client, analyst):
    """Authorisation is checked first, so an authorised caller gets the 404."""
    response = client.get("/reports/999", headers=analyst)
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_summary_totals(client, analyst):
    body = client.get("/reports/summary", headers=analyst).json()
    assert body["report_count"] == 6
    assert body["total_amount"] == 40849.0
    assert body["by_category"]["travel"] == 13300.0
    assert body["largest"]["title"] == "Conference ticket"


# ------------------------------------------------------------------- writing
def test_analyst_cannot_write(client, analyst):
    """A valid token, but not one that carries reports:write."""
    response = client.post("/reports", headers=analyst, json=NEW)
    assert response.status_code == 403
    assert response.json()["error"] == "insufficient_scope"
    assert "reports:write" in response.json()["message"]


def test_the_403_says_what_the_token_does_carry(client, analyst):
    message = client.post("/reports", headers=analyst, json=NEW).json()["message"]
    assert "reports:read" in message


def test_the_403_carries_the_required_scope_in_the_header(client, analyst):
    response = client.post("/reports", headers=analyst, json=NEW)
    assert "insufficient_scope" in response.headers.get("WWW-Authenticate", "")


def test_manager_can_write(client, manager):
    response = client.post("/reports", headers=manager, json=NEW)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 7
    assert body["submitted_by"] == "manager"
    assert body["status"] == "pending"


def test_a_created_report_is_then_listed(client, manager):
    client.post("/reports", headers=manager, json=NEW)
    assert client.get("/reports", headers=manager).json()["count"] == 7


def test_a_write_scope_is_not_a_delete_scope(client, manager):
    response = client.delete("/reports/1", headers=manager)
    assert response.status_code == 403
    assert "reports:delete" in response.json()["message"]


def test_admin_can_delete(client, admin):
    assert client.delete("/reports/1", headers=admin).status_code == 204
    assert client.get("/reports", headers=admin).json()["count"] == 5


def test_deleting_twice_is_404(client, admin):
    client.delete("/reports/1", headers=admin)
    assert client.delete("/reports/1", headers=admin).status_code == 404


def test_a_narrowed_token_loses_the_permission(client):
    """The account may write, but this token was not granted the scope."""
    from tests.conftest import auth_header
    header = auth_header(client, "admin", scope="reports:read")
    assert client.get("/reports", headers=header).status_code == 200
    assert client.post("/reports", headers=header, json=NEW).status_code == 403


def test_writes_are_validated(client, manager):
    for bad in [{"title": "", "category": "meals", "amount": 10.0},
                {"title": "x", "category": "meals", "amount": -5.0},
                {"title": "x", "category": "meals", "amount": 0},
                {"title": "x", "category": "meals"}]:
        assert client.post("/reports", headers=manager,
                           json=bad).status_code == 422


def test_health_needs_no_token(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["scopes_available"] == ["reports:delete", "reports:read",
                                        "reports:write"]


def test_every_reports_endpoint_refuses_an_anonymous_caller(client):
    assert client.get("/reports").status_code == 401
    assert client.get("/reports/1").status_code == 401
    assert client.get("/reports/summary").status_code == 401
    assert client.post("/reports", json=NEW).status_code == 401
    assert client.delete("/reports/1").status_code == 401
