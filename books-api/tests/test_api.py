"""The behaviour of the five endpoints."""
from __future__ import annotations

HOBBIT = {"title": "The Hobbit", "author": "J. R. R. Tolkien", "year": 1937}


# ------------------------------------------------------------------ GET /books
def test_list_returns_the_seeded_books(client):
    body = client.get("/books").get_json()
    assert body["count"] == 2
    assert [b["title"] for b in body["books"]] == [
        "Nineteen Eighty-Four", "Brave New World"]


def test_list_is_empty_when_there_are_no_books(empty_client):
    assert empty_client.get("/books").get_json() == {"books": [], "count": 0}


def test_list_filters_by_author_ignoring_case(client):
    body = client.get("/books?author=orwell").get_json()
    assert body["count"] == 1
    assert body["books"][0]["author"] == "George Orwell"


def test_filter_with_no_matches_returns_an_empty_list(client):
    assert client.get("/books?author=nobody").get_json()["count"] == 0


# ----------------------------------------------------------------- POST /books
def test_create_returns_201_the_book_and_a_location_header(client):
    response = client.post("/books", json=HOBBIT)
    assert response.status_code == 201
    book = response.get_json()
    assert book["id"] == 3
    assert book["title"] == "The Hobbit"
    assert book["available"] is True
    assert response.headers["Location"] == "/books/3"


def test_created_book_is_then_listed(client):
    client.post("/books", json=HOBBIT)
    assert client.get("/books").get_json()["count"] == 3


def test_create_defaults_year_to_null_and_available_to_true(client):
    book = client.post("/books", json={"title": "Untitled",
                                       "author": "Anon"}).get_json()
    assert book["year"] is None
    assert book["available"] is True


def test_create_tidies_whitespace_in_text(client):
    book = client.post("/books", json={"title": "  The   Hobbit ",
                                       "author": " Tolkien "}).get_json()
    assert book["title"] == "The Hobbit"
    assert book["author"] == "Tolkien"


def test_create_rejects_a_missing_title(client):
    response = client.post("/books", json={"author": "Tolkien"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "validation_error"
    assert "'title' is required" in response.get_json()["message"]


def test_create_rejects_an_empty_title(client):
    assert client.post("/books", json={"title": "   ",
                                       "author": "A"}).status_code == 400


def test_create_rejects_a_client_supplied_id(client):
    response = client.post("/books", json={**HOBBIT, "id": 99})
    assert response.status_code == 400
    assert "assigned by the server" in response.get_json()["message"]


def test_create_rejects_an_unknown_field(client):
    response = client.post("/books", json={**HOBBIT, "isbn": "123"})
    assert response.status_code == 400
    assert "'isbn'" in response.get_json()["message"]


def test_create_rejects_a_year_outside_the_documented_range(client):
    for year in (1000, 3000):
        response = client.post("/books", json={**HOBBIT, "year": year})
        assert response.status_code == 400
        assert "between 1450 and 2100" in response.get_json()["message"]


def test_create_rejects_a_year_that_is_not_an_integer(client):
    for year in ("1937", 19.37, True):
        assert client.post("/books",
                           json={**HOBBIT, "year": year}).status_code == 400


def test_create_rejects_a_missing_body(client):
    assert client.post("/books").status_code == 400


def test_create_rejects_a_duplicate_title_and_author(client):
    client.post("/books", json=HOBBIT)
    response = client.post("/books", json=HOBBIT)
    assert response.status_code == 409
    assert response.get_json()["error"] == "conflict"


def test_same_title_by_a_different_author_is_allowed(client):
    client.post("/books", json=HOBBIT)
    assert client.post("/books", json={**HOBBIT,
                                       "author": "Someone Else"}).status_code == 201


# ------------------------------------------------------------ GET /books/{id}
def test_get_one_returns_the_book(client):
    book = client.get("/books/1").get_json()
    assert book["id"] == 1
    assert book["title"] == "Nineteen Eighty-Four"


def test_get_one_returns_404_for_an_unknown_id(client):
    response = client.get("/books/99")
    assert response.status_code == 404
    assert response.get_json() == {"error": "not_found",
                                   "message": "No book with id 99."}


def test_a_non_numeric_id_is_not_a_book_route(client):
    assert client.get("/books/abc").status_code == 404


# ------------------------------------------------------------ PUT /books/{id}
def test_update_changes_only_the_fields_sent(client):
    before = client.get("/books/1").get_json()
    after = client.put("/books/1", json={"available": False}).get_json()
    assert after["available"] is False
    assert after["title"] == before["title"]
    assert after["author"] == before["author"]
    assert after["year"] == before["year"]


def test_update_can_change_several_fields_at_once(client):
    book = client.put("/books/1", json={"title": "1984", "year": 1950}).get_json()
    assert book["title"] == "1984"
    assert book["year"] == 1950


def test_update_persists(client):
    client.put("/books/1", json={"available": False})
    assert client.get("/books/1").get_json()["available"] is False


def test_update_returns_404_for_an_unknown_id(client):
    assert client.put("/books/99", json={"available": False}).status_code == 404


def test_update_rejects_an_empty_body(client):
    response = client.put("/books/1", json={})
    assert response.status_code == 400
    assert "at least one field" in response.get_json()["message"]


def test_update_rejects_changing_the_id(client):
    response = client.put("/books/1", json={"id": 5})
    assert response.status_code == 400
    assert "cannot be changed" in response.get_json()["message"]


def test_update_rejects_a_bad_type(client):
    assert client.put("/books/1", json={"available": "yes"}).status_code == 400


def test_update_into_an_existing_title_and_author_is_a_conflict(client):
    response = client.put("/books/2", json={"title": "Nineteen Eighty-Four",
                                            "author": "George Orwell"})
    assert response.status_code == 409


def test_update_keeping_its_own_title_is_not_a_conflict(client):
    assert client.put("/books/1", json={"title": "Nineteen Eighty-Four",
                                        "available": False}).status_code == 200


# --------------------------------------------------------- DELETE /books/{id}
def test_delete_returns_204_and_no_body(client):
    response = client.delete("/books/1")
    assert response.status_code == 204
    assert response.get_data() == b""
    # No body, so it should not claim to have a content type.
    assert "Content-Type" not in response.headers


def test_deleted_book_is_gone(client):
    client.delete("/books/1")
    assert client.get("/books/1").status_code == 404
    assert client.get("/books").get_json()["count"] == 1


def test_delete_is_404_the_second_time(client):
    client.delete("/books/1")
    assert client.delete("/books/1").status_code == 404


# -------------------------------------------------------------------- general
def test_unknown_endpoint_uses_the_same_error_shape(client):
    body = client.get("/authors").get_json()
    assert set(body) == {"error", "message"}


def test_wrong_method_is_reported(client):
    response = client.delete("/books")
    assert response.status_code == 405
    assert response.get_json()["error"] == "not_found"
