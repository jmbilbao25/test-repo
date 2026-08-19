#!/usr/bin/env bash
#
# The whole lab, start to finish, in one run.
#
#   ./setup.sh
#
# Builds a PostgreSQL cluster, creates the ewb_core database, runs every script
# in sql/ in order, and writes the output of each into results/ so the figures
# in the write-up are rendered from real output rather than transcribed.
#
# Re-runnable: it tears the cluster down first.
#
# Two environment notes, both the reason for a choice below:
#   - PostgreSQL refuses to run as root, so every server command goes through
#     runuser -u postgres.
#   - the postgres user cannot write to /tmp here, which is where the Unix
#     socket and its lock file would go by default, so the socket directory is
#     pinned to /var/run/postgresql.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/results"
SQL="$HERE/sql"

BASE=/var/lib/pgsql/ewb
DATA="$BASE/data"
SOCK=/var/run/postgresql
BIN=/usr/bin
DB=ewb_core
PORT=5432

mkdir -p "$RESULTS"

pg() { runuser -u postgres -- "$@"; }
say() { echo; echo "=== $* ==="; }

# Run a script and keep stdout *and* stderr. The stderr is the point of half
# these captures: constraint violations are reported there, and those are
# exactly what Exercise 1 has to show.
capture() {
    pg "$BIN/psql" -h "$SOCK" -p "$PORT" -d "$DB" \
        -v ON_ERROR_STOP=1 -f "$SQL/$1" > "$RESULTS/$2" 2>&1
}

# Same, for the scripts whose statements are meant to be rejected. Without
# ON_ERROR_STOP psql reports each error and moves on, and a non-zero exit is
# the expected outcome rather than a failure of the run.
capture_failing() {
    pg "$BIN/psql" -h "$SOCK" -p "$PORT" -d "$DB" \
        -f "$SQL/$1" > "$RESULTS/$2" 2>&1 || true
}

# ------------------------------------------------------------------- teardown

say "teardown"
if [ -f "$DATA/postmaster.pid" ]; then
    pg "$BIN/pg_ctl" -D "$DATA" -m immediate stop >/dev/null 2>&1 || true
fi
rm -rf "$BASE"
mkdir -p "$BASE" "$SOCK"
chown postgres:postgres "$BASE" "$SOCK"

# ---------------------------------------------------------------- the cluster

say "initdb, and create $DB"
pg "$BIN/initdb" -D "$DATA" -E UTF8 --locale=C >/dev/null

cat >> "$DATA/postgresql.conf" <<CONF

# --- added by setup.sh ---
port = $PORT
unix_socket_directories = '$SOCK'
listen_addresses = '127.0.0.1'
logging_collector = off
CONF

# pgAdmin connects over TCP, and initdb leaves host connections on trust. A lab
# that teaches the database as the last line of defence should not be reachable
# without a password, so TCP is switched to scram-sha-256.
sed -i "s|^host\(.*\)127.0.0.1/32.*trust|host\1127.0.0.1/32            scram-sha-256|" \
    "$DATA/pg_hba.conf"

pg "$BIN/pg_ctl" -D "$DATA" -l "$BASE/server.log" start >/dev/null
sleep 2

pg "$BIN/createdb" -h "$SOCK" -p "$PORT" "$DB"
pg "$BIN/psql" -h "$SOCK" -p "$PORT" -d "$DB" -q \
    -c "ALTER USER postgres WITH PASSWORD 'ewb_lab_2026';"

{
    "$BIN/psql" --version
    echo
    echo "$ initdb -D data -E UTF8"
    echo "$ pg_ctl -D data start"
    echo "$ createdb $DB"
    echo
    pg "$BIN/psql" -h "$SOCK" -p "$PORT" -d "$DB" -c \
       "SELECT current_database()          AS database,
               current_user                AS connected_as,
               current_setting('port')     AS port,
               current_setting('server_version') AS version;"
} > "$RESULTS/setup.txt" 2>&1

# ------------------------------------------------------------------ exercise 1

say "exercise 1: DDL and the CHECK constraints"
capture         01_create_accounts.sql   create_accounts.txt
capture_failing 02_constraint_tests.sql  constraint_tests.txt

# ------------------------------------------------------------------ exercise 2

say "exercise 2: the ledger, and relational queries"
capture         03_seed_accounts.sql     seed_accounts.txt
capture         04_create_transactions.sql create_transactions.txt
capture_failing 05_fk_test.sql           fk_test.txt
capture         06_queries.sql           queries.txt

# ------------------------------------------------------------------ exercise 3

say "exercise 3: BEGIN / COMMIT / ROLLBACK"
# psql echoes BEGIN, UPDATE 1, INSERT 0 1 and COMMIT one per statement, which is
# the tag for each step of the transfer. -a echoes the statement that produced
# each tag, so the figure reads as a transcript rather than a column of tags.
pg "$BIN/psql" -h "$SOCK" -p "$PORT" -d "$DB" -a \
    -v ON_ERROR_STOP=1 -f "$SQL/07_transfer_commit.sql" \
    > "$RESULTS/transfer_commit.txt" 2>&1
capture         08_verify_transfer.sql   verify_transfer.txt

pg "$BIN/psql" -h "$SOCK" -p "$PORT" -d "$DB" -a \
    -f "$SQL/09_overdraw_rollback.sql" \
    > "$RESULTS/overdraw_rollback.txt" 2>&1 || true
capture         10_verify_rollback.sql   verify_rollback.txt

# ------------------------------------------------------------------------ done

say "stopping the cluster"
pg "$BIN/pg_ctl" -D "$DATA" -m fast stop >/dev/null

# Absolute paths are noise in a screenshot; show the scripts by name, which is
# how the write-up refers to them.
python3 - "$RESULTS" "$SQL" <<'PY'
import os, sys
results, sqldir = sys.argv[1], sys.argv[2]
for name in os.listdir(results):
    path = os.path.join(results, name)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    new = text.replace(sqldir + "/", "")
    if new != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
PY

say "done"
wc -l "$RESULTS"/*.txt
