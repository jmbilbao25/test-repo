"""The Book Management API.

Five endpoints, matching openapi.yaml:

    POST   /books        create
    GET    /books        list, optionally filtered by author
    GET    /books/{id}   read one
    PUT    /books/{id}   update
    DELETE /books/{id}   delete

The spec is served at /openapi.yaml and Swagger UI at /docs.
"""
from __future__ import annotations

import os

from flask import Flask, Response, jsonify, request, send_from_directory

from .store import BookStore
from .validation import ValidationError, clean_new_book, clean_update

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SWAGGER_UI = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Book Management API</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css">
  <style>body{margin:0}.topbar{display:none}</style>
</head>
<body>
  <div id="swagger"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      url: "/openapi.yaml",
      dom_id: "#swagger",
      deepLinking: true,
      defaultModelsExpandDepth: 1,
      tryItOutEnabled: true
    });
  </script>
</body>
</html>
"""


def error(code: str, message: str, status: int):
    """Every failure uses the Error schema from the spec."""
    return jsonify({"error": code, "message": message}), status


def create_app(seed: bool = True) -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    store = BookStore(seed=seed)
    app.config["STORE"] = store

    # ------------------------------------------------------------- the spec
    @app.get("/openapi.yaml")
    def spec():
        return send_from_directory(ROOT, "openapi.yaml",
                                   mimetype="application/yaml")

    @app.get("/docs")
    def docs():
        return SWAGGER_UI

    # ------------------------------------------------------------ endpoints
    @app.get("/books")
    def list_books():
        books = store.search(author=request.args.get("author"))
        return jsonify({"books": books, "count": len(books)}), 200

    @app.post("/books")
    def create_book():
        try:
            data = clean_new_book(request.get_json(silent=True))
        except ValidationError as exc:
            return error("validation_error", str(exc), 400)

        clash = store.find_duplicate(data["title"], data["author"])
        if clash:
            return error(
                "conflict",
                f"'{clash['title']}' by {clash['author']} is already on the "
                "list.",
                409,
            )

        book = store.add(data)
        return jsonify(book), 201, {"Location": f"/books/{book['id']}"}

    @app.get("/books/<int:book_id>")
    def get_book(book_id: int):
        book = store.get(book_id)
        if book is None:
            return error("not_found", f"No book with id {book_id}.", 404)
        return jsonify(book), 200

    @app.put("/books/<int:book_id>")
    def update_book(book_id: int):
        book = store.get(book_id)
        if book is None:
            return error("not_found", f"No book with id {book_id}.", 404)

        try:
            changes = clean_update(request.get_json(silent=True))
        except ValidationError as exc:
            return error("validation_error", str(exc), 400)

        clash = store.find_duplicate(
            changes.get("title", book["title"]),
            changes.get("author", book["author"]),
            ignore_id=book_id,
        )
        if clash:
            return error(
                "conflict",
                f"'{clash['title']}' by {clash['author']} is already on the "
                "list.",
                409,
            )

        book.update(changes)
        return jsonify(book), 200

    @app.delete("/books/<int:book_id>")
    def delete_book(book_id: int):
        if not store.remove(book_id):
            return error("not_found", f"No book with id {book_id}.", 404)
        # A 204 has no body, so it should not carry a Content-Type describing
        # one. Werkzeug sets text/html by default, so it is removed here.
        response = Response(status=204)
        response.headers.pop("Content-Type", None)
        return response

    # --------------------------------------------------------------- errors
    @app.errorhandler(404)
    def handle_404(_exc):
        return error("not_found", "No such endpoint.", 404)

    @app.errorhandler(405)
    def handle_405(_exc):
        return error("not_found",
                     f"{request.method} is not allowed on this path.", 405)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5000)
