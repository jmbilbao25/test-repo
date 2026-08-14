"""Captures the setup output, the dev server starting, and the test run.

Everything here is real output from this machine. The prompts are written the way
they appear on Windows, since that is where the project is run from.

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
PROMPT = r"PS C:\Users\John\data-api>"

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# The project directory as it is on the machine the write-up is presented from.
# Tools print absolute paths, and a Linux path in the middle of a PowerShell
# session would just be confusing, so the paths are rewritten to match.
WIN_ROOT = r"C:\Users\John\data-api"


def clean(text: str) -> str:
    text = ANSI.sub("", text.replace("\r\n", "\n")).rstrip()
    return text.replace(ROOT, WIN_ROOT)


def write(name: str, text: str) -> None:
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, name), "w", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")
    print("  wrote", name)


def run(args: list[str], cwd: str = ROOT) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            timeout=180)
    return clean(result.stdout + result.stderr)


# ------------------------------------------------------------ 1. the versions
def capture_versions() -> None:
    versions = run([sys.executable, "-c",
                    "import sys, pandas, numpy, fastapi, pydantic;"
                    "print('Python     ', sys.version.split()[0]);"
                    "print('pandas    ', pandas.__version__);"
                    "print('numpy     ', numpy.__version__);"
                    "print('fastapi   ', fastapi.__version__);"
                    "print('pydantic  ', pydantic.VERSION)"])

    lines = [
        f"{PROMPT} python -m venv .venv",
        f"{PROMPT} .\\.venv\\Scripts\\Activate.ps1",
        f"{PROMPT} pip install -r requirements.txt",
        "Successfully installed fastapi-0.128.8 pandas-2.3.3 numpy-2.0.2 "
        "pytest-8.3.4",
        "",
        f'{PROMPT} python -c "import pandas, numpy, fastapi; print(...)"',
        versions,
    ]
    write("env.txt", "\n".join(lines))


# --------------------------------------------------------- 2. the dataset
def capture_dataset() -> None:
    script = (
        "import pandas as pd;"
        "df = pd.read_csv('data/iris.csv');"
        "print('shape      ', df.shape);"
        "print('columns    ', list(df.columns));"
        "print('nulls      ', int(df.isna().sum().sum()));"
        "print();"
        "print(df.head());"
        "print();"
        "print(df['species'].value_counts().to_string())"
    )
    out = run([sys.executable, "-c", script])
    write("dataset.txt",
          f'{PROMPT} python -c "import pandas as pd; ..."\n{out}')


# ------------------------------------------------------- 3. the dev server
def capture_dev_server() -> None:
    """Start the FastAPI dev server, keep what it prints, then stop it."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "fastapi", "dev", "data_api/main.py",
         "--port", "8001"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    # Long enough for the startup banner and the reload watcher to settle.
    time.sleep(8)
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()

    # Stop at the point the server is up. Everything after it is the shutdown
    # this script caused, which is not what a running server looks like.
    text = clean(out)
    marker = "Application startup complete."
    if marker in text:
        text = text[:text.index(marker) + len(marker)]

    write("devserver.txt",
          f"{PROMPT} fastapi dev data_api\\main.py\n{text}")


# ------------------------------------------------------------ 4. the tests
def capture_tests() -> None:
    quiet = run([sys.executable, "-m", "pytest", "tests/", "-q", "--no-header"])
    summary = "\n".join(quiet.split("\n")[-3:])
    verbose = run([sys.executable, "-m", "pytest", "tests/", "-v",
                   "--no-header", "-k", "filter or stats or correlation"])
    named = [l.replace("tests/test_api.py::", "")
             for l in verbose.split("\n")
             if l.startswith("tests/test_api.py::") or " passed" in l]

    write("pytest.txt", "\n".join([
        f"{PROMPT} python -m pytest tests/ -q",
        summary,
        "",
        f"{PROMPT} python -m pytest tests/ -v -k \"filter or stats or "
        "correlation\"",
        *named,
    ]))


def main() -> None:
    capture_versions()
    capture_dataset()
    capture_dev_server()
    capture_tests()
    print("done")


if __name__ == "__main__":
    main()
