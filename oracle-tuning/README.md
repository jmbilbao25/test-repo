# Day 9: Optimizing and Recovering an Oracle Database

The write-up is **[Oracle-Optimization-Recovery-Assignment.docx](../Oracle-Optimization-Recovery-Assignment.docx)**,
with a **[PDF copy](../Oracle-Optimization-Recovery-Assignment.pdf)** — 43 pages,
49 figures.

Everything ran against a real instance: Oracle AI Database 26ai Free Release
23.26.2.0.0, from the `gvenzl/oracle-free` container image.

## What is here

| Path | What it is |
| --- | --- |
| `setup.sh` | Runs the whole assignment and captures every step into `results/` |
| `scripts/start_db.sh` | Creates and opens the database instance |
| `sql/01..14` | Each step, in order, as a runnable script |
| `rman/01_backup.rman` | The full backup |
| `rman/02_restore.rman` | The point-in-time recovery |
| `results/` | Raw captured output — the source for every figure |
| `scripts/make_figures.py` | Renders `results/` and `sql/` into `figures/` |
| `build.py` | Renders the figures and `content.py` into the .docx and .pdf |

## Reproducing it

```bash
cd oracle-tuning
./setup.sh                       # instance, schema, tuning, backup, recovery
python3 scripts/make_figures.py  # results/ into figures/
python3 build.py                 # figures/ into the .docx and .pdf
```

About fifteen minutes, most of it the RMAN backup and restore.

Two things about the environment, both of which shaped the scripts:

- `setup.sh` does everything in one invocation because the container runtime
  here kills the container when the shell that started it exits.
- The `-slim` image variants have the `rman` binary stripped out, so
  `start_db.sh` uses `gvenzl/oracle-free:23-faststart`.

## The results

Two queries, on 200,012 employees across ten departments:

- **Q1** — `AVG(salary) GROUP BY department_id`, the query the assignment asks for
- **Q2** — `AVG(salary) WHERE department_id = 10`, one department of 501 people

| | No index | `department_id` | `(department_id, salary)` |
| --- | --- | --- | --- |
| Q1 buffer gets | 1,006 | 1,006 | 569 |
| Q1 ms per run | 9.600 | 9.400 | 13.000 |
| Q2 buffer gets | 1,004 | 505 | 4 |
| Q2 ms per run | 2.140 | 0.200 | 0.020 |

**The index the assignment asks for does not speed up the query the assignment
asks for.** Q1 averages every salary, so it reads every row either way, and the
plan is `TABLE ACCESS FULL` before and after — same plan hash value, same 1,006
buffer gets. Hinting the index onto Q1 produces the full scan again, silently,
because no legal plan using it exists.

It is a large win for Q2: `TABLE ACCESS FULL` becomes `INDEX RANGE SCAN`, 1,004
gets become 505, and the query is 10.7x faster. That only works because a
`FOR COLUMNS SIZE 254` histogram tells the optimizer department 10 is 0.25% of
the table rather than a tenth of it.

What does help Q1 is a covering index on `(department_id, salary)`. It holds both
columns Q1 reads, so the plan becomes `INDEX FAST FULL SCAN` with no table access
at all — 43% fewer blocks. Note the wall clock went **up**: at this size the
table already fits in the buffer cache, so there is no physical I/O for the block
saving to save, and only the extra CPU is left.

Measuring used `ALTER INDEX ... INVISIBLE` rather than dropping the index, so
before and after were taken against an identical segment with identical
statistics.

## Backup and recovery

`NOARCHIVELOG` to `ARCHIVELOG` first, then `BACKUP AS COMPRESSED BACKUPSET
DATABASE PLUS ARCHIVELOG`, then `VALIDATE DATABASE` — zero blocks corrupt.

The failure is `DROP TABLE employees CASCADE CONSTRAINTS PURGE`. `PURGE` is the
point: without it the recycle bin answers the question and the backup is never
tested. `FLASHBACK TABLE ... TO BEFORE DROP` fails with ORA-38305, and the
recovery has to come from the backup.

Recovery is a point-in-time restore of the container database to the SCN read one
statement before the `DROP`, which `setup.sh` passes to RMAN so the number in the
command is not a retyped copy:

```
SET UNTIL SCN <scn>;   RESTORE DATABASE;   RECOVER DATABASE;
ALTER DATABASE OPEN RESETLOGS;
```

Checked rather than declared:

| | Before the backup | After the recovery |
| --- | --- | --- |
| employees rows | 200,012 | 200,012 |
| Sum of salaries | 15,018,179,225.12 | 15,018,179,225.12 |
| Row fingerprint | 430599086091596 | 430599086091596 |
| departments rows | 10 | 10 |

The fingerprint sums a hash of all four columns of every row, so matching row
counts alone would not have been enough — it would change if any single salary
came back different. `departments` is untouched throughout, which is what shows
nothing else was rolled backwards to get the employees back.

One RMAN note left in deliberately: `PARALLELISM 2` draws RMAN-06908 and
RMAN-06909, because parallel backup is an Enterprise Edition feature. Free
allocates one channel and says so.
