"""Calls the API with curl and saves the output, including the refusals.

The server is started here and every request is real. The command shown above
each response is written in PowerShell form with curl.exe, because that is how it
is run on Windows.

JSON bodies are re-indented, and a JWT in a body is shortened to its first and
last few characters, because a full token is 300 characters of base64 that would
push everything else off the page. Both are marked where they happen.

    python3 scripts/capture_curl.py
"""
from __future__ import annotations

import contextlib
import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
PORT = 8000
HOST = f"http://127.0.0.1:{PORT}"
PROMPT = r"PS C:\Users\John\secure-api>"

TOKEN_FIELDS = ("access_token", "refresh_token")
# Long arrays get shortened, or a full report list runs off the page.
TRIM = {"reports": 2}


def start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "secure_api.main:app",
         "--port", str(PORT), "--log-level", "warning"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(150):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                return proc
        except OSError:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("the server did not come up")


# ---------------------------------------------------------------- formatting
def shorten_token(token: str) -> str:
    """Keep the shape of a JWT visible without printing all of it."""
    parts = token.split(".")
    if len(parts) != 3:
        return token[:24] + "..." if len(token) > 24 else token
    head, payload, signature = parts
    return f"{head}.{payload[:16]}...{payload[-8:]}.{signature[:10]}..."


def format_body(output: str) -> str:
    if "\n\n" not in output:
        return output
    head, _, body = output.partition("\n\n")
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return output
    if isinstance(parsed, dict):
        for field in TOKEN_FIELDS:
            if isinstance(parsed.get(field), str):
                parsed[field] = shorten_token(parsed[field])
        for field, keep in TRIM.items():
            rows = parsed.get(field)
            if isinstance(rows, list) and len(rows) > keep:
                hidden = len(rows) - keep
                parsed[field] = rows[:keep] + [
                    f"... {hidden} more not shown"]
    return head + "\n\n" + json.dumps(parsed, indent=2)


WRAP_AT = 88


def quote(value: str) -> str:
    """Quote a value the way PowerShell needs it.

    A single-quoted string in PowerShell is literal, so it is the right wrapper
    for JSON, which is full of double quotes. Double quotes are fine for anything
    that has none of its own.
    """
    if "'" in value:
        # Neither wrapper is safe unescaped; double the single quotes.
        return "'" + value.replace("'", "''") + "'"
    if '"' in value:
        return f"'{value}'"
    return f'"{value}"'


def pretty(args: list[str], token_label: str | None) -> str:
    """The command as it would be typed, with the token shown as a variable.

    Long commands are broken with a backtick, which is PowerShell's line
    continuation, so what is printed can be pasted and run.
    """
    head = ["curl.exe"]
    parts: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-H", "-d"):
            value = args[i + 1]
            if token_label and value.startswith("Authorization: Bearer "):
                value = f"Authorization: Bearer $env:{token_label}"
            parts.append(f"{arg} {quote(value)}")
            i += 2
        elif arg == "-X":
            head.append(f"-X {args[i + 1]}")
            i += 2
        elif arg.startswith("http"):
            head.append(quote(arg) if "?" in arg else arg)
            i += 1
        else:
            head.append(arg)
            i += 1

    single = " ".join(head + parts)
    if len(single) <= WRAP_AT or not parts:
        return single
    return " ".join(head) + " `\n    " + " `\n    ".join(parts)


def run(args: list[str]) -> str:
    result = subprocess.run(["curl", "-s", *args], capture_output=True,
                            text=True, timeout=30)
    return result.stdout.replace("\r\n", "\n").strip()


def save(name: str, blocks: list[str]) -> None:
    with open(os.path.join(RESULTS, f"curl-{name}.txt"), "w",
              encoding="utf-8") as fh:
        fh.write("\n\n".join(blocks).rstrip() + "\n")
    print(f"  wrote curl-{name}.txt")


def call(args: list[str], token_label: str | None = None) -> tuple[str, str]:
    """Run a request and return the command line and the formatted output."""
    output = format_body(run(["-i", *args]))
    return f"{PROMPT} {pretty(['-i', *args], token_label)}", output


def block(args: list[str], token_label: str | None = None) -> str:
    command, output = call(args, token_label)
    return f"{command}\n{output}"


@contextlib.contextmanager
def server():
    """A server for one group of captures.

    The login limit is five a minute, and the counters live in the process, so
    each group gets a fresh one. Without this the script would spend the budget
    on its own setup and start collecting 429s it did not ask for, which is what
    happened the first time it was run.
    """
    proc = start_server()
    try:
        yield
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def sign_in(username: str, password: str, scope: str | None = None) -> dict:
    """One login, returning both tokens, so a group spends as little as it can."""
    data = f"username={username}&password={password}"
    if scope:
        data += f"&scope={scope}"
    body = run(["-X", "POST", f"{HOST}/auth/token",
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", data])
    parsed = json.loads(body)
    if "access_token" not in parsed:
        raise SystemExit(f"could not sign in as {username}: {body}")
    return parsed


FORM = "Content-Type: application/x-www-form-urlencoded"


def expired_token() -> str:
    """A token that was already expired when it was made."""
    return subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, '.');"
         "from secure_api.security import create_access_token;"
         "print(create_access_token('manager', ['reports:read'], minutes=-1))"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()


def group_reading() -> None:
    """The happy path. Two logins."""
    save("health", [block([f"{HOST}/health"])])
    save("token", [block(["-X", "POST", f"{HOST}/auth/token", "-H", FORM,
                          "-d", "username=manager&password=manager-password"])])

    manager = sign_in("manager", "manager-password")["access_token"]
    bearer = f"Authorization: Bearer {manager}"

    save("me", [block([f"{HOST}/auth/me", "-H", bearer], "TOKEN")])
    save("reports", [block([f"{HOST}/reports", "-H", bearer], "TOKEN")])
    save("summary", [block([f"{HOST}/reports/summary", "-H", bearer], "TOKEN")])
    save("create", [block(
        ["-X", "POST", f"{HOST}/reports", "-H", bearer,
         "-H", "Content-Type: application/json",
         "-d", '{"title": "Client workshop, Iloilo", "category": "travel", '
               '"amount": 9800}'], "TOKEN")])


def group_scopes() -> None:
    """Scope narrowing, and the delete only admin may do. Two logins."""
    save("narrow-scope", [block(
        ["-X", "POST", f"{HOST}/auth/token", "-H", FORM,
         "-d", "username=admin&password=admin-password&scope=reports:read"])])

    admin = sign_in("admin", "admin-password")["access_token"]
    save("delete", [block(["-X", "DELETE", f"{HOST}/reports/2", "-H",
                           f"Authorization: Bearer {admin}"], "ADMIN_TOKEN")])


def group_refusals() -> None:
    """Everything that gets turned away. Four logins."""
    manager = sign_in("manager", "manager-password")
    analyst = sign_in("analyst", "analyst-password")["access_token"]
    access = manager["access_token"]

    save("no-token", [block([f"{HOST}/reports"])])

    tampered = access[:-1] + ("x" if access[-1] != "x" else "y")
    save("tampered", [block([f"{HOST}/reports", "-H",
                             f"Authorization: Bearer {tampered}"],
                            "TAMPERED")])

    save("expired", [block([f"{HOST}/reports", "-H",
                            f"Authorization: Bearer {expired_token()}"],
                           "EXPIRED")])

    save("refresh-misuse", [block(
        [f"{HOST}/reports", "-H",
         f"Authorization: Bearer {manager['refresh_token']}"], "REFRESH")])

    save("forbidden", [block(
        ["-X", "POST", f"{HOST}/reports",
         "-H", f"Authorization: Bearer {analyst}",
         "-H", "Content-Type: application/json",
         "-d", '{"title": "Not allowed", "category": "meals", '
               '"amount": 100}'], "ANALYST_TOKEN")])

    save("forbidden-delete", [block(
        ["-X", "DELETE", f"{HOST}/reports/2", "-H",
         f"Authorization: Bearer {access}"], "TOKEN")])

    save("bad-password", [block(
        ["-X", "POST", f"{HOST}/auth/token", "-H", FORM,
         "-d", "username=manager&password=not-the-password"])])

    save("bad-scope", [block(
        ["-X", "POST", f"{HOST}/auth/token", "-H", FORM,
         "-d", "username=analyst&password=analyst-password"
               "&scope=reports:delete"])])


def group_rate_limit() -> None:
    """Six guesses in a row, on a server whose budget is untouched."""
    attempts = []
    for attempt in range(6):
        code = run(["-o", "/dev/null", "-w", "%{http_code}",
                    "-X", "POST", f"{HOST}/auth/token", "-H", FORM,
                    "-d", "username=manager&password=guess"])
        attempts.append(f"  attempt {attempt + 1}: HTTP {code}")

    loop = (f"{PROMPT} 1..6 | ForEach-Object {{ curl.exe -s -o NUL "
            f"-w \"%{{http_code}}`n\" `\n"
            f"    -X POST {HOST}/auth/token `\n"
            f"    -d \"username=manager&password=guess\" }}\n"
            + "\n".join(attempts))

    # The next call has the right password and is still refused.
    limited = block(["-X", "POST", f"{HOST}/auth/token", "-H", FORM,
                     "-d", "username=manager&password=manager-password"])
    save("rate-limit", [loop, limited])


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    for name, group in [("reading", group_reading),
                        ("scopes", group_scopes),
                        ("refusals", group_refusals),
                        ("rate limit", group_rate_limit)]:
        print(f"-- {name}")
        with server():
            group()
    print("done")


if __name__ == "__main__":
    main()
