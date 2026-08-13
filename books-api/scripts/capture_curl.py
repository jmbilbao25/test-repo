"""Runs each endpoint through curl against the real server and saves the output.

The server is started here, the requests are genuine, and whatever comes back is
written to results/ for the figures to be built from. Nothing is typed in by
hand, so a change in the API shows up in the write-up.

The one thing that is not byte for byte what curl printed: a JSON body is
re-indented, because Flask sends it on a single line and a list of books then
runs off the side of the figure. The status line, the headers and the data are
untouched.

    python3 scripts/capture_curl.py
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
PORT = 5000
BASE = f"http://localhost:{PORT}"

# name, human description, curl arguments after the base url
CALLS = [
    ("post", "Create a book",
     ["-i", "-X", "POST", f"{BASE}/books",
      "-H", "Content-Type: application/json",
      "-d", '{"title": "The Hobbit", "author": "J. R. R. Tolkien", '
            '"year": 1937}']),
    ("get-all", "List every book", ["-i", f"{BASE}/books"]),
    ("get-filtered", "List books filtered by author",
     ["-i", f"{BASE}/books?author=orwell"]),
    ("get-one", "Retrieve one book by id", ["-i", f"{BASE}/books/3"]),
    ("put", "Update a book",
     ["-i", "-X", "PUT", f"{BASE}/books/3",
      "-H", "Content-Type: application/json",
      "-d", '{"available": false}']),
    ("delete", "Delete a book", ["-i", "-X", "DELETE", f"{BASE}/books/3"]),
    ("get-deleted", "The deleted book is gone", ["-i", f"{BASE}/books/3"]),
    ("err-validation", "A body with no title",
     ["-i", "-X", "POST", f"{BASE}/books",
      "-H", "Content-Type: application/json",
      "-d", '{"author": "Nobody"}']),
    ("err-conflict", "A book that is already on the list",
     ["-i", "-X", "POST", f"{BASE}/books",
      "-H", "Content-Type: application/json",
      "-d", '{"title": "Brave New World", "author": "Aldous Huxley"}']),
    ("err-notfound", "An id that does not exist", ["-i", f"{BASE}/books/99"]),
]


def start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "flask", "--app", "books_api.app", "run",
         "--port", str(PORT)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                return proc
        except OSError:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("the server did not come up")


def pretty(args: list[str]) -> str:
    """The command as a reader would type it, wrapped where it gets long."""
    out = ["curl"]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-d":
            out.append(f"\\\n  -d '{args[i + 1]}'")
            i += 2
        elif arg == "-H":
            out.append(f"\\\n  -H '{args[i + 1]}'")
            i += 2
        elif arg == "-X":
            out.append(f"-X {args[i + 1]}")
            i += 2
        elif arg.startswith("http"):
            out.append(f"'{arg}'" if "?" in arg else arg)
            i += 1
        else:
            out.append(arg)
            i += 1
    return " ".join(out)


def indent_json_body(output: str) -> str:
    """Re-indent the JSON body, leaving the status line and headers alone."""
    if "\n\n" not in output:
        return output
    head, _, body = output.partition("\n\n")
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return output
    return head + "\n\n" + json.dumps(parsed, indent=2)


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    server = start_server()
    print(f"server up on {BASE}")
    try:
        for name, description, args in CALLS:
            result = subprocess.run(["curl", "-s", *args],
                                    capture_output=True, text=True, timeout=20)
            body = indent_json_body(result.stdout.replace("\r\n", "\n").strip())
            text = f"$ {pretty(args)}\n{body}\n"
            with open(os.path.join(RESULTS, f"curl-{name}.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(text)
            status = body.split("\n", 1)[0] if body else "(no output)"
            print(f"  {name:15} {description:36} {status}")
    finally:
        server.terminate()
        server.wait(timeout=10)
    print("done")


if __name__ == "__main__":
    main()
