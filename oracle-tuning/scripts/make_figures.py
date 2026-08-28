"""Builds every figure in the write-up.

Each figure is either output that setup.sh captured into results/, or a slice of
an actual file in sql/ or rman/. Nothing here is retyped by hand, so a figure
cannot say something the database did not do.

The terminal styling and the syntax highlighting come from the shared renderer
written for the Day 3 assignment.

    python3 scripts/make_figures.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
FIG = os.path.join(ROOT, "figures")
RESULTS = os.path.join(ROOT, "results")

sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
try:
    from render import Renderer, numbered, terminal
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"could not import todo-app/scripts/render.py: {exc}")

CHAR_EM = 0.602

# sqlplus writes the SGA sizes with tabs in them, and RMAN indents some of its
# report tables the same way. A tab inside a <div> that is already white-space:pre
# renders as an eight-column jump that does not line up with the header, so they
# are expanded here rather than in the capture.
TAB = 8


def read(name: str, folder: str = RESULTS) -> str:
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read().expandtabs(TAB).rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def fit(body: str, font_size: float, cap: int = 1010) -> int:
    """Width that fits the longest line, so nothing is clipped or floating."""
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, cap))


def trim(body: str) -> str:
    """Drop leading and trailing blank lines from a slice."""
    return body.strip("\n")


def section(text: str, start: str, end: str | None = None) -> str:
    """The part of a capture between two === headers."""
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return trim(text[i:j])


def lines(text: str, first: int, last: int) -> str:
    """Lines first..last of a capture, counting from 1 as the file does."""
    return trim("\n".join(text.split("\n")[first - 1:last]))


def code_slice(path: str, first: str, last: str) -> tuple[str, int]:
    """Lines of a file from the one containing first to the one containing last,
    with the real line number the slice starts at."""
    folder, filename = os.path.split(path)
    src = read(filename, os.path.join(ROOT, folder)).split("\n")
    a = next(i for i, l in enumerate(src) if first in l)
    b = next(i for i, l in enumerate(src) if last in l and i >= a)
    return "\n".join(src[a:b + 1]), a + 1


def code_figure(r: Renderer, name: str, path: str, first: str, last: str,
                lang: str = "sql", width: int = 940) -> None:
    """A source excerpt in an editor window, with its real line numbers."""
    code, start = code_slice(path, first, last)
    filename = os.path.basename(path)
    language = {"sql": "PL/SQL", "bash": "Shell Script"}.get(lang, "Text")
    r.shot(f"""
<div class="win" style="width:{width}px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>{filename}</div>
  </div>
  <div class="ebody">{numbered(code, lang, start=start)}</div>
  <div class="sbar">
    <span>{path}</span><span>{language}</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
""", out(name))


# --------------------------------------------------------------------- figures

def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    startup = read("db_startup.txt")
    instance = read("instance.txt")
    schema = read("schema.txt")
    index = read("index.txt")
    plsql = read("plsql.txt")
    small = read("explain_small.txt")
    scale = read("scale.txt")
    before = read("explain_before.txt")
    after = read("explain_after.txt")
    covering = read("covering.txt")
    archivelog = read("archivelog.txt")
    pre = read("before_backup.txt")
    backup = read("rman_backup.txt")
    drop = read("drop.txt")
    restore = read("rman_restore.txt")
    recovered = read("after_recovery.txt")

    SQLP = "sqlplus / as sysdba"
    RMAN = "rman target /"

    # (filename, title bar, body, font size, width cap)
    shells = [
        # ------------------------------------------------- introduction
        ("fig-startup-listener.png",
         "docker run gvenzl/oracle-free - the instance comes up",
         lines(startup, 1, 16), 11, 1010),
        ("fig-startup-open.png",
         "docker run gvenzl/oracle-free - mounted, opened, ready",
         lines(startup, 36, 56), 11.5, 1010),
        ("fig-instance-version.png",
         f"{SQLP} - what the instance is",
         section(instance, "=== version ===", "=== instance ==="), 11.5, 1010),
        ("fig-instance-layout.png",
         f"{SQLP} - the instance, its PDBs and its memory",
         section(instance, "=== instance ==="), 11.5, 1010),

        # ------------------------------------------------------- step 1
        ("fig-schema-create.png",
         f"{SQLP}@FREEPDB1 - the user and the two tables",
         section(schema, "=== the schema owner ===", "=== ten departments ==="),
         12, 1010),
        ("fig-schema-rows.png",
         f"{SQLP}@FREEPDB1 - ten departments, twelve employees",
         section(schema, "=== what is in the two tables ===",
                 "=== the constraints that came with them ==="), 12, 1010),
        ("fig-schema-constraints.png",
         f"{SQLP}@FREEPDB1 - the constraints that came with them",
         section(schema, "=== the constraints that came with them ==="),
         12, 1010),
        ("fig-index-create.png",
         f"{SQLP}@FREEPDB1 - the index on employees.department_id",
         index, 11.5, 1010),

        # ------------------------------------------------------- step 2
        ("fig-plsql-block.png",
         f"{SQLP}@FREEPDB1 - the anonymous block's output",
         section(plsql, "=== an anonymous PL/SQL block",
                 "=== the same thing as a stored function"), 12, 1010),
        ("fig-plsql-function.png",
         f"{SQLP}@FREEPDB1 - the same averages through the stored function",
         section(plsql, "=== the same thing as a stored function"), 12, 1010),
        ("fig-explain-small-q1.png",
         f"{SQLP}@FREEPDB1 - Q1 on twelve rows",
         section(small, "=== how big the optimizer thinks",
                 "=== Q2: average salary for one department ==="), 10.5, 1070),
        ("fig-explain-small-q2.png",
         f"{SQLP}@FREEPDB1 - Q2 on twelve rows",
         section(small, "=== Q2: average salary for one department ==="),
         10.5, 1070),
        ("fig-scale-load.png",
         f"{SQLP}@FREEPDB1 - 200,000 more employees, and the histogram",
         section(scale, "=== 200,000 more employees ===",
                 "=== how the employees are spread"), 12, 1010),
        ("fig-scale-spread.png",
         f"{SQLP}@FREEPDB1 - how the employees are spread, and what it costs",
         section(scale, "=== how the employees are spread"), 12, 1010),

        ("fig-explain-before-q1.png",
         f"{SQLP}@FREEPDB1 - Q1 with the index invisible",
         section(before, "=== the index is still there",
                 "=== Q2 before:"), 10.5, 1070),
        ("fig-explain-before-q2.png",
         f"{SQLP}@FREEPDB1 - Q2 with the index invisible",
         section(before, "=== Q2 before:"), 10.5, 1070),
        ("fig-explain-after-q1.png",
         f"{SQLP}@FREEPDB1 - Q1 with the index visible",
         section(after, "=== the index is visible", "=== Q2 after:"),
         10.5, 1070),
        ("fig-explain-after-q2.png",
         f"{SQLP}@FREEPDB1 - Q2 with the index visible",
         section(after, "=== Q2 after:",
                 "=== what it costs to force the index"), 10.5, 1070),
        ("fig-explain-forced.png",
         f"{SQLP}@FREEPDB1 - forcing the index on Q1 with a hint",
         section(after, "=== what it costs to force the index"), 10.5, 1070),

        ("fig-covering-create.png",
         f"{SQLP}@FREEPDB1 - the covering index, and its size",
         section(covering, "=== a covering index for Q1 ===",
                 "=== Q1 with the covering index"), 12, 1010),
        ("fig-covering-q1.png",
         f"{SQLP}@FREEPDB1 - Q1 answered from the covering index alone",
         section(covering, "=== Q1 with the covering index",
                 "=== Q2 with the covering index"), 10.5, 1070),
        ("fig-covering-q2.png",
         f"{SQLP}@FREEPDB1 - Q2 answered from the covering index alone",
         section(covering, "=== Q2 with the covering index"), 10.5, 1070),
        ("fig-benchmark.png",
         f"{SQLP}@FREEPDB1 - 50 runs of Q1 and 500 of Q2 per configuration",
         read("benchmark.txt"), 12, 1010),

        # ------------------------------------------------------- step 3
        ("fig-archivelog-switch.png",
         f"{SQLP} - the bounce through MOUNT that enables ARCHIVELOG",
         section(archivelog, "=== before: the log mode", "=== after ==="),
         11.5, 1010),
        ("fig-archivelog-after.png",
         f"{SQLP} - ARCHIVELOG, and the first archived log",
         section(archivelog, "=== after ==="), 12, 1010),
        ("fig-before-backup.png",
         f"{SQLP}@FREEPDB1 - what the backup is being taken of",
         pre, 12, 1010),

        ("fig-rman-config.png",
         f"{RMAN} - the configuration the backup runs under",
         lines(backup, 66, 79), 11.5, 1060),
        ("fig-rman-schema.png",
         f"{RMAN} - REPORT SCHEMA: every file in the backup",
         lines(backup, 80, 97), 11, 1060),
        ("fig-rman-backup-run.png",
         f"{RMAN} - BACKUP AS COMPRESSED BACKUPSET DATABASE PLUS ARCHIVELOG",
         lines(backup, 107, 155), 9.5, 1090),
        ("fig-rman-backup-list.png",
         f"{RMAN} - the autobackup, and LIST BACKUP SUMMARY",
         lines(backup, 168, 183), 11, 1060),
        ("fig-rman-validate.png",
         f"{RMAN} - VALIDATE DATABASE, and REPORT NEED BACKUP",
         lines(backup, 184, 196) + "\n...\n" + lines(backup, 327, 341),
         10.5, 1060),

        ("fig-drop.png",
         f"{SQLP}@FREEPDB1 - the SCN, then the failure",
         section(drop, "=== the point the recovery will aim for",
                 "=== so the two obvious shortcuts both fail ==="), 11.5, 1010),
        ("fig-drop-shortcuts.png",
         f"{SQLP}@FREEPDB1 - neither shortcut can bring it back",
         section(drop, "=== so the two obvious shortcuts both fail ==="),
         11, 1010),

        ("fig-rman-restore.png",
         f"{RMAN} - SET UNTIL SCN, then RESTORE DATABASE",
         lines(restore, 48, 95), 9.5, 1090),
        ("fig-rman-recover.png",
         f"{RMAN} - RECOVER DATABASE, OPEN RESETLOGS, and the new incarnation",
         lines(restore, 97, 115), 11, 1060),
        ("fig-pdb-open.png",
         f"{SQLP} - the pluggable database has to be opened separately",
         read("pdb_open.txt"), 12, 1010),

        ("fig-recovered-rows.png",
         f"{SQLP}@FREEPDB1 - the same 200,012 rows, and the same fingerprint",
         section(recovered, "=== the database is open again ===",
                 "=== every object,"), 12, 1010),
        ("fig-recovered-objects.png",
         f"{SQLP}@FREEPDB1 - every object and constraint came back",
         section(recovered, "=== every object,",
                 "=== the stored function still runs ==="), 12, 1010),
        ("fig-recovered-function.png",
         f"{SQLP}@FREEPDB1 - the function runs, and the incarnation moved on",
         section(recovered, "=== the stored function still runs ==="),
         11.5, 1010),
    ]

    # (filename, path, first line, last line, language)
    codes = [
        ("fig-code-departments.png", "sql/02_schema.sql",
         "PROMPT === departments ===", ");", "sql"),
        ("fig-code-employees.png", "sql/02_schema.sql",
         "PROMPT === employees ===", "CONSTRAINT employees_salary_ck", "sql"),
        ("fig-code-index.png", "sql/03_index.sql",
         "PROMPT === the index the assignment asks for ===",
         "CREATE INDEX hr_day9.employees_dept_idx", "sql"),
        ("fig-code-plsql-block.png", "sql/04_plsql.sql",
         "DECLARE", "END;", "sql"),
        ("fig-code-plsql-function.png", "sql/04_plsql.sql",
         "CREATE OR REPLACE FUNCTION", "END dept_avg_salary;", "sql"),
        ("fig-code-invisible.png", "sql/07_explain_before.sql",
         "ALTER INDEX hr_day9.employees_dept_idx INVISIBLE;",
         "ALTER INDEX hr_day9.employees_dept_idx INVISIBLE;", "sql"),
        ("fig-code-covering.png", "sql/09_covering.sql",
         "PROMPT === a covering index for Q1 ===",
         "ON hr_day9.employees (department_id, salary);", "sql"),
        ("fig-code-rman-backup.png", "rman/01_backup.rman",
         "SHOW ALL;", "LIST BACKUP SUMMARY;", "bash"),
        ("fig-code-rman-restore.png", "rman/02_restore.rman",
         "RUN {", "LIST INCARNATION OF DATABASE;", "bash"),
        ("fig-code-drop.png", "sql/13_drop.sql",
         "PROMPT === the failure ===",
         "DROP TABLE hr_day9.employees CASCADE CONSTRAINTS PURGE;", "sql"),
    ]

    with Renderer(scale=2) as r:
        for name, title, body, size, cap in shells:
            r.shot(terminal(title, body, width=fit(body, size, cap),
                            font_size=size),
                   out(name))

        for name, path, first, last, lang in codes:
            code_figure(r, name, path, first, last, lang)

    print(f"\n{len(shells) + len(codes)} figures in {FIG}")


if __name__ == "__main__":
    main()
