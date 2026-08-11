"""Tests that go through the Flask routes."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from todo_app.app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "tasks.json"))
    app.config.update(TESTING=True, SECRET_KEY="test-key")
    return app.test_client()


def test_empty_list_shows_the_placeholder(client):
    body = client.get("/").get_data(as_text=True)
    assert "Your list is empty" in body


def test_adding_a_task_shows_it_on_the_page(client):
    client.post("/add", data={"title": "Buy milk"}, follow_redirects=True)
    body = client.get("/").get_data(as_text=True)
    assert "Buy milk" in body
    assert "1 active" in body


def test_rejected_task_reports_the_reason(client):
    body = client.post("/add", data={"title": "   "},
                       follow_redirects=True).get_data(as_text=True)
    assert "cannot be empty" in body


def test_duplicate_reports_the_reason(client):
    client.post("/add", data={"title": "Buy milk"}, follow_redirects=True)
    body = client.post("/add", data={"title": "buy milk"},
                       follow_redirects=True).get_data(as_text=True)
    assert "already on the list" in body


def test_toggle_and_filters(client):
    client.post("/add", data={"title": "one"}, follow_redirects=True)
    client.post("/add", data={"title": "two"}, follow_redirects=True)
    client.post("/toggle/1", follow_redirects=True)

    done = client.get("/?view=done").get_data(as_text=True)
    assert "one" in done and "two" not in done

    active = client.get("/?view=active").get_data(as_text=True)
    assert "two" in active and ">one<" not in active


def test_clear_completed(client):
    client.post("/add", data={"title": "one"}, follow_redirects=True)
    client.post("/toggle/1", follow_redirects=True)
    body = client.post("/clear-completed",
                       follow_redirects=True).get_data(as_text=True)
    assert "Your list is empty" in body


def test_a_title_with_html_in_it_is_escaped(client):
    """The template must not render a task title as markup."""
    client.post("/add", data={"title": "<script>alert('xss')</script>"},
                follow_redirects=True)
    body = client.get("/").get_data(as_text=True)
    assert "<script>alert" not in body
    assert "&lt;script&gt;" in body


def test_unknown_view_falls_back_to_all(client):
    client.post("/add", data={"title": "one"}, follow_redirects=True)
    assert "one" in client.get("/?view=nonsense").get_data(as_text=True)
