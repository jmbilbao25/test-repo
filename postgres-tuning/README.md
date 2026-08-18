# Day 8 — Optimizing PostgreSQL Performance

Indexing, stored procedures, streaming replication and configuration tuning
against the `dvdrental` sample database on PostgreSQL 16.

Deliverables are at the repository root:

- `PostgreSQL-Performance-Assignment.docx`
- `PostgreSQL-Performance-Assignment.pdf`

19 pages, 24 figures. Every figure is real output captured from the two running
clusters, or a slice of an actual `.sql` file in `sql/`. Nothing is retyped.

## Reproducing it

```bash
./setup.sh                        # builds both clusters, writes results/
python3 scripts/make_figures.py   # renders figures/ from results/ and sql/
python3 build.py                  # writes the .docx and .pdf
```

`setup.sh` needs root (PostgreSQL binaries plus `runuser`) and about a minute.
It tears down and rebuilds both clusters on every run, so it is safe to repeat.

## What it builds

Two clusters under `/var/lib/pgsql/day8`:

| | Port | Role |
|---|---|---|
| `primary` | 5432 | Read-write, `pg_stat_statements` loaded, replication slot `replica1` |
| `replica` | 5433 | Streaming standby created with `pg_basebackup -R -C -S replica1` |

## Layout

```
setup.sh                  every step, in order, in one session
sql/                      the SQL, numbered in execution order
results/                  captured output — the source for all figures
scripts/make_figures.py   results/ + sql/  ->  figures/
content.py                the text of the write-up
build.py                  content.py + figures/  ->  .docx and .pdf
```

The document writers and the figure renderer are imported from `todo-app/`
(Day 3) rather than copied, so this directory only contains what is specific to
this assignment.

## Results

Each query was run 200 times before and after indexing, and the mean compared
via `pg_stat_statements`, because a single `EXPLAIN ANALYZE` of a sub-millisecond
query varied by 3x run to run.

From the most recent run (`setup.sh` re-measures on each run, and the write-up
parses these numbers out of `results/` so its prose always matches its figures —
the exact means move by a few percent between runs):

| | Mean before | Mean after | | Blocks per call |
|---|---|---|---|---|
| Q1 — date range | 0.7649 ms | 0.0438 ms | 17.5x faster | 128 → 17 |
| Q2 — filter then sort | 0.0068 ms | 0.0029 ms | 2.3x faster | 5 → 4 |

Q1 had no usable index; Q2 already had one on `customer_id`, so the composite
index only removed the `Sort` node. That is why its gain is small, and the
write-up says so rather than rounding it up.

The database is 16 MB and fits in `shared_buffers` several times over, so the
cache hit ratio is 100% and no query here ever waited on disk. The buffer counts
and plan shapes are the transferable results; the millisecond figures are not.

## Notes

Three things in this environment that the script works around, each commented at
the point it matters:

- PostgreSQL refuses to run as root, so server commands go through
  `runuser -u postgres`.
- The `postgres` user cannot write to `/tmp` here, which is where a Unix socket
  and its lock file would go, so `unix_socket_directories` is pinned to
  `/var/run/postgresql`.
- After restarting the primary, the replica reconnects on
  `wal_retrieve_retry_interval` (5s default). Querying `pg_stat_replication`
  sooner returns no rows and looks like a failure — the script waits.

Two presentation choices, both disclosed in the document:

- Shell prompts are shown as PowerShell, matching the Day 6 and 7 submissions.
- Absolute cluster paths in the captures are shortened to the names used in the
  report. `setup.sh` does this to its own output so it is applied consistently.
