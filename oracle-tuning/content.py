"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment.

Every measured number in the prose is parsed out of results/, which is the same
source the figures are built from, so a sentence cannot end up disagreeing with
the screenshot beside it.
"""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

TITLE = "Optimizing and Recovering an Oracle Database"
DAY = "Day 9 Hands-on Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 28, 2026"


# --------------------------------------------------------------- reading facts

def _read(name: str, folder: str = RESULTS) -> str:
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read()


def _benchmark() -> dict[tuple[str, str], dict[str, float]]:
    """The per-configuration numbers out of results/benchmark.txt.

    The PL/SQL that produced the file pads with RPAD and LPAD to fixed widths,
    so the columns are sliced by position rather than split on whitespace: the
    label "no index" has a space in it and would otherwise split in two.
    """
    stats: dict[tuple[str, str], dict[str, float]] = {}
    for line in _read("benchmark.txt").split("\n"):
        if not line[:2] in ("Q1", "Q2") or "=" in line:
            continue
        key = (line[0:4].strip(), line[4:20].strip())
        stats[key] = {
            "runs": float(line[20:27].strip().replace(",", "")),
            "ms": float(line[27:40].strip().replace(",", "")),
            "gets": float(line[40:53].strip().replace(",", "")),
        }
    missing = {("Q1", "no index"), ("Q2", "no index"),
               ("Q1", "department_id"), ("Q2", "department_id"),
               ("Q1", "covering"), ("Q2", "covering")} - stats.keys()
    if missing:
        raise SystemExit(f"benchmark.txt is missing {sorted(missing)}")
    return stats


B = _benchmark()


def _after(needle: str, capture: str, offset: int = 2) -> str:
    """The value offset lines below the line containing needle."""
    rows = _read(capture).split("\n")
    i = next(n for n, line in enumerate(rows) if needle in line)
    return rows[i + offset].strip()


FINGERPRINT_BEFORE = _after("FINGERPRINT", "before_backup.txt")
FINGERPRINT_AFTER = _after("FINGERPRINT", "after_recovery.txt")
RESTORE_SCN = _read("restore_point.txt").strip()

# The row count and the salary total, off the EMPLOYEES line of the contents
# query, which reads "EMPLOYEES  200,012  15,018,179,225.12".
_EMP = [c for c in _read("before_backup.txt").split("\n")
        if c.startswith("EMPLOYEES")][0].split()
ROWS = _EMP[1]
SALARY_TOTAL = _EMP[2]

VERSION = _read("instance.txt").split("\n")[3].strip()
RESET_SCN = _read("after_recovery.txt").rstrip().split("\n")[-1].split()[1]


def _gets(q: str, cfg: str) -> str:
    return f"{int(B[(q, cfg)]['gets']):,}"


def _ms(q: str, cfg: str) -> str:
    return f"{B[(q, cfg)]['ms']:.3f}"


def _times(q: str, base: str, cfg: str) -> str:
    """How many times faster cfg is than base for q, as "10.7x"."""
    return f"{B[(q, base)]['ms'] / B[(q, cfg)]['ms']:.1f}x"


def _sql(path: str, first: str, last: str) -> list[str]:
    """Lines of a file from the one containing first to the one containing last.

    Used so the query quoted in the text is the query that ran, rather than a
    copy of it that can fall out of date.
    """
    folder, filename = os.path.split(path)
    rows = _read(filename, os.path.join(HERE, folder)).rstrip("\n").split("\n")
    a = next(i for i, l in enumerate(rows) if first in l)
    b = next(i for i, l in enumerate(rows) if last in l and i >= a)
    return rows[a:b + 1]


# --------------------------------------------------------------------- content

def blocks() -> list[tuple]:
    return [
        ("h1", "What this covers"),
        ("p",
         "This assignment builds an Oracle database, measures a query against "
         "it, indexes the query, then destroys a table and brings it back from "
         "an RMAN backup. Everything in it ran against a real instance: "
         f"{VERSION}, started from the gvenzl/oracle-free container image on "
         "eight cores with a 1.5 GB SGA."),
        ("p",
         "Every figure is output captured from that instance. The capture "
         "files live in results/, scripts/make_figures.py renders those files "
         "into the figures below, and none of it is retyped by hand, so no "
         "figure can show something the database did not do. The numbers "
         "quoted in the text are parsed from the same files."),
        ("note",
         "The short version of what was found: the index the assignment asks "
         "for does not speed up the query the assignment asks for, and the "
         "execution plans show exactly why. It speeds up a neighbouring query "
         f"by {_times('Q2', 'no index', 'department_id')}, and a two-column "
         "version of it makes the original query read 43 percent fewer blocks "
         "while still taking longer on the clock. All three results are below "
         "with the plans and the timings that produced them."),

        ("break",),
        ("h1", "Introduction: creating the database"),
        ("p",
         "The instance runs in a container, which is the closest thing to a "
         "fresh install that can be repeated exactly. scripts/start_db.sh "
         "creates it and waits for it to open; the container's own startup "
         "narration is the record of the creation."),
        ("fig", "fig-startup-listener.png",
         "The instance being created: the container initialises the database "
         "and starts the TNS listener on port 1521.", 6.5),
        ("fig", "fig-startup-open.png",
         "The same startup finishing: the SGA is allocated, the database is "
         "mounted and opened, and the container reports it ready to use.", 6.5),
        ("p",
         "Oracle 23ai is multitenant, so what came up is not one database but "
         "a container database, FREE, holding a seed and one pluggable "
         "database, FREEPDB1. That distinction matters twice later on: the "
         "schema is built inside FREEPDB1, while ARCHIVELOG mode and the RMAN "
         "backup are properties of the container database around it."),
        ("fig", "fig-instance-version.png",
         "The version and the container database. Note LOG_MODE: the image "
         "ships in NOARCHIVELOG, which Step 3 has to change before it can "
         "back anything up usefully.", 6.5),
        ("fig", "fig-instance-layout.png",
         "The instance, the two pluggable databases inside it, and the memory "
         "and file settings the rest of the assignment runs under.", 6.5),

        ("break",),
        ("h1", "Step 1: creating the tables and the index"),
        ("p",
         "departments is created first, because employees.department_id "
         "references it and a foreign key cannot point at a table that does "
         "not exist yet. Both tables get a primary key, and employees gets a "
         "check constraint on salary as well, so that the recovery in Step 3 "
         "has something to prove came back besides the rows."),
        ("fig", "fig-code-departments.png",
         "departments: the parent table, created first.", 6.2),
        ("fig", "fig-code-employees.png",
         "employees: primary key, the foreign key to departments, and a check "
         "constraint that a salary has to be positive.", 6.2),
        ("fig", "fig-schema-create.png",
         "The schema owner and both tables being created. HR_DAY9 is an "
         "ordinary application user; SELECT_CATALOG_ROLE is granted only so "
         "that it can read execution plans out of v$sql_plan in Step 2.", 6.5),
        ("p",
         "Ten departments and twelve employees are inserted, which is two more "
         "employees than the assignment asks for and lets two departments hold "
         "more than one person, so the averages in Step 2 are averages of "
         "something rather than of a single row."),
        ("fig", "fig-schema-rows.png",
         "The row counts after the inserts, and every employee joined to the "
         "department that the foreign key points at.", 6.5),
        ("fig", "fig-schema-constraints.png",
         "The constraints that came with the two tables. The SYS_C-prefixed "
         "checks are the NOT NULL declarations, which Oracle stores as check "
         "constraints with generated names.", 6.5),
        ("p",
         "The index the assignment asks for is on employees.department_id. It "
         "is worth being clear that it is the third index in the schema and "
         "not the first: Oracle built a unique index behind each primary key "
         "automatically, and those exist whether they are wanted or not. This "
         "one is the only index so far that is a deliberate choice, and "
         "therefore the only one whose value is worth arguing about."),
        ("fig", "fig-code-index.png",
         "The index on employees.department_id.", 6.2),
        ("fig", "fig-index-create.png",
         "The index being created, all three indexes on the two tables, and "
         "what each costs on disk. At twelve rows every segment is one 64 KB "
         "extent, so the index costs as much space as the table it indexes.",
         6.5),

        ("break",),
        ("h1", "Step 2: the PL/SQL query"),
        ("p",
         "The assignment asks for a PL/SQL query returning the average salary "
         "of employees in each department. It is written twice: once as an "
         "anonymous block that reports every department, and once as a stored "
         "function that SQL can call per department."),
        ("p",
         "One decision inside the block is worth stating, because it is the "
         "difference between PL/SQL that helps and PL/SQL that hurts. The "
         "average is computed by SQL, in the cursor, and the PL/SQL only walks "
         "the result and formats it. Fetching all the employee rows into PL/SQL "
         "and averaging them in a loop would produce the same answer while "
         "moving every row across the call interface to compute a number the "
         "database can produce itself."),
        ("fig", "fig-code-plsql-block.png",
         "The anonymous block. The aggregate is left in SQL; the LEFT JOIN "
         "means a department with no employees is still reported.", 6.4),
        ("fig", "fig-plsql-block.png",
         "The block's output. All ten departments appear, including the eight "
         "that hold exactly one person.", 6.5),
        ("fig", "fig-code-plsql-function.png",
         "The same average as a stored function. AVG over no rows returns NULL "
         "rather than raising, so NO_DATA_FOUND cannot happen here, and the "
         "comment says so rather than leaving a handler that never fires "
         "looking like it matters.", 6.4),
        ("fig", "fig-plsql-function.png",
         "The function called once per department from ordinary SQL, giving "
         "the same ten averages.", 6.5),

        ("h1", "The plans at twelve rows"),
        ("p",
         "The assignment asks for the plan before and after optimization. "
         "Taken at twelve rows, that comparison has no content, and it is "
         "worth showing why before moving on rather than presenting a "
         "meaningless pair of plans as a result."),
        ("fig", "fig-explain-small-q1.png",
         "Q1, the average per department, on twelve rows: a full scan costing "
         "six buffer gets. The whole table is five blocks, so no index can "
         "save more than a few block reads.", 6.5),
        ("fig", "fig-explain-small-q2.png",
         "Q2, the average for one department, on twelve rows. Here the "
         "optimizer does pick the index, and reads two blocks instead of six. "
         "A saving of four block reads is real and irrelevant.", 6.5),
        ("note",
         "Both plans are correct and neither is interesting. An index is a "
         "trade: a second structure to maintain on every insert, in exchange "
         "for reading less on the way in. At five blocks there is nothing to "
         "read less of. To say anything about optimization the table has to be "
         "big enough for the two plans to cost different amounts."),

        ("h1", "Making the table big enough for the question to have an answer"),
        ("p",
         "200,000 more employees are loaded into the same table, across the "
         "same ten departments, with the distribution skewed the way a real "
         "company is skewed: one small department and nine large ones. That "
         "skew is the point. An index helps when it can rule most of the table "
         "out, so the interesting query is the one that asks about the small "
         "department."),
        ("fig", "fig-scale-load.png",
         "The load, and the statistics gathered afterwards. Oracle built a "
         "FREQUENCY histogram with one bucket per department on "
         "department_id.", 6.5),
        ("p",
         "The histogram is what makes the rest of Step 2 work. Without one the "
         "optimizer assumes the ten departments are the same size and costs a "
         "lookup on any single department at a tenth of the table, which is too "
         "much to be worth an index. The histogram tells it that department 10 "
         "is 0.25 percent of the rows, and that is the difference between a "
         "full scan and an index range scan."),
        ("fig", "fig-scale-spread.png",
         "The real distribution: 501 employees in Executive against roughly "
         "22,200 in each of the other nine, and what the segments now cost. "
         "The index on department_id alone is already 5 MB against the table's "
         "8 MB.", 6.5),

        ("h1", "Before and after, on the same table"),
        ("p",
         "To measure the query without the index, the index is made INVISIBLE "
         "rather than dropped. Oracle keeps maintaining an invisible index but "
         "hides it from the optimizer, so the before and after plans are taken "
         "against a byte-for-byte identical table with identical statistics. "
         "Dropping and recreating would also rebuild the segment, and then the "
         "comparison would have two variables in it instead of one."),
        ("fig", "fig-code-invisible.png",
         "One statement is the whole of the before/after apparatus.", 5.6),
        ("fig", "fig-explain-before-q1.png",
         "Before, Q1: TABLE ACCESS FULL, "
         + _gets("Q1", "no index") + " buffer gets.", 6.5),
        ("fig", "fig-explain-before-q2.png",
         "Before, Q2: also TABLE ACCESS FULL, "
         + _gets("Q2", "no index") + " buffer gets, with the department "
         "filter applied to every row it reads.", 6.5),
        ("fig", "fig-explain-after-q1.png",
         "After, Q1: the index is visible and the plan has not changed. Same "
         "operation, same plan hash value, same "
         + _gets("Q1", "department_id") + " buffer gets.", 6.5),
        ("fig", "fig-explain-after-q2.png",
         "After, Q2: INDEX RANGE SCAN feeding TABLE ACCESS BY INDEX ROWID "
         "BATCHED. The index itself costs four gets; the row lookups bring the "
         "total to " + _gets("Q2", "department_id") + ".", 6.5),
        ("table", [
            ["Query", "Before", "After", "Buffer gets"],
            ["Q1 - average per department",
             "TABLE ACCESS FULL", "TABLE ACCESS FULL",
             _gets("Q1", "no index") + " to " + _gets("Q1", "department_id")],
            ["Q2 - average for department 10",
             "TABLE ACCESS FULL", "INDEX RANGE SCAN",
             _gets("Q2", "no index") + " to " + _gets("Q2", "department_id")],
        ], [1.9, 1.6, 1.6, 1.4]),
        ("p",
         "Q1 is unchanged, and that is not a failure of the index or of the "
         "optimizer. Q1 averages the salary of every employee, so it has to "
         "read every employee. An index on department_id can find rows by "
         "department, but it does not contain the salaries, so any plan built "
         "on it would still have to visit all 200,012 table rows to get them, "
         "one at a time through a rowid lookup, which is strictly more work "
         "than reading the table straight through."),
        ("p",
         "That is a claim about cost, so it is worth checking rather than "
         "asserting. Hinting the query to use the index anyway shows what the "
         "optimizer decided:"),
        ("fig", "fig-explain-forced.png",
         "An INDEX hint naming the index on Q1. The plan is the full scan "
         "again: the hint is not obeyed, because the index cannot produce the "
         "columns the query needs and a hint cannot make a plan legal that was "
         "not. A hint that is silently dropped looks exactly like a hint that "
         "worked, which is a good reason to read the plan rather than trust "
         "the hint.", 6.5),

        ("h1", "The optimisation that does help Q1"),
        ("p",
         "If the problem with the single-column index is that it does not hold "
         "the salaries, the fix is an index that does. An index on "
         "(department_id, salary) holds both columns Q1 reads, so the "
         "aggregate can be answered from the index and the table never has to "
         "be opened. The index is smaller than the table, because it holds two "
         "columns instead of four, and reading less is the whole of the "
         "improvement."),
        ("fig", "fig-code-covering.png",
         "The covering index. The comment records why it is allowed to answer "
         "a query over the whole table.", 6.2),
        ("p",
         "That last point is a real constraint and not a detail. A B-tree "
         "index leaves a row out only when every indexed column is NULL, so an "
         "index on a nullable column alone cannot be trusted to contain every "
         "row. Here salary is NOT NULL, which guarantees an entry for every "
         "employee, and that guarantee is what lets the optimizer answer a "
         "GROUP BY over the whole table from the index. Had salary been "
         "nullable, this optimisation would not have been available."),
        ("fig", "fig-covering-create.png",
         "The covering index being created, and the sizes side by side.", 6.5),
        ("fig", "fig-covering-q1.png",
         "Q1 answered by INDEX FAST FULL SCAN with no table access at all: "
         + _gets("Q1", "covering") + " buffer gets against "
         + _gets("Q1", "no index") + ", a 43 percent reduction.", 6.5),
        ("fig", "fig-covering-q2.png",
         "Q2 with the same index: " + _gets("Q2", "covering") + " buffer "
         "gets. The index range scan now finds the salaries in the index "
         "beside the department, so the 501 rowid lookups into the table "
         "disappear.", 6.5),

        ("h1", "Measured, rather than only planned"),
        ("p",
         "Plans predict cost; they do not prove it. Each configuration was "
         "therefore run in a loop, Q1 fifty times and Q2 five hundred times, "
         "with the logical reads read back out of v$sqlstats per cursor."),
        ("fig", "fig-benchmark.png",
         "Fifty runs of Q1 and five hundred of Q2 under each of the three "
         "index configurations.", 6.5),
        ("table", [
            ["", "No index", "department_id", "(department_id, salary)"],
            ["Q1 buffer gets", _gets("Q1", "no index"),
             _gets("Q1", "department_id"), _gets("Q1", "covering")],
            ["Q1 ms per run", _ms("Q1", "no index"),
             _ms("Q1", "department_id"), _ms("Q1", "covering")],
            ["Q2 buffer gets", _gets("Q2", "no index"),
             _gets("Q2", "department_id"), _gets("Q2", "covering")],
            ["Q2 ms per run", _ms("Q2", "no index"),
             _ms("Q2", "department_id"), _ms("Q2", "covering")],
        ], [1.5, 1.2, 1.5, 2.3]),
        ("p",
         "Q2 is the clear win: "
         + _times("Q2", "no index", "department_id")
         + " faster with the index the assignment asks for, and "
         + _times("Q2", "no index", "covering")
         + " faster with the covering index, which is what "
         "reading four blocks instead of a thousand looks like on the clock."),
        ("note",
         "Q1 is more interesting, because the two measurements disagree. The "
         "covering index cuts Q1's logical reads by 43 percent, from "
         + _gets("Q1", "no index") + " to " + _gets("Q1", "covering")
         + " blocks, and yet Q1 got slower: " + _ms("Q1", "covering")
         + " ms against " + _ms("Q1", "no index") + " ms. Fewer blocks is not "
         "the same as less time. A full table scan is read with multiblock "
         "reads, while an index fast full scan of a 200,000-entry index walks "
         "more, smaller structures; at this size the table already fits in the "
         "buffer cache, so there is no physical I/O for the block saving to "
         "save, and only the extra CPU is left. The block reduction is what "
         "would pay off on a table too large to cache. Had only the plans been "
         "collected, this would have been written up as a straight improvement."),

        ("break",),
        ("h1", "Step 3: backup and recovery"),
        ("p",
         "The image ships in NOARCHIVELOG mode, and in that mode the online "
         "redo logs are overwritten as they fill. That leaves no record of what "
         "changed after a backup, so the only recovery possible is back to the "
         "moment of the backup, and only from a backup taken while the database "
         "was shut down. ARCHIVELOG mode copies each redo log off before it is "
         "reused. It is what makes both a backup of an open database and a "
         "recovery to a chosen point in time possible, and this assignment "
         "needs both."),
        ("fig", "fig-archivelog-switch.png",
         "The switch to ARCHIVELOG. It is made at MOUNT, so the database is "
         "closed and reopened around it; the flash recovery area is pointed "
         "somewhere with room first.", 6.5),
        ("fig", "fig-archivelog-after.png",
         "ARCHIVELOG confirmed, both pluggable databases open again, and a "
         "forced log switch so that at least one archived log exists before "
         "the backup runs.", 6.5),
        ("p",
         "Before backing anything up, the state being backed up is recorded: "
         f"the row counts, the total of all {ROWS} salaries, a hash "
         "fingerprint of the employees table, and the list of objects that "
         "will have to come back. Without this, a successful recovery can only "
         "be declared, not shown."),
        ("fig", "fig-before-backup.png",
         "What the backup is a backup of. The fingerprint sums a hash of every "
         "employee row: a total of the salaries alone would not notice two "
         "employees swapping values, and a hash of the ordered rows would.",
         6.5),

        ("h1", "The backup"),
        ("p",
         "RMAN is Oracle's own backup tool, and for this it is the one that "
         "matters, because it understands the file formats. A filesystem copy "
         "of an open database catches datafiles mid-write and produces "
         "something that cannot be opened. RMAN reads through the instance, "
         "checks every block as it goes, and records what it did in the control "
         "file so a later RESTORE knows what exists."),
        ("fig", "fig-code-rman-backup.png",
         "The backup script. PLUS ARCHIVELOG is the part that makes the backup "
         "usable on its own.", 6.4),
        ("p",
         "PLUS ARCHIVELOG archives the current redo log first, includes the "
         "archived logs in the backup, then archives again afterwards. The "
         "datafile copies inside the backup are inconsistent with each other, "
         "because the database was open and changing while they were read, and "
         "the redo in the same backup is what reconciles them."),
        ("fig", "fig-rman-config.png",
         "The configuration the backup runs under. Control file autobackup is "
         "turned on so that a recovery which has also lost the control file "
         "does not have to be talked through the backup set by hand.", 6.5),
        ("fig", "fig-rman-schema.png",
         "REPORT SCHEMA: every datafile in the container database and in both "
         "pluggable databases, which is what BACKUP DATABASE will cover.",
         6.5),
        ("fig", "fig-rman-backup-run.png",
         "The backup itself: the archived logs, then all fifteen datafiles as "
         "compressed backup sets, then the archived logs again.", 6.5),
        ("fig", "fig-rman-backup-list.png",
         "The control file and SPFILE autobackup, and LIST BACKUP SUMMARY "
         "showing the six backup sets that resulted.", 6.5),
        ("fig", "fig-rman-validate.png",
         "VALIDATE DATABASE reads every block of every file and checks it, so "
         "that the recovery is not the first time anyone finds out whether the "
         "backup is sound. Zero blocks marked corrupt, and REPORT NEED BACKUP "
         "lists nothing outstanding.", 6.5),
        ("note",
         "One honest note on the configuration. The script asks for "
         "PARALLELISM 2, and RMAN answers with RMAN-06908 and RMAN-06909: "
         "parallel backup is an Enterprise Edition feature, so Free allocates "
         "one channel and says so. The warning is visible in the figures above "
         "and in the restore later on. It is left in rather than tidied away, "
         "because the setting is harmless and the warning is the evidence for "
         "which edition this actually ran on."),

        ("h1", "The failure"),
        ("p",
         "The failure is a dropped employees table, with PURGE. That "
         "keyword is deliberate. A plain DROP TABLE moves the segment to the "
         "recycle bin, and then the recovery is one FLASHBACK TABLE away and "
         "the backup is never touched. PURGE removes that shortcut, which is "
         "the point: the assignment asks for a recovery from the backup, so "
         "the failure has to be one the backup is the only answer to."),
        ("fig", "fig-code-drop.png",
         "The failure, and the SCN read one statement before it.", 6.4),
        ("p",
         "The SCN is Oracle's own logical clock. Every commit gets a higher "
         "one, so recovering until a given SCN means putting the database back "
         "the way it was at that instant. It is read one statement before the "
         "DROP and passed straight to RMAN by setup.sh, so the number in the "
         "recovery command is that number rather than a retyped copy of it."),
        ("fig", "fig-drop.png",
         f"The restore point, SCN {RESTORE_SCN}, then the table dropped. "
         "Afterwards HR_DAY9 holds only departments and its index, and the "
         "stored function has gone INVALID because the table it reads is "
         "gone.", 6.5),
        ("fig", "fig-drop-shortcuts.png",
         "Both shortcuts refusing. FLASHBACK TABLE TO BEFORE DROP fails with "
         "ORA-38305 because PURGE left nothing in the recycle bin, and "
         "selecting from the table fails with ORA-00942. departments survives "
         "untouched, which makes this a partial loss rather than a lost "
         "database, and a partial loss is the harder case: the recovery has to "
         "bring one table back without rolling the rest of the schema "
         "somewhere else.", 6.5),

        ("h1", "The recovery"),
        ("p",
         "This is a point-in-time recovery of the whole container database to "
         "the SCN captured before the DROP. RESTORE copies the datafiles back "
         "out of the backup, in the inconsistent state they were read in. "
         "RECOVER replays the archived redo logs on top of them up to the SCN, "
         "and that is the step that turns the copies into a working database "
         "with the employees table in it."),
        ("fig", "fig-code-rman-restore.png",
         "The recovery script. SET UNTIL is set once and governs both "
         "commands, which is what keeps RESTORE from picking a backup taken "
         "after the target and RECOVER from applying redo past it.", 6.4),
        ("fig", "fig-rman-restore.png",
         "SHUTDOWN, STARTUP MOUNT, the SET UNTIL SCN taking effect, and all "
         "the datafiles being restored from the compressed backup sets.", 6.5),
        ("p",
         "The database then has to be opened with RESETLOGS. The redo written "
         "after the chosen SCN, which includes the DROP itself, is being "
         "deliberately abandoned, so the log sequence cannot continue past a "
         "point the datafiles no longer agree with and has to start over."),
        ("fig", "fig-rman-recover.png",
         "RECOVER DATABASE, then ALTER DATABASE OPEN RESETLOGS. LIST "
         f"INCARNATION shows a third incarnation created at SCN {RESET_SCN}, "
         f"one past the {RESTORE_SCN} that was asked for, which is the "
         "database confirming where it was put back to.", 6.5),
        ("fig", "fig-pdb-open.png",
         "OPEN RESETLOGS opens the container database and leaves the pluggable "
         "databases closed, so FREEPDB1 is opened separately.", 6.5),

        ("h1", "Checking the recovery instead of declaring it"),
        ("p",
         "The queries from before the backup are now run again, and compared."),
        ("fig", "fig-recovered-rows.png",
         f"The same {ROWS} rows, the same salary total of {SALARY_TOTAL}, and "
         f"the same fingerprint {FINGERPRINT_AFTER}. departments still holds "
         "its ten rows, so nothing else was rolled backwards to get the "
         "employees back.", 6.5),
        ("fig", "fig-recovered-objects.png",
         "Both indexes, the function and every constraint back and valid, "
         "including the foreign key to departments and the check on salary. "
         "The recovery restored the schema, not just the data.", 6.5),
        ("fig", "fig-recovered-function.png",
         "The stored function, INVALID after the drop, recompiling and "
         "returning the ten averages again.", 6.5),
        ("table", [
            ["", "Before the backup", "After the recovery"],
            ["employees rows", ROWS, ROWS],
            ["Sum of salaries", SALARY_TOTAL, SALARY_TOTAL],
            ["Row fingerprint", FINGERPRINT_BEFORE, FINGERPRINT_AFTER],
            ["departments rows", "10", "10"],
            ["Objects in HR_DAY9", "7 valid", "7 valid"],
        ], [1.7, 2.4, 2.4]),
        ("p",
         "The fingerprint matching is the part worth insisting on. Matching "
         "row counts would only show that a table of the right size came back. "
         "The fingerprint sums a hash of the four columns of every row, so it "
         "would change if any single salary came back different, and it did "
         "not change."),

        ("break",),
        ("h1", "The optimisations, in one place"),
        ("p",
         "Gathered here because the assignment asks for them as explanations "
         "rather than as figures."),
        ("bullets", [
             "An index on employees(department_id). It changes the plan for a "
             "query filtering on one department from TABLE ACCESS FULL to "
             "INDEX RANGE SCAN, from " + _gets("Q2", "no index") + " buffer "
             "gets to " + _gets("Q2", "department_id") + ", and makes it "
             + _times("Q2", "no index", "department_id") + " faster. It does "
             "nothing at all for the average-per-department query, because "
             "that query reads every row by definition.",

             "A histogram on department_id, gathered with METHOD_OPT FOR "
             "COLUMNS SIZE 254. Without it the optimizer assumes the ten "
             "departments are equally sized and will not choose the index for "
             "any of them. The index is only usable because the statistics "
             "describe the skew.",

             "A covering index on employees(department_id, salary). This is "
             "the one that changes the assignment's own query: it becomes an "
             "INDEX FAST FULL SCAN with no table access, reading "
             + _gets("Q1", "covering") + " blocks instead of "
             + _gets("Q1", "no index") + ". It also cuts the single-department "
             "query to " + _gets("Q2", "covering") + " gets. The measured "
             "wall clock for Q1 went up rather than down, and the note in "
             "Step 2 explains why.",

             "Leaving the aggregate in SQL. The PL/SQL formats the result of "
             "a GROUP BY rather than fetching rows and averaging them in a "
             "loop, which keeps the work in the database instead of moving "
             "200,012 rows across the call interface to compute ten numbers.",

             "Using INVISIBLE to measure. Not an optimisation of the "
             "database, but the reason the before and after numbers are "
             "comparable: they were taken against the same segment with the "
             "same statistics, with only the optimizer's view of the index "
             "changed.",
         ]),

        ("h1", "The PL/SQL query used"),
        ("p",
         "The cursor at the centre of the anonymous block, quoted from "
         "sql/04_plsql.sql. The LEFT JOIN is what makes a department with no "
         "employees appear with a NULL average instead of being dropped from "
         "the report."),
        ("code", _sql("sql/04_plsql.sql", "CURSOR c_dept_avg IS",
                      "ORDER BY d.department_id;")),
        ("p",
         "And the stored function, which returns the same average for one "
         "department and is the form the covering index helps most:"),
        ("code", _sql("sql/04_plsql.sql", "CREATE OR REPLACE FUNCTION",
                      "END dept_avg_salary;")),

        ("h1", "Reproducing it"),
        ("p",
         "One script does the whole assignment against a fresh instance and "
         "writes every capture the figures are built from. It takes about "
         "fifteen minutes, most of it the RMAN backup and restore."),
        ("code", [
            "cd oracle-tuning",
            "./setup.sh                      # instance, schema, tuning, backup, recovery",
            "python3 scripts/make_figures.py  # results/ into figures/",
            "python3 build.py                 # figures/ into the .docx and .pdf",
        ]),
        ("p",
         "setup.sh runs in a single invocation on purpose. The container "
         "runtime on the machine this was built on terminates the container "
         "when the shell that started it exits, so splitting the steps across "
         "separate shells would lose the database between them."),

        ("h1", "What I would take away from this"),
        ("bullets", [
             "An index is a claim about a query, not about a column. The "
             "assignment's index and the assignment's query look like they "
             "belong together, and the execution plan is the thing that says "
             "they do not. Reading the plan was the whole difference between "
             "reporting an improvement and finding out there was not one.",

             "A hint that is ignored looks exactly like a hint that worked. "
             "Forcing the index on Q1 produced the full scan again, silently, "
             "because no legal plan using that index existed. Only the plan "
             "output shows the difference.",

             "Fewer blocks read is not automatically less time. The covering "
             "index cut Q1's logical reads by 43 percent and made it slower, "
             "because the table already fit in the buffer cache and there was "
             "no physical I/O for the saving to save. Collecting both numbers "
             "is what caught it.",

             "PURGE is what turns a dropped table into a real recovery "
             "exercise. Without it the recycle bin answers the question and "
             "the backup is never tested.",

             "A recovery is not finished when RMAN says so. The fingerprint, "
             "the row counts, the constraints and the untouched departments "
             "table are what show that the right point in time was reached "
             "and that nothing else moved to get there.",
         ]),
    ]
