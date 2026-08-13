"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment.
"""
from __future__ import annotations

TITLE = "Designing a REST API with OpenAPI/Swagger Documentation"
DAY = "Day 6 Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 13, 2026"


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))

    # ------------------------------------------------------------ introduction
    h("Introduction")
    p("This assignment asks for a REST API for a book management system, "
      "documented with OpenAPI, with screenshots of each endpoint being "
      "exercised.")
    p("I wrote the OpenAPI document first and then implemented it, rather than "
      "the other way round. That order is the reason the two agree: the "
      "validation rules in the code are the limits written in the schemas, and "
      "the error shape the endpoints return is the one the document advertises. "
      "There is also a set of tests that reads openapi.yaml and checks the real "
      "responses against the schemas in it, so the two cannot quietly drift "
      "apart later.")
    p("The API is Flask, the document is OpenAPI 3.0.3, and the application "
      "serves both the specification at /openapi.yaml and Swagger UI at /docs. "
      "Every screenshot in this report is of that running API.")

    # ----------------------------------------------------------------- step 1
    h("Step 1: The endpoints")
    p("Five endpoints, covering the four CRUD operations:")
    b.append(("table", [
        ["Method and path", "What it does", "Success", "Failures"],
        ["POST /books", "Create a book", "201", "400, 409"],
        ["GET /books", "List every book, optionally filtered by author",
         "200", "\u2014"],
        ["GET /books/{id}", "Retrieve one book", "200", "404"],
        ["PUT /books/{id}", "Update the fields given", "200", "400, 404, 409"],
        ["DELETE /books/{id}", "Delete a book", "204", "404"],
    ], [1.55, 2.75, 0.85, 1.35]))
    p("A few of those choices are worth explaining. POST returns 201 with a "
      "Location header pointing at the new book, so a client does not have to "
      "guess the URL it just created. DELETE returns 204 and no body, because "
      "there is nothing meaningful to send back. PUT changes only the fields "
      "present in the body, which means marking a book as out on loan is "
      "{\"available\": false} rather than a full copy of the record.")
    p("409 is there because a duplicate is not a malformed request. The body is "
      "perfectly valid; it conflicts with something already stored. Returning "
      "400 for it would tell the client to fix its JSON, which is not the "
      "problem.")
    p("Every failure uses the same two-field shape, an error code and a "
      "sentence, so a client only has to learn one error format:")
    b.append(("code", [
        "{",
        '  "error": "not_found",',
        '  "message": "No book with id 99."',
        "}",
    ]))

    # ----------------------------------------------------------------- step 2
    h("Step 2: The OpenAPI document")
    p("openapi.yaml is about 260 lines and describes all five operations, the "
      "query parameter, the request bodies, every response, and four schemas: "
      "Book, NewBook, BookUpdate and Error. The POST operation as it appears in "
      "the file:")
    b.append(("fig", "fig-spec.png",
              "The POST /books operation in openapi.yaml", 5.2))
    p("Three schemas rather than one is a deliberate choice. Book is what comes "
      "back and includes the server-assigned id. NewBook is what a client may "
      "send to create one, and has no id at all, which is how the document says "
      "that ids are not the client's to choose. BookUpdate is every writable "
      "field made optional with minProperties: 1, which is how it says that a "
      "partial update is fine but an empty body is not.")
    p("The repeated responses are written once under components and referenced. "
      "NotFound is defined in one place and pointed at from the three endpoints "
      "that can return it, so the description cannot end up saying three "
      "slightly different things.")
    p("Swagger UI reads that file directly. All five operations and the four "
      "schemas, as served at /docs:")
    b.append(("fig", "fig-swagger-overview.png",
              "Swagger UI rendering openapi.yaml at /docs", 5.0))
    p("Expanding POST /books shows what the document gives a reader: the "
      "required fields, the limits on each one, an example body, and all three "
      "responses it can produce with an example of each.")
    b.append(("fig", "fig-swagger-post.png",
              "POST /books expanded, showing the request body and every "
              "documented response", 4.8))
    p("The schemas at the bottom of the page are the same definitions the "
      "endpoints reference:")
    b.append(("fig", "fig-swagger-schemas.png",
              "The Book schema, with the constraints the API enforces", 6.0))

    # ----------------------------------------------------------------- step 3
    h("Step 3: Testing each endpoint")
    p("Each endpoint below was called with curl against the running server. The "
      "-i flag prints the status line and headers as well as the body. The only "
      "thing changed in these screenshots is that the JSON body is indented; "
      "Flask sends it on one line, which runs off the edge of the page.")
    p("Creating a book. Note the 201 and the Location header:")
    b.append(("fig", "fig-curl-post.png", "POST /books", 6.2))
    p("Listing everything. The two seeded books plus the one just created:")
    b.append(("fig", "fig-curl-get-all.png", "GET /books", 5.4))
    p("The documented query parameter, matching on part of the author's name, "
      "case-insensitively:")
    b.append(("fig", "fig-curl-get-filtered.png",
              "GET /books?author=orwell", 6.0))
    p("Retrieving the new book by its id:")
    b.append(("fig", "fig-curl-get-one.png", "GET /books/3", 6.2))
    p("Updating one field. Only available was sent, and the title, author and "
      "year are unchanged in the response:")
    b.append(("fig", "fig-curl-put.png", "PUT /books/3", 6.2))
    p("Deleting it. The 204 carries no body, and no Content-Type either, since "
      "there is no content to describe. Reading the same id afterwards gives "
      "the 404:")
    b.append(("fig", "fig-curl-delete.png",
              "DELETE /books/3, then GET /books/3", 6.2))
    p("Swagger UI can also call the API itself. This is Try it out on "
      "GET /books/{id}, executed against the running server, showing the "
      "request it sent and the response and headers that came back:")
    b.append(("fig", "fig-swagger-tryit.png",
              "Try it out on GET /books/{id}, run against the live API", 5.0))

    # --------------------------------------------------------------- errors
    h("The error responses")
    p("The three failure cases, all returning the shape the document "
      "describes: a body with no title, a book that is already on the list, and "
      "an id that does not exist.")
    b.append(("fig", "fig-curl-errors.png",
              "400, 409 and 404, all using the Error schema", 5.2))
    p("The 400 names the field that was wrong rather than saying the request "
      "was invalid, which is the difference between a client developer fixing "
      "it in a minute and reading the spec line by line to work out which field "
      "the server disliked.")

    # -------------------------------------------------- spec vs implementation
    h("Keeping the document and the code in agreement")
    p("A specification that describes what the API was intended to do is worth "
      "very little. The part of this assignment I spent most time on was making "
      "the document checkable.")
    p("There are 48 tests. 34 cover behaviour. The other 14 load openapi.yaml "
      "and compare it against the running application:")
    b.append(("fig", "fig-tests.png", "The test run", 6.2))
    p("Those 14 do four kinds of check. They confirm the document declares "
      "exactly the five operations and no more, and that each has a summary and "
      "an operationId. They walk Flask's own routing table and assert that "
      "every path the application serves under /books is one the document "
      "declares, so a route added in code and forgotten in the spec fails the "
      "build. They validate real responses against the response schemas with "
      "jsonschema, including a book with no year, since year is documented as "
      "nullable. And they check that every error response matches the Error "
      "schema and that the code is one of the three values in its enum.")
    p("Getting the schema validation working took one real piece of work. "
      "OpenAPI's nullable is not a JSON Schema keyword, so jsonschema ignores "
      "it, and a book with year: null failed against type: integer even though "
      "the document says null is allowed. The test helper resolves the $refs "
      "and rewrites a nullable field's type into [type, \"null\"] before "
      "validating. Without that the tests would have quietly disagreed with the "
      "document they were meant to be enforcing.")

    # ------------------------------------------------------------- reflection
    h("What I would do differently")
    p("Writing the document first was the right call, and not because of the "
      "document. Deciding on paper that POST returns 201 with a Location "
      "header, that DELETE returns 204 with no body, and that a duplicate is a "
      "409 rather than a 400, meant those questions were settled before any "
      "endpoint was written. When I have started from the code instead, the "
      "status codes end up being whatever the first implementation happened to "
      "return.")
    p("Two things I would change. The store is in memory, so the list resets "
      "when the server restarts; that was a deliberate trade to keep the "
      "endpoint code short, but it is the first thing I would replace. And PUT "
      "here updates only the fields it is given, which is really PATCH "
      "behaviour. The assignment specifies PUT, so PUT is what I documented and "
      "implemented, and the description says plainly that it replaces only the "
      "fields given, but on a real API I would either make PUT a full "
      "replacement or move this behaviour to PATCH.")

    return b
