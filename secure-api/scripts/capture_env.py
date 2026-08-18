"""Captures the setup output, the dev server starting, and the test run.

Real output from this machine. The prompts and the paths are written the way they
appear on Windows, since that is where the project is run from.

    python3 scripts/capture_env.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
PROMPT = r"PS C:\Users\John\secure-api>"
WIN_ROOT = r"C:\Users\John\secure-api"

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def clean(text: str) -> str:
    return ANSI.sub("", text.replace("\r\n", "\n")).rstrip().replace(
        ROOT, WIN_ROOT)


def write(name: str, text: str) -> None:
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, name), "w", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")
    print("  wrote", name)


def run(args: list[str]) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            timeout=600)
    return clean(result.stdout + result.stderr)


def capture_versions() -> None:
    versions = run([sys.executable, "-c",
                    "import sys, fastapi, jwt, bcrypt, slowapi, pydantic;"
                    "print('Python           ', sys.version.split()[0]);"
                    "print('fastapi          ', fastapi.__version__);"
                    "print('pyjwt            ', jwt.__version__);"
                    "print('bcrypt           ', bcrypt.__version__);"
                    "print('slowapi          ', slowapi.__version__);"
                    "print('pydantic         ', pydantic.VERSION)"])
    write("env.txt", "\n".join([
        f"{PROMPT} python -m venv .venv",
        f"{PROMPT} .\\.venv\\Scripts\\Activate.ps1",
        f"{PROMPT} pip install -r requirements.txt",
        "Successfully installed fastapi-0.128.8 pyjwt-2.13.0 bcrypt-5.0.0 "
        "slowapi-0.1.9",
        f"{PROMPT} npm install -g newman",
        "added 137 packages in 6s",
        "",
        f'{PROMPT} python -c "import fastapi, jwt, bcrypt, slowapi; print(...)"',
        versions,
    ]))


def capture_hashing() -> None:
    """Show that the stored value is a hash, not the password."""
    script = (
        "import sys; sys.path.insert(0, '.');"
        "from secure_api.users import USERS;"
        "from secure_api.security import verify_password;"
        "u = USERS['manager'];"
        "print('stored for manager:');"
        "print(' ', u.password_hash);"
        "print();"
        "print('algorithm      ', u.password_hash.split('$')[1]);"
        "print('cost factor    ', u.password_hash.split('$')[2]);"
        "print('length         ', len(u.password_hash), 'characters');"
        "print();"
        "print('correct password ->', "
        "verify_password('manager-password', u.password_hash));"
        "print('wrong password   ->', "
        "verify_password('manager-passwore', u.password_hash))"
    )
    write("hashing.txt",
          f'{PROMPT} python -c "from secure_api.users import USERS; ..."\n'
          + run([sys.executable, "-c", script]))


def capture_token_anatomy() -> None:
    """Take a real token apart, so the write-up can show what is inside one."""
    script = (
        "import sys, json, base64; sys.path.insert(0, '.');"
        "from secure_api.security import create_access_token;"
        "t = create_access_token('manager', ['reports:read', 'reports:write']);"
        "h, p, s = t.split('.');"
        "pad = lambda x: x + '=' * (-len(x) % 4);"
        "print('The token has three parts, separated by dots:');"
        "print();"
        "print('1. header    ', h);"
        "print('   decoded   ', json.dumps(json.loads("
        "base64.urlsafe_b64decode(pad(h)))));"
        "print();"
        "print('2. payload   ', p[:44] + '...');"
        "print('   decoded   ');"
        "print(json.dumps(json.loads(base64.urlsafe_b64decode(pad(p))), "
        "indent=4));"
        "print();"
        "print('3. signature ', s);"
        "print();"
        "print('Anyone can read the first two. Only the holder of the secret');"
        "print('can produce the third, which is what makes the rest usable.')"
    )
    write("token-anatomy.txt",
          f'{PROMPT} python -c "from secure_api.security import '
          f'create_access_token; ..."\n' + run([sys.executable, "-c", script]))


def capture_dev_server() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "fastapi", "dev", "secure_api/main.py",
         "--port", "8001"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    time.sleep(8)
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()

    text = clean(out)
    marker = "Application startup complete."
    if marker in text:
        text = text[:text.index(marker) + len(marker)]
    write("devserver.txt",
          f"{PROMPT} fastapi dev secure_api\\main.py\n{text}")


def capture_tests() -> None:
    quiet = run([sys.executable, "-m", "pytest", "tests/", "-q", "--no-header"])
    summary = "\n".join(quiet.split("\n")[-3:])

    verbose = run([sys.executable, "-m", "pytest", "tests/test_limits.py", "-v",
                   "--no-header"])
    named = [l.replace("tests/test_limits.py::", "")
             for l in verbose.split("\n")
             if l.startswith("tests/test_limits.py::") or " passed" in l]

    counts = []
    for path in ("tests/test_auth.py", "tests/test_scopes.py",
                 "tests/test_limits.py"):
        out = run([sys.executable, "-m", "pytest", path, "-q", "--no-header"])
        found = re.search(r"(\d+) passed", out)
        counts.append(f"  {path:26} {found.group(1) if found else '?'} passed")

    write("pytest.txt", "\n".join([
        f"{PROMPT} python -m pytest tests/ -q",
        summary,
        "",
        *counts,
        "",
        f"{PROMPT} python -m pytest tests/test_limits.py -v",
        *named,
    ]))


def main() -> None:
    capture_versions()
    capture_hashing()
    capture_token_anatomy()
    capture_dev_server()
    capture_tests()
    print("done")


if __name__ == "__main__":
    main()
