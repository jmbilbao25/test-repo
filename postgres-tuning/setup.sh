#!/usr/bin/env bash
#
# Everything this assignment does, start to finish, in one run.
#
#   ./setup.sh
#
# Builds a primary cluster on port 5432 and a streaming replica on 5433, loads
# the dvdrental sample database, and writes the output of every step to
# results/ so the figures are built from real output rather than transcribed.
#
# Re-runnable: it tears down both clusters first.
#
# Two environment notes, both the reason for a choice below:
#   - PostgreSQL refuses to run as root, so every server command goes through
#     runuser -u postgres.
#   - The postgres user cannot write to /tmp here, which is where a Unix socket
#     and its lock file would go by default, so the socket directory is pinned
#     to /var/run/postgresql.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/results"
SQL="$HERE/sql"

# The sample database. postgresqltutorial.com serves the same archive but blocks
# non-browser clients; this mirror is the identical dvdrental.zip.
DVDRENTAL_URL="${DVDRENTAL_URL:-https://neon.com/postgresqltutorial/dvdrental.zip}"

BASE=/var/lib/pgsql/day8
PRIMARY="$BASE/primary"
REPLICA="$BASE/replica"
SOCK=/var/run/postgresql
BIN=/usr/bin

mkdir -p "$RESULTS"

# --------------------------------------------------------------- helpers

pg() { runuser -u postgres -- "$@"; }

# Run a psql script against a port and save stdout *and* stderr. The stderr
# matters: RAISE NOTICE and error messages go there, and those are exactly what
# the Step 3 figures need to show.
capture() {
    local port="$1" file="$2" out="$3"
    pg "$BIN/psql" -h "$SOCK" -p "$port" -d exampledb \
        -v ON_ERROR_STOP=1 -f "$SQL/$file" > "$RESULTS/$out" 2>&1
}

say() { echo; echo "=== $* ==="; }

# --------------------------------------------------------------- teardown

say "teardown"
for dir in "$PRIMARY" "$REPLICA"; do
    if [ -f "$dir/postmaster.pid" ]; then
        pg "$BIN/pg_ctl" -D "$dir" -m immediate stop >/dev/null 2>&1 || true
    fi
done
rm -rf "$BASE"
mkdir -p "$BASE" "$SOCK"
chown postgres:postgres "$BASE" "$SOCK"

# --------------------------------------------------------------- step 1

say "step 1: initdb primary"
pg "$BIN/initdb" -D "$PRIMARY" -E UTF8 --locale=C >/dev/null

# pg_stat_statements has to be preloaded at startup, so it is configured before
# the server is ever started. It is what Step 2 uses to find the busiest
# queries instead of guessing at them.
cat >> "$PRIMARY/postgresql.conf" <<CONF

# --- added by setup.sh ---
port = 5432
unix_socket_directories = '$SOCK'
listen_addresses = '127.0.0.1'
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = 'all'
logging_collector = off
CONF

echo "host replication replicator 127.0.0.1/32 trust" >> "$PRIMARY/pg_hba.conf"

pg "$BIN/pg_ctl" -D "$PRIMARY" -l "$BASE/primary.log" start >/dev/null
sleep 2

say "step 1: restore dvdrental into exampledb"
if [ ! -f "$BASE/dvdrental.tar" ]; then
    curl -sSL -o "$BASE/dvdrental.zip" "$DVDRENTAL_URL"
    ( cd "$BASE" && unzip -o -q dvdrental.zip )
fi
chown postgres:postgres "$BASE/dvdrental.tar"

pg "$BIN/createdb" -h "$SOCK" -p 5432 exampledb
pg "$BIN/pg_restore" -h "$SOCK" -p 5432 -d exampledb "$BASE/dvdrental.tar"
pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -q \
    -c "CREATE EXTENSION pg_stat_statements;" \
    -c "CREATE ROLE replicator WITH REPLICATION LOGIN;" \
    -c "ANALYZE;"

{
    "$BIN/psql" --version
    echo
    echo "$ pg_ctl -D primary start"
    echo "$ createdb exampledb"
    echo "$ pg_restore -d exampledb dvdrental.tar"
    echo
    pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -c \
       "SELECT current_database() AS database, pg_size_pretty(pg_database_size(current_database())) AS size;"
} > "$RESULTS/setup.txt" 2>&1

capture 5432 01_schema.sql        schema.txt
capture 5432 02_payment_table.sql payment_table.txt

# --------------------------------------------------------------- step 2

say "step 2: generate a workload, then look for index candidates"
# Run the two queries repeatedly so pg_stat_statements has real call counts and
# pg_stat_user_tables has real sequential-scan counts to report.
pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -q <<'SQL' >/dev/null
SELECT pg_stat_statements_reset();
SELECT pg_stat_reset();
DO $$
BEGIN
    FOR i IN 1..40 LOOP
        PERFORM customer_id, amount, payment_date FROM payment
         WHERE payment_date >= '2007-02-15' AND payment_date < '2007-02-16';
        PERFORM payment_id, amount, payment_date FROM payment
         WHERE customer_id = 341 ORDER BY payment_date DESC LIMIT 10;
    END LOOP;
END $$;
SQL

capture 5432 03_candidates.sql candidates.txt

say "step 2: EXPLAIN before"
capture 5432 04_explain_before.sql explain_before.txt
capture 5432 11_benchmark.sql      benchmark_before.txt

say "step 2: create indexes"
capture 5432 05_indexes.sql indexes.txt

say "step 2: EXPLAIN after"
capture 5432 06_explain_after.sql explain_after.txt
capture 5432 11_benchmark.sql      benchmark_after.txt

# --------------------------------------------------------------- step 3

say "step 3: function and procedure"
capture 5432 07_functions.sql functions.txt
# The test script deliberately triggers three failures, so a non-zero exit is
# the expected outcome here and must not abort the run.
pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -f "$SQL/08_functions_test.sql" \
    > "$RESULTS/functions_test.txt" 2>&1 || true

# --------------------------------------------------------------- step 4

say "step 4: pg_basebackup to build the replica"
pg "$BIN/pg_basebackup" \
    -D "$REPLICA" \
    -d "host=127.0.0.1 port=5432 user=replicator application_name=replica1" \
    -X stream -C -S replica1 -R -P -v \
    > "$RESULTS/basebackup.txt" 2>&1

cat >> "$REPLICA/postgresql.conf" <<CONF

# --- added by setup.sh: the replica shares the host, so it needs its own port ---
port = 5433
unix_socket_directories = '$SOCK'
CONF

pg "$BIN/pg_ctl" -D "$REPLICA" -l "$BASE/replica.log" start >/dev/null
sleep 3

{
    echo "$ pg_ctl -D replica start        # replica listening on 5433"
    echo
    echo "--- is this server a replica? ---"
    pg "$BIN/psql" -h "$SOCK" -p 5433 -d exampledb -c \
       "SELECT pg_is_in_recovery() AS in_recovery, pg_last_wal_replay_lsn() AS replayed;"
} > "$RESULTS/replica_state.txt" 2>&1

capture 5432 10_replication_check.sql replication.txt

say "step 4: prove replication actually streams"
{
    echo "--- on the PRIMARY (5432): insert a row ---"
    pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -c \
       "INSERT INTO category (name) VALUES ('Replication Test') RETURNING category_id, name;"
    echo
    echo "--- on the REPLICA (5433): the row arrived ---"
    pg "$BIN/psql" -h "$SOCK" -p 5433 -d exampledb -c \
       "SELECT category_id, name FROM category WHERE name = 'Replication Test';"
    echo
    echo "--- on the REPLICA (5433): try to write to it ---"
    pg "$BIN/psql" -h "$SOCK" -p 5433 -d exampledb -c \
       "INSERT INTO category (name) VALUES ('Written On Replica');" || true
} > "$RESULTS/replication_test.txt" 2>&1

# --------------------------------------------------------------- step 5

say "step 5: monitoring views"
capture 5432 09_stats.sql stats.txt

say "step 5: tuning"
# Size the two parameters the assignment names from the actual machine, rather
# than pasting numbers from a blog post.
TOTAL_MB=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 ))
SHARED_MB=$(( TOTAL_MB / 4 ))          # 25% of RAM
CACHE_MB=$(( TOTAL_MB * 3 / 4 ))       # 75% of RAM

{
    echo "detected RAM: ${TOTAL_MB} MB across $(nproc) cores"
    echo "target: shared_buffers ${SHARED_MB}MB (25%), effective_cache_size ${CACHE_MB}MB (75%)"
    echo
    echo "--- defaults ---"
    pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -f "$SQL/12_settings.sql"
} > "$RESULTS/tuning_before.txt" 2>&1

pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -q \
    -c "ALTER SYSTEM SET shared_buffers = '${SHARED_MB}MB';" \
    -c "ALTER SYSTEM SET effective_cache_size = '${CACHE_MB}MB';" \
    -c "ALTER SYSTEM SET work_mem = '32MB';" \
    -c "ALTER SYSTEM SET maintenance_work_mem = '512MB';" \
    -c "ALTER SYSTEM SET random_page_cost = 1.1;"

# shared_buffers allocates shared memory at startup, so it needs a restart, not
# a reload. The others would have taken a reload.
pg "$BIN/pg_ctl" -D "$PRIMARY" -m fast restart -l "$BASE/primary.log" >/dev/null
# The replica retries its connection on wal_retrieve_retry_interval, which
# defaults to 5s. Waiting less than that and then querying pg_stat_replication
# reports zero rows and makes it look as though replication broke.
sleep 12

{
    echo "$ psql -c \"ALTER SYSTEM SET shared_buffers = '${SHARED_MB}MB'\"   # +4 more"
    echo "$ pg_ctl -D primary -m fast restart        # shared_buffers needs a restart"
    echo
    echo "--- after ---"
    pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -f "$SQL/12_settings.sql"
    echo "--- the replica reconnected on its own after the restart ---"
    pg "$BIN/psql" -h "$SOCK" -p 5432 -d exampledb -c \
       "SELECT application_name, state, sync_state FROM pg_stat_replication;"
} > "$RESULTS/tuning_after.txt" 2>&1

say "step 5: re-run Q2 on the tuned server"
capture 5432 06_explain_after.sql explain_tuned.txt

# --------------------------------------------------------------- done

say "stopping both clusters"
pg "$BIN/pg_ctl" -D "$REPLICA" -m fast stop >/dev/null
pg "$BIN/pg_ctl" -D "$PRIMARY" -m fast stop >/dev/null

# The absolute cluster paths are noise in a screenshot; show them as the short
# names used throughout the report.
python3 - "$RESULTS" "$BASE" "$SQL" <<'PY'
import os, sys
results, base, sqldir = sys.argv[1], sys.argv[2], sys.argv[3]
for name in os.listdir(results):
    path = os.path.join(results, name)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    new = (text.replace(sqldir + "/", "")     # psql:08_foo.sql:6: not the full path
               .replace(base + "/", "")
               .replace(base, "."))
    if new != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
PY

say "done"
wc -l "$RESULTS"/*.txt
