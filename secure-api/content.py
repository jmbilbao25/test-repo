"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment.
"""
from __future__ import annotations

TITLE = "Securing and Documenting a REST API with OAuth2, JWT and Rate Limiting"
DAY = "Day 7 Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 18, 2026"


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    fig = lambda name, caption, width: b.append(("fig", name, caption, width))
    code = lambda lines: b.append(("code", lines))

    # ------------------------------------------------------------ introduction
    h("Introduction")
    p("This assignment asks for an API secured with OAuth2 and JWT, protected "
      "with rate limiting, documented with Swagger and Postman, and put to use "
      "by a practical client.")
    p("What I built is an expense reports API. The reports themselves are "
      "incidental; they exist so there is something worth protecting. Three "
      "accounts have different permissions, which is what makes it possible to "
      "show the difference between a caller the API does not recognise, one it "
      "recognises but will not let through, and one it lets through.")
    p("The API is FastAPI. I chose it over Flask for this particular assignment "
      "because its OAuth2PasswordBearer is a real implementation of the "
      "password grant rather than a bearer-token helper: it produces the "
      "Authorize dialog in Swagger UI with the scopes as checkboxes, and that "
      "dialog performs an actual token exchange. Every screenshot of a refusal "
      "in this document is a response the running API sent.")
    p("Everything is run from PowerShell on Windows.")

    # ----------------------------------------------------------------- step 1
    h("Step 1: The API")
    p("Nine endpoints. Only /health is open; everything else needs a token, and "
      "the reports endpoints each need a specific scope.")
    b.append(("table", [
        ["Endpoint", "Purpose", "Scope required"],
        ["POST /auth/token", "Exchange username and password for tokens",
         "\u2014 open"],
        ["POST /auth/refresh", "Trade a refresh token for a new access token",
         "a refresh token"],
        ["GET /auth/me", "Who the presented token belongs to", "any token"],
        ["GET /reports", "List reports", "reports:read"],
        ["GET /reports/{id}", "One report", "reports:read"],
        ["GET /reports/summary", "Totals by category", "reports:read"],
        ["POST /reports", "Create a report", "reports:write"],
        ["DELETE /reports/{id}", "Delete a report", "reports:delete"],
        ["GET /health", "Service status", "\u2014 open"],
    ], [1.75, 3.0, 1.55]))
    p("The three accounts, and what each may be granted:")
    b.append(("table", [
        ["Account", "Password", "Scopes it may hold"],
        ["analyst", "analyst-password", "reports:read"],
        ["manager", "manager-password", "reports:read, reports:write"],
        ["admin", "admin-password",
         "reports:read, reports:write, reports:delete"],
    ], [1.15, 1.95, 3.2]))
    p("There is also a disabled account, so the difference between credentials "
      "being wrong and an account being turned off can be shown.")
    p("Setting up is four packages, plus Newman for running the Postman "
      "collection from the command line:")
    fig("fig-env.png", "The environment and the versions in it", 5.4)
    p("The FastAPI command line tool runs it, and reports where the "
      "documentation is:")
    fig("fig-devserver.png", "fastapi dev starting the server", 4.4)
    p("The open endpoint answers without any credentials, and says which "
      "scopes exist:")
    fig("fig-curl-health.png", "GET /health, no token needed", 5.0)

    # ----------------------------------------------------------------- step 2
    h("Step 2: OAuth2 and JWT")
    p("OAuth2 is a framework of several flows rather than one protocol. The one "
      "used here is the password grant, which is the flow for a client the API "
      "owner controls: the client collects the username and password, posts "
      "them once to the token endpoint, and from then on holds a token instead. "
      "The credentials are not stored by the client and not sent again.")
    p("The token endpoint takes form fields rather than JSON, which is what "
      "OAuth2 specifies. It returns two tokens:")
    fig("fig-curl-token.png",
        "POST /auth/token. The tokens are shortened in this screenshot; a real "
        "one is about 300 characters.", 5.6)
    p("Two tokens rather than one is the part worth explaining. The access token "
      "expires in 15 minutes, which limits the damage if it leaks, but nobody "
      "wants to retype a password every 15 minutes. The refresh token lasts 24 "
      "hours and can be exchanged for a new access token. It carries no scopes "
      "at all, so it cannot be used to reach a protected endpoint even though "
      "it is a perfectly valid JWT.")

    h("What is actually inside a JWT")
    p("A JWT is three base64 sections joined by dots. It is worth being precise "
      "about what that means: the first two are encoded, not encrypted. Anyone "
      "holding the token can read them.")
    fig("fig-token-anatomy.png",
        "A real token taken apart. The payload is readable by anyone who has "
        "the token.", 5.6)
    p("So the security does not come from hiding the claims. It comes from the "
      "third section, the signature. The API signs the header and payload with "
      "a secret using HS256; anyone can verify the token is intact, but only "
      "the holder of the secret can produce a signature for claims they have "
      "changed. That is why nothing secret is ever put in a payload.")
    p("The claims are what the API relies on. sub is the account, scopes is "
      "what the token may do, exp is when it stops working, iat is when it was "
      "issued, iss and aud say who issued it and who it was issued for, and jti "
      "is a unique id for this token. This is the function that assembles them:")
    fig("fig-code-jwt.png", "Building the payload and signing it", 5.9)
    p("Verifying is where the care goes. Every claim that was written has to be "
      "checked, and each failure has to produce a message that helps a "
      "legitimate client without helping an attacker:")
    fig("fig-code-decode.png",
        "Verifying a token. The type check is what stops a refresh token being "
        "used as an access token.", 5.9)
    p("Passwords are never stored, only bcrypt hashes. bcrypt is deliberately "
      "slow and salts each hash, so two accounts with the same password get "
      "different hashes and a stolen list cannot be reversed with a lookup "
      "table:")
    fig("fig-hashing.png",
        "What is stored for the manager account: algorithm 2b, cost factor 12, "
        "60 characters", 5.2)

    h("Authentication is not authorisation")
    p("This is the distinction the scopes exist to enforce, and the one the "
      "status codes have to reflect. A 401 means the API does not know who you "
      "are. A 403 means it knows exactly who you are and is refusing anyway. "
      "Returning 401 for both would tell a client to sign in again when signing "
      "in again would not help.")
    p("FastAPI's SecurityScopes makes the requirement part of the endpoint "
      "declaration, so the rule lives where the endpoint is defined:")
    fig("fig-code-endpoint.png",
        "The scope required is declared on the endpoint itself", 6.2)
    p("And the dependency that enforces it:")
    fig("fig-code-scopes.png",
        "Refusing a request whose token lacks a scope, with the scope named in "
        "the response", 5.9)
    p("A token also carries only what was asked for. The admin account may hold "
      "all three scopes, but a client can request fewer, and then the token can "
      "do less. A client that only reads should ask only to read:")
    fig("fig-curl-narrow-scope.png",
        "The admin account signing in with reports:read only", 5.6)
    p("Reading back what a token represents:")
    fig("fig-curl-me.png", "GET /auth/me", 5.8)
    p("Listing the protected data:")
    fig("fig-curl-reports.png",
        "GET /reports with a valid token. The list is shortened here.", 5.4)
    p("The aggregate endpoint:")
    fig("fig-curl-summary.png", "GET /reports/summary", 5.8)
    p("A write, which needs a second scope:")
    fig("fig-curl-create.png", "POST /reports as manager", 5.2)
    p("And a delete, which only admin can do:")
    fig("fig-curl-delete.png", "DELETE /reports/2 as admin", 5.2)

    h("Every way a request gets turned away")
    p("This is the part I spent most of the time on, because an API is only as "
      "good as its refusals. No token at all:")
    fig("fig-curl-no-token.png", "401 with a WWW-Authenticate header", 5.0)
    p("A token with one character of its signature changed. The claims are "
      "still perfectly readable, and it still does not work, which is the whole "
      "point of signing:")
    fig("fig-curl-tampered.png", "401, the signature does not match", 5.8)
    p("A token that has expired:")
    fig("fig-curl-expired.png", "401, expired", 5.8)
    p("A refresh token presented where an access token belongs. Both are valid "
      "JWTs signed by this API; the type claim is what separates them:")
    fig("fig-curl-refresh-misuse.png",
        "401, the wrong kind of token", 5.8)
    p("A valid token whose scopes do not stretch far enough. Note the 403 and "
      "that the message names both the scope needed and the scopes held:")
    fig("fig-curl-forbidden.png",
        "403 for the analyst account attempting a write", 5.6)
    p("The same for a manager attempting a delete, which shows that write is "
      "not a superset of delete:")
    fig("fig-curl-forbidden-delete.png",
        "403, reports:write is not reports:delete", 5.9)
    p("A wrong password. The message is deliberately the same one an unknown "
      "username produces, because a different message would let someone work "
      "out which accounts exist:")
    fig("fig-curl-bad-password.png", "401, wrong password", 5.4)
    p("And asking for a scope the account may not hold, which is refused rather "
      "than quietly granted in a reduced form:")
    fig("fig-curl-bad-scope.png", "400, scope refused", 5.6)

    # ----------------------------------------------------------------- step 3
    h("Step 3: Rate limiting")
    p("Rate limiting is here because authentication alone does not stop abuse. "
      "Nothing in the token logic prevents someone posting thousands of "
      "password guesses to the token endpoint, and each one would be correctly "
      "rejected while the attacker worked through a word list.")
    p("SlowAPI is the FastAPI equivalent of Flask-Limiter and works the same "
      "way: a limit per endpoint, counted against a key. Four limits are used:")
    b.append(("table", [
        ["Endpoint", "Limit", "Counted against", "Why"],
        ["POST /auth/token", "5 / minute", "the client address",
         "This is where password guessing happens"],
        ["POST, DELETE /reports", "10 / minute", "the token id",
         "Writes cost more than reads"],
        ["GET /reports/summary", "20 / minute", "the token id",
         "Aggregates more work per call"],
        ["Everything else", "60 / minute", "the token id", "A sane default"],
    ], [1.6, 0.95, 1.35, 2.4]))
    p("The key matters as much as the number. Counting reads per address would "
      "mean an office behind one address shares a single allowance, and one busy "
      "client could lock out its colleagues. So an authenticated request is "
      "counted against the token's jti claim instead. Logins have no token yet, "
      "so those are counted per address, which is the right key for the thing "
      "being defended against:")
    fig("fig-code-limits.png",
        "Choosing what to count a request against", 5.9)
    p("Six password guesses in a row. The first five are refused as wrong; the "
      "sixth is refused for being the sixth. The call after that has the "
      "correct password and is still refused, which is what makes this useful:")
    fig("fig-curl-rate-limit.png",
        "429 after five attempts, with the limit and a Retry-After header", 5.6)
    p("The 429 says what the limit was and when to try again, so a legitimate "
      "client that has been too eager can back off correctly instead of "
      "guessing.")

    # ----------------------------------------------------------------- step 4
    h("Step 4: Documentation, with Swagger")
    p("FastAPI generates the OpenAPI document from the type hints and the "
      "response models. Nothing in the pages below was written separately; the "
      "descriptions come from the endpoint decorators and the Pydantic fields.")
    fig("fig-docs-header.png",
        "The description at /docs, including the accounts and the rate limits",
        6.2)
    p("The endpoints, each with a padlock showing it is protected:")
    fig("fig-docs-endpoints.png",
        "All nine endpoints. Only /health has no padlock.", 6.2)
    p("The Authorize button opens the OAuth2 dialog. This is the clearest "
      "evidence that the flow is real OAuth2 rather than a bearer token pasted "
      "into a header: Swagger UI knows the flow is password, knows the token "
      "URL, and lists the scopes as checkboxes because the API declared them.")
    fig("fig-docs-authorize-empty.png",
        "The Authorize dialog, showing the password flow and the token URL",
        5.2)
    p("Filled in as manager, with two of the three scopes ticked:")
    fig("fig-docs-authorize-filled.png",
        "Requesting reports:read and reports:write", 5.2)
    p("Pressing Authorize performs the token exchange against /auth/token. The "
      "dialog then shows the session as authorised:")
    fig("fig-docs-authorized.png",
        "Authorized. Swagger UI now holds a token and sends it with every call.",
        5.2)
    p("The token endpoint as documented:")
    fig("fig-docs-token-endpoint.png",
        "POST /auth/token, with its form fields and every response it can give",
        5.0)
    p("With the session authorised, Try it out sends the token. This response "
      "came back from the running API:")
    fig("fig-docs-tryit-reports.png",
        "GET /reports executed from /docs, with the token attached", 4.6)
    p("The same session attempting a delete. The token carries read and write "
      "but not delete, and the API refuses it. The curl command Swagger UI "
      "shows is the exact request, and the response headers include the scope "
      "that would have been needed:")
    fig("fig-docs-tryit-forbidden.png",
        "A live 403 from /docs: authenticated, not authorised", 4.6)
    p("The generated schemas, including the Error shape every failure uses:")
    fig("fig-docs-schemas.png", "The generated schemas", 5.6)
    p("The same document also renders as ReDoc:")
    fig("fig-redoc.png", "The API at /redoc", 4.4)

    h("Step 4, continued: the Postman collection")
    p("The collection is at postman/secure-api.postman_collection.json, in "
      "Postman's v2.1 format, with 16 requests in three folders: Auth, Reports "
      "and Rejected.")
    p("The piece that makes it pleasant to use is the test script on the sign-in "
      "request. It saves both tokens into collection variables, and the "
      "collection's own auth is set to send the access token as a bearer, so "
      "every request after sign-in is authorised without anything being pasted "
      "anywhere. It also decodes the payload and checks the claims:")
    fig("fig-postman-script.png",
        "The test script on the Sign in request", 6.0)
    p("Every request carries assertions, which means the collection is not only "
      "documentation but a check on the API. The Rejected folder asserts the "
      "refusals: that no token gives 401, that a tampered token names the "
      "signature, that a missing scope gives 403 and not 401, and that a wrong "
      "password gives a message which does not reveal whether the account "
      "exists.")
    p("Newman is Postman's command line runner and reads the same file, so the "
      "collection can be run without the app:")
    fig("fig-newman-head.png",
        "newman run, showing the Auth folder and its assertions", 5.4)
    p("The totals for the whole run:")
    fig("fig-newman-summary.png",
        "16 requests, 41 assertions, nothing failed", 5.4)
    p("One assertion did fail the first time I ran this, and it was my own "
      "mistake rather than the API's: the collection saved the new report's id "
      "as a number and then compared it against a string. Worth mentioning "
      "because it is exactly the sort of thing that makes a collection worse "
      "than nothing if it is written and never executed.")

    # ----------------------------------------------------------------- step 5
    h("Step 5: The practical use case")
    p("The client is a single page served by the API itself at /app. It signs "
      "in, holds the token, and calls the same endpoints as everything above. "
      "It is the practical use case the assignment asks for, and it is also "
      "where the security decisions become visible to a person.")
    fig("fig-app-login.png",
        "The sign-in screen. This posts to /auth/token, the same endpoint curl "
        "used.", 5.4)
    p("Signed in as manager. The scopes the token carries are shown next to the "
      "account name, the totals come from /reports/summary and the table from "
      "/reports, each with the token attached:")
    fig("fig-app-manager.png", "The client, signed in as manager", 5.8)
    p("Adding a report, which needs reports:write:")
    fig("fig-app-created.png", "A report created through the client", 5.8)
    p("The delete buttons are disabled, because this token does not carry "
      "reports:delete. That is a courtesy to the user, not a security measure, "
      "and the distinction matters. To show why, I enabled a delete button in "
      "the browser and pressed it, which is exactly what a modified client "
      "would do. The API refused it:")
    fig("fig-app-forbidden.png",
        "The API refusing a delete after the disabled button was re-enabled in "
        "the browser. The message is the API's own.", 5.8)
    p("Signed in as analyst instead, the add form is not rendered at all, "
      "because that token cannot write:")
    fig("fig-app-analyst.png",
        "The same client with a read-only token", 5.8)
    p("And the login rate limit as a user meets it, after six wrong passwords:")
    fig("fig-app-rate-limited.png",
        "The 429 surfaced in the client, with the limit that was hit", 5.4)
    p("Three things in the client are deliberate. The token is kept in a "
      "variable and not in localStorage, because anything in localStorage can "
      "be read by any script on the page, so one injected script would be "
      "enough to steal it. A 401 sends the user back to the sign-in screen, "
      "since a token that is expired or not trusted cannot be recovered from. "
      "And a 403 shows the API's own message rather than a generic failure, so "
      "the user is told what permission they are missing.")

    # ------------------------------------------------------------------ tests
    h("Tests")
    p("49 tests, in three files: 23 for authentication, 18 for scopes and 8 for "
      "the rate limits.")
    fig("fig-tests.png", "The test run, and the rate limit tests by name", 5.6)
    p("The ones I would keep if I could keep only a few are the attacks. One "
      "edits the scopes inside a token's payload to add reports:delete and "
      "confirms the request is still refused, which is the test that proves the "
      "signature is doing its job. One signs a well-formed token with a "
      "different secret. One presents a refresh token as an access token. One "
      "checks that a wrong password and an unknown username produce byte for "
      "byte the same response.")
    p("The rate limit tests needed a fixture I did not expect to write. The "
      "limiter counts across requests, which is the point of it, so one test's "
      "traffic was spending the next test's allowance and unrelated tests were "
      "failing with 429s. It is switched off by default and turned on only for "
      "the tests that are about limiting.")
    p("The same problem bit the screenshot script. Its own setup was signing in "
      "often enough to trip the five-per-minute login limit, so it started "
      "collecting 429s it had not asked for. It now restarts the server between "
      "groups of captures, since the counters live in the process.")

    # ------------------------------------------------------------- reflection
    h("What I would change")
    p("The tokens cannot be revoked. Every token carries a jti precisely so "
      "that a specific one could be blacklisted, but nothing reads it yet, so a "
      "leaked access token stays usable for its full 15 minutes and a refresh "
      "token for a day. A store of revoked ids checked on each request is the "
      "first thing I would add.")
    p("The secret has a fallback default so the project runs after a clone, "
      "which is convenient and wrong. It should refuse to start without "
      "SECRET_KEY set in the environment. The accounts are in a module for the "
      "same reason and would be a database.")
    p("The rate limit counters are in memory, so they are per process. Two "
      "workers would give an attacker twice the allowance, and a restart clears "
      "the count entirely. Flask-Limiter and SlowAPI both support Redis for "
      "this, which is what a deployment would use.")
    p("What I got most out of was the difference between 401 and 403. Before "
      "this I would have treated them as roughly interchangeable. Building the "
      "scope dependency made it concrete: they are answers to two different "
      "questions, and a client can only respond sensibly, by signing in again "
      "or by giving up, if the API is precise about which one it is asking.")

    return b
