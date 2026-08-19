# EastWest Bank — Hands-on Core Banking Relational Database Lab

DDL constraints, a double-entry audit ledger behind a foreign key, and atomic
fund transfers with `BEGIN` / `COMMIT` / `ROLLBACK`, on PostgreSQL 16 driven from
both `psql` and pgAdmin 4.

Deliverables are at the repository root:

- `EWB-Core-Banking-Database-Lab.docx`
- `EWB-Core-Banking-Database-Lab.pdf`

24 pages, 27 figures. 11 are real `psql` output captured into `results/`; 16 are
screenshots of pgAdmin 4 actually running the same SQL against the same cluster.
Nothing is retyped and nothing is mocked up.

## Reproducing it

```bash
./setup.sh                          # builds the cluster, runs sql/, writes results/
python3 scripts/capture_pgadmin.py  # drives pgAdmin 4, writes the fig-pga-*.png
python3 scripts/make_figures.py     # renders the psql figures from results/
python3 build.py                    # writes the .docx and .pdf
```

`setup.sh` needs root (PostgreSQL binaries plus `runuser`) and about fifteen
seconds. It tears the cluster down and rebuilds it on every run, so it is safe to
repeat.

`scripts/capture_pgadmin.py` needs a pgAdmin 4 install and Playwright's Chromium.
It starts PostgreSQL, resets pgAdmin's configuration database, registers the EWB
server, starts the pgAdmin web application, drives it with headless Chromium, and
stops everything afterwards — nothing is left running. Point it at a different
install with:

```bash
PGADMIN_HOME=/path/to/site-packages/pgadmin4 \
PGADMIN_PYTHON=/path/to/venv/bin/python \
python3 scripts/capture_pgadmin.py
```

The reset is not tidiness. pgAdmin saves the password on first connect, so
without it a second run would connect silently and the *Connect to Server*
figure — the one showing the instance is not reachable without a password —
could never be taken again.

## The database

One cluster under `/var/lib/pgsql/ewb`, one database `ewb_core`, two tables:

| Table | Enforces |
|---|---|
| `ewb_accounts` | `PRIMARY KEY (account_number)`, `NOT NULL` name, `check_positive_balance`, `check_valid_currency` |
| `ewb_transactions` | `SERIAL` primary key, `REFERENCES ewb_accounts`, `transaction_type IN ('DEBIT','CREDIT')`, `amount > 0` |

`initdb` leaves TCP connections on `trust`, which means the instance opens
without a password. For a lab about the database being the last line of defence
that is the wrong default, so `setup.sh` switches host connections to
`scram-sha-256` before the server is first started.

## Layout

```
setup.sh                     every step, in order, in one session
sql/                         the SQL, numbered in execution order
results/                     captured psql output — the source for the psql figures
scripts/capture_pgadmin.py   drives pgAdmin 4 and screenshots it
scripts/pgadmin_servers.json the server registration pgAdmin is loaded with
scripts/make_figures.py      results/  ->  the psql figures
content.py                   the text of the write-up
build.py                     content.py + figures/  ->  .docx and .pdf
```

The document writers and the terminal renderer are imported from `todo-app/`
(Day 3) rather than copied, so this directory only holds what is specific to this
lab.

## Results

Every step produced what the lab predicts:

| Step | Result |
|---|---|
| Negative opening balance | Refused, `check_positive_balance`, SQLSTATE 23514 |
| Currency `EUR` | Refused, `check_valid_currency`, SQLSTATE 23514 |
| Ledger entry for `EWB-9999` | Refused, foreign key, SQLSTATE 23503 |
| Transfer of PHP 3,000.00, committed | Juan PHP 7,000.00, Maria PHP 5,500.00 |
| Ledger after the transfer | One `DEBIT` and one `CREDIT`, netting to zero |
| Maria overdrawing by PHP 20,000.00 | Refused, transaction aborted, `ROLLBACK` |
| Maria's balance after the rollback | PHP 5,500.00, unchanged; ledger still 2 rows |

Three findings the lab does not mention, all covered in the write-up:

- The three refused inserts consumed sequence values 1–3, so the first committed
  ledger entry is `transaction_id` 4. Sequences are not transactional, so gaps in
  a `SERIAL` are normal — reconciliation that reads a gap as a lost row will
  raise false alarms.
- `CURRENT_TIMESTAMP` is the transaction's start time, not the statement's, so
  both halves of the double entry carry the same `created_at` to the microsecond.
  Correct for a ledger; wrong for anything trying to order statements within a
  transaction.
- After the constraint violation the transaction is *aborted*, not merely
  carrying a failure. Every later statement fails with "current transaction is
  aborted" until the block ends.

The write-up parses the balances and ledger ids out of `results/`, so its prose
cannot disagree with the figure beside it.

## Notes

Environment things the scripts work around, each commented where it matters:

- PostgreSQL refuses to run as root, so server commands go through
  `runuser -u postgres`.
- The `postgres` user cannot write to `/tmp` here, so
  `unix_socket_directories` is pinned to `/var/run/postgresql`.
- pgAdmin serves the Query Tool in its own iframe with no `src` attribute, so the
  editor is reached through the loaded frame's URL rather than a CSS selector.
- A server *group* opens its properties dialog on double-click, so groups are
  expanded with the keyboard and only servers are double-clicked.
- Seven levels of tree indentation truncate constraint names, and the dock
  splitter cannot be dragged from a script, so the constraint figures use
  pgAdmin's Properties tab instead.

Two presentation choices, both disclosed in the document:

- Shell prompts in the `psql` figures are shown as PowerShell, matching the
  earlier submissions in this series.
- Absolute script paths in the captures are shortened to file names. `setup.sh`
  does this to its own output so it is applied consistently.
