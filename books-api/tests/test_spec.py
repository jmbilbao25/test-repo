"""Checks the implementation against openapi.yaml.

These are the tests that make the document worth something. Without them the
spec is a description of what the API was meant to do, and nothing stops the two
drifting apart.
"""
from __future__ import annotations

from jsonschema import validate

EXPECTED = {
    "/books": {"get", "post"},
    "/books/{id}": {"get", "put", "delete"},
}


# ------------------------------------------------------------ the spec itself
def test_spec_declares_the_five_endpoints(spec):
    assert set(spec["paths"]) == set(EXPECTED)
    for path, methods in EXPECTED.items():
        documented = {k for k in spec["paths"][path]
                      if k in {"get", "post", "put", "delete", "patch"}}
        assert documented == methods, path


def test_every_operation_has_a_summary_and_an_operation_id(spec):
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method == "parameters":
                continue
            assert operation.get("summary"), f"{method} {path}"
            assert operation.get("operationId"), f"{method} {path}"


def test_every_documented_response_has_a_description(spec):
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method == "parameters":
                continue
            for status, response in operation["responses"].items():
                if "$ref" in response:
                    continue
                assert response.get("description"), f"{method} {path} {status}"


def test_the_routes_the_app_serves_are_the_routes_the_spec_declares(client, spec):
    """Anything reachable under /books must appear in the document."""
    served = set()
    for rule in client.application.url_map.iter_rules():
        if not rule.rule.startswith("/books"):
            continue
        # Flask writes <int:book_id>, the spec writes {id}.
        path = rule.rule.replace("<int:book_id>", "{id}")
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            served.add((path, method.lower()))

    documented = {(path, method)
                  for path, methods in EXPECTED.items() for method in methods}
    assert served == documented


# ------------------------------------------- responses against their schemas
def test_list_response_matches_the_schema(client, schema_for):
    body = client.get("/books").get_json()
    validate(body, schema_for("/books", "get", 200))


def test_create_response_matches_the_schema(client, schema_for):
    body = client.post("/books", json={"title": "The Hobbit",
                                       "author": "Tolkien",
                                       "year": 1937}).get_json()
    validate(body, schema_for("/books", "post", 201))


def test_a_book_with_no_year_still_matches_the_schema(client, schema_for):
    """year is documented as nullable, so null has to be acceptable."""
    body = client.post("/books", json={"title": "Untitled",
                                       "author": "Anon"}).get_json()
    assert body["year"] is None
    validate(body, schema_for("/books", "post", 201))


def test_get_one_response_matches_the_schema(client, schema_for):
    validate(client.get("/books/1").get_json(),
             schema_for("/books/{id}", "get", 200))


def test_update_response_matches_the_schema(client, schema_for):
    validate(client.put("/books/1", json={"available": False}).get_json(),
             schema_for("/books/{id}", "put", 200))


def test_delete_is_documented_as_having_no_body(client, schema_for):
    assert schema_for("/books/{id}", "delete", 204) is None
    assert client.delete("/books/1").get_data() == b""


# --------------------------------------------- errors against the Error schema
def test_every_error_response_matches_the_error_schema(client, schema_for):
    cases = [
        (client.get("/books/99"), "/books/{id}", "get", 404),
        (client.post("/books", json={"author": "no title"}),
         "/books", "post", 400),
        (client.put("/books/99", json={"available": False}),
         "/books/{id}", "put", 404),
        (client.put("/books/1", json={}), "/books/{id}", "put", 400),
        (client.delete("/books/99"), "/books/{id}", "delete", 404),
    ]
    for response, path, method, status in cases:
        assert response.status_code == status, f"{method} {path}"
        validate(response.get_json(), schema_for(path, method, status))


def test_error_codes_are_from_the_documented_enum(client, spec):
    allowed = spec["components"]["schemas"]["Error"]["properties"]["error"]["enum"]
    responses = [
        client.get("/books/99"),
        client.post("/books", json={}),
        client.post("/books", json={"title": "Nineteen Eighty-Four",
                                    "author": "George Orwell"}),
    ]
    for response in responses:
        assert response.get_json()["error"] in allowed


# ------------------------------------------------------------ served documents
def test_the_spec_is_served(client):
    response = client.get("/openapi.yaml")
    assert response.status_code == 200
    assert b"openapi: 3.0.3" in response.get_data()


def test_swagger_ui_is_served_and_points_at_the_spec(client):
    body = client.get("/docs").get_data(as_text=True)
    assert "swagger-ui" in body
    assert "/openapi.yaml" in body
