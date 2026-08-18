# Secure Expense Reports API

Day 7 assignment. The write-up is **[API-Security-OAuth2-JWT-Assignment.docx](../API-Security-OAuth2-JWT-Assignment.docx)**,
with a **[PDF copy](../API-Security-OAuth2-JWT-Assignment.pdf)** — 37 pages, 46 screenshots.

A FastAPI service secured with the **OAuth2 password flow**, **JWT** bearer
tokens and **rate limiting**, documented with Swagger and a Postman collection,
and used by a small web client at `/app`.

## Endpoints

| Endpoint | Purpose | Scope required |
| --- | --- | --- |
| `POST /auth/token` | Username and password for tokens | — open |
| `POST /auth/refresh` | Refresh token for a new access token | a refresh token |
| `GET /auth/me` | Who the token belongs to | any token |
| `GET /reports` | List reports | `reports:read` |
| `GET /reports/{id}` | One report | `reports:read` |
| `GET /reports/summary` | Totals by category | `reports:read` |
| `POST /reports` | Create a report | `reports:write` |
| `DELETE /reports/{id}` | Delete a report | `reports:delete` |
| `GET /health` | Service status | — open |

## Accounts

| Username | Password | Scopes |
| --- | --- | --- |
| `analyst` | `analyst-password` | `reports:read` |
| `manager` | `manager-password` | `reports:read`, `reports:write` |
| `admin` | `admin-password` | all three |
| `retired` | `retired-password` | disabled, to show 403 on a valid password |

A client may request **fewer** scopes than the account holds, and the token can
then do less.

## Running it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev secure_api\main.py
```

- Swagger UI: http://127.0.0.1:8000/docs — press **Authorize** to sign in
- ReDoc: http://127.0.0.1:8000/redoc
- The web client: http://127.0.0.1:8000/app/

```powershell
# get a token
curl.exe -i -X POST http://127.0.0.1:8000/auth/token `
    -H "Content-Type: application/x-www-form-urlencoded" `
    -d "username=manager&password=manager-password"

# use it
curl.exe -i http://127.0.0.1:8000/reports -H "Authorization: Bearer <token>"
```

## How the security works

**OAuth2 password grant.** `POST /auth/token` takes form fields and returns a
15-minute access token plus a 24-hour refresh token. The refresh token carries
**no scopes**, so it cannot reach a protected endpoint even though it is a valid
JWT signed by this API — the `type` claim keeps the two apart.

**JWT.** HS256, with `sub`, `scopes`, `iat`, `exp`, `iss`, `aud` and a unique
`jti`. The header and payload are base64, *not* encrypted: anyone holding a token
can read them, so nothing secret goes in a payload. The signature is what makes
the claims trustworthy. Verification checks the signature, expiry, issuer,
audience and token type.

**Passwords** are bcrypt hashes (cost 12), never stored in plain text. An unknown
username is checked against a dummy hash so it takes the same time to reject as a
wrong password — otherwise the response time would reveal which accounts exist.

**Scopes.** 401 means "I don't know who you are"; 403 means "I know exactly who
you are and I'm refusing". The required scope is declared on the endpoint via
FastAPI's `Security(..., scopes=[...])`, and the 403 names both the scope needed
and the scopes held.

**Rate limits** (SlowAPI, the FastAPI equivalent of Flask-Limiter):

| Endpoint | Limit | Counted against |
| --- | --- | --- |
| `POST /auth/token` | 5 / minute | client address |
| writes to `/reports` | 10 / minute | token `jti` |
| `/reports/summary` | 20 / minute | token `jti` |
| everything else | 60 / minute | token `jti` |

Reads are counted per **token**, not per address, so an office behind one address
does not share a single allowance. Logins have no token yet, so those are counted
per address — the right key for password guessing.

## Tests

```powershell
python -m pytest tests/ -v      # 49 tests
```

23 for authentication, 18 for scopes, 8 for rate limits. The ones worth reading
are the attacks:

- editing `scopes` inside a token payload to add `reports:delete` — still refused,
  which is the test that proves the signature is doing its job
- a well-formed token signed with a different secret
- a refresh token presented as an access token
- a wrong password and an unknown username producing identical responses

The rate limit tests need the limiter switched on deliberately; it is off for the
rest, because the counters persist across requests and one test was otherwise
spending the next test's allowance.

## Postman

`postman/secure-api.postman_collection.json` — 16 requests in three folders
(Auth, Reports, Rejected) with 41 assertions. The sign-in request's test script
saves both tokens into collection variables, so everything after it is authorised
automatically.

```bash
npm install -g newman
python3 scripts/run_newman.py     # starts the server and runs the collection
```

## Rebuilding the write-up

```bash
python3 scripts/capture_env.py      # setup, hashing, token anatomy, dev server, tests
python3 scripts/capture_curl.py     # every endpoint and every refusal
python3 scripts/run_newman.py       # the Postman run
python3 scripts/capture_swagger.py  # /docs, the Authorize dialog, live Try it out
python3 scripts/capture_webapp.py   # the web client
python3 scripts/make_figures.py     # terminal and code figures
python3 build.py                    # writes the .docx and the .pdf
```

Every figure is real. The Authorize dialog screenshots show an actual token
exchange, and the 403 in `/docs` is a response the server sent. The terminal
figures use the Windows Terminal styling and the browser frames use the Windows
window controls, both from `../todo-app/scripts/`.

Two presentation notes, applied by the capture scripts and stated in the report:
JWTs in response bodies are shortened to their first and last characters (a real
one is ~300 characters of base64), long arrays are trimmed, and absolute paths
printed by `fastapi dev` are rewritten to the Windows project path.

`capture_curl.py` restarts the server between groups of captures, because its own
setup logins would otherwise trip the five-per-minute limit and start collecting
429s it did not ask for.

## Known limitations

Deliberate, and discussed in the write-up: tokens cannot be revoked (the `jti` is
there but nothing reads it), `SECRET_KEY` falls back to a development default
instead of refusing to start, accounts live in a module rather than a database,
and the rate limit counters are in memory so they are per process.
