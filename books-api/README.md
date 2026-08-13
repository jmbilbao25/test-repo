# Book Management API

Day 6 assignment. The write-up is **[REST-API-OpenAPI-Assignment.docx](../REST-API-OpenAPI-Assignment.docx)**,
with a **[PDF copy](../REST-API-OpenAPI-Assignment.pdf)**.

A REST API for managing books, specified in [`openapi.yaml`](openapi.yaml) and
implemented in Flask. The spec was written first and the implementation follows
it; 14 of the 48 tests check that the two still agree.

## Endpoints

| Method and path | What it does | Success | Failures |
| --- | --- | --- | --- |
| `POST /books` | Create a book | 201 + `Location` | 400, 409 |
| `GET /books` | List books, `?author=` filters | 200 | — |
| `GET /books/{id}` | Retrieve one book | 200 | 404 |
| `PUT /books/{id}` | Update the fields given | 200 | 400, 404, 409 |
| `DELETE /books/{id}` | Delete a book | 204, no body | 404 |

Every failure returns the same shape:

```json
{ "error": "not_found", "message": "No book with id 99." }
```

`error` is one of `validation_error`, `not_found` or `conflict`.

## Running it

```bash
pip install -r requirements.txt
flask --app books_api.app run
```

- API: http://localhost:5000/books
- Swagger UI: http://localhost:5000/docs
- The spec itself: http://localhost:5000/openapi.yaml

Books are kept in memory, so the list resets when the server restarts. The two
seeded books are there to make the read endpoints useful straight away.

## Tests

```bash
python3 -m pytest tests/ -v      # 48 tests
```

`tests/test_api.py` has 34 tests covering behaviour. `tests/test_spec.py` has 14
that check the implementation against `openapi.yaml`:

- the document declares exactly the five operations, each with a summary and an
  `operationId`, and every response has a description
- every route Flask actually serves under `/books` is one the document declares,
  walked from Flask's own routing table, so a route added in code and forgotten
  in the spec fails the tests
- real responses validate against the documented response schemas with
  `jsonschema`, including a book with no `year`
- every error response matches the `Error` schema, and the code is one of the
  three values in its enum

One wrinkle worth knowing about: OpenAPI's `nullable` is not a JSON Schema
keyword, so `jsonschema` ignores it and `year: null` would fail against
`type: integer`. The helper in `tests/conftest.py` resolves `$ref`s and rewrites a
nullable field's type to `[type, "null"]` before validating.

## Rebuilding the write-up

```bash
python3 scripts/capture_curl.py     # runs every endpoint through curl
python3 scripts/capture_swagger.py  # screenshots Swagger UI, live
python3 scripts/make_figures.py     # terminal and code figures
python3 build.py                    # writes the .docx and the .pdf
```

Every figure is real. `capture_curl.py` starts the server and calls it, and
`capture_swagger.py` drives Swagger UI in a headless browser, including the
Try it out execution. The document writers and the figure renderer are imported
from `../todo-app/` rather than copied.

The one thing not byte-for-byte from `curl`: JSON bodies are re-indented, because
Flask sends them on a single line and a list of books would run off the side of
the page. Status lines, headers and data are untouched.
