#!/usr/bin/env bash
# Runs the whole assignment against a real Oracle Database Free 23ai instance and
# captures every step into results/.
#
#   ./setup.sh
#
# Everything happens in one invocation on purpose. sqlplus and RMAN are driven
# inside the container, and each step's output is written to results/ verbatim;
# scripts/make_figures.py then renders those files, so no figure in the write-up
# can say something the database did not.
#
# Roughly fifteen minutes, most of it the RMAN backup and restore.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"

NAME=${NAME:-oradb}
RESULTS="$HERE/results"
PASSWORD=${ORACLE_PASSWORD:-Day9Oracle_}

mkdir -p "$RESULTS"

# ---------------------------------------------------------------- plumbing

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

# sqlplus / as sysdba inside the container. $1 is the results file to write,
# $2 the container to connect into (CDB$ROOT or FREEPDB1), $3 the script.
sqlp() {
    local out=$1 container=$2 script=$3
    local prelude=""
    if [ "$container" != "root" ]; then
        prelude="ALTER SESSION SET CONTAINER = $container;"
    fi
    docker exec -i "$NAME" bash -lc "
        export ORACLE_SID=FREE
        sqlplus -s -L / as sysdba <<'SQLEOF'
WHENEVER OSERROR EXIT 9
SET ECHO OFF
SET FEEDBACK OFF
SET TAB OFF
$prelude
@/tmp/lab/$script
EXIT
SQLEOF" >"$RESULTS/$out" 2>&1
    local rc=$?
    if grep -qE '^(ORA-|SP2-|PLS-)' "$RESULTS/$out"; then
        printf '    \033[1;33mOracle reported:\033[0m\n'
        grep -E '^(ORA-|SP2-|PLS-)' "$RESULTS/$out" | sort -u | sed 's/^/      /'
    fi
    echo "    -> results/$out ($(wc -l <"$RESULTS/$out") lines, rc=$rc)"
}

# rman target / inside the container. $1 results file, $2 cmdfile, rest passed
# to RMAN as substitution variables.
rman_run() {
    local out=$1 script=$2
    shift 2
    local using=""
    [ $# -gt 0 ] && using="using $*"
    docker exec -i "$NAME" bash -lc "
        export ORACLE_SID=FREE
        rman target / cmdfile=/tmp/lab/$script $using" >"$RESULTS/$out" 2>&1
    local rc=$?
    if grep -qE '^RMAN-|^ORA-' "$RESULTS/$out"; then
        printf '    \033[1;33mRMAN reported:\033[0m\n'
        grep -E '^RMAN-|^ORA-' "$RESULTS/$out" | sort -u | head -8 | sed 's/^/      /'
    fi
    echo "    -> results/$out ($(wc -l <"$RESULTS/$out") lines, rc=$rc)"
}

# ------------------------------------------------------- the instance itself

step "Introduction: create the Oracle Database instance"
./scripts/start_db.sh || exit 1

# The entrypoint narrates the whole instance startup on stdout. That narration is
# the evidence for the first figure, so it is kept rather than watched.
docker logs "$NAME" 2>&1 | grep -v '^time=' >"$RESULTS/db_startup.txt"
echo "    -> results/db_startup.txt ($(wc -l <"$RESULTS/db_startup.txt") lines)"

# The scripts go under /lab inside the container. /tmp is used as the landing
# spot because it already exists and is writable by every user in the image,
# which saves a chown that podman would need root in the container for.
docker exec "$NAME" rm -rf /tmp/lab
docker exec "$NAME" mkdir -p /tmp/lab
docker cp "$HERE/sql" "$NAME:/tmp/lab/sql" >/dev/null
docker cp "$HERE/rman" "$NAME:/tmp/lab/rman" >/dev/null
docker exec "$NAME" mkdir -p /opt/oracle/oradata/FRA

sqlp instance.txt root sql/01_instance.sql

# ------------------------------------------------------------------- step 1

step "Step 1: tables, rows and the index"
sqlp schema.txt FREEPDB1 sql/02_schema.sql
sqlp index.txt   FREEPDB1 sql/03_index.sql

# ------------------------------------------------------------------- step 2

step "Step 2: the PL/SQL, and the plans before and after"
sqlp plsql.txt          FREEPDB1 sql/04_plsql.sql
sqlp explain_small.txt  FREEPDB1 sql/05_explain_small.sql
sqlp scale.txt          FREEPDB1 sql/06_scale.sql
sqlp explain_before.txt FREEPDB1 sql/07_explain_before.sql
sqlp explain_after.txt  FREEPDB1 sql/08_explain_after.sql
sqlp covering.txt       FREEPDB1 sql/09_covering.sql
sqlp benchmark.txt      FREEPDB1 sql/10_benchmark.sql

# ------------------------------------------------------------------- step 3

step "Step 3: ARCHIVELOG, then the RMAN backup"
sqlp archivelog.txt root sql/11_archivelog.sql
sqlp before_backup.txt FREEPDB1 sql/12_before_backup.sql

rman_run rman_backup.txt rman/01_backup.rman

step "Step 3: the failure"
sqlp drop.txt FREEPDB1 sql/13_drop.sql

SCN=$(grep -o 'RESTORE_POINT_SCN=[0-9]*' "$RESULTS/drop.txt" | head -1 | cut -d= -f2)
if [ -z "$SCN" ]; then
    echo "    could not read the restore point out of results/drop.txt; stopping"
    exit 1
fi
echo "$SCN" >"$RESULTS/restore_point.txt"
echo "    recovering to SCN $SCN"

step "Step 3: the recovery"
rman_run rman_restore.txt rman/02_restore.rman "$SCN"

# OPEN RESETLOGS opens the container database; the pluggable databases inside it
# are left closed and have to be opened separately.
docker exec -i "$NAME" bash -lc "
    export ORACLE_SID=FREE
    sqlplus -s -L / as sysdba <<'SQLEOF'
SET FEEDBACK ON
ALTER PLUGGABLE DATABASE ALL OPEN;
EXIT
SQLEOF" >"$RESULTS/pdb_open.txt" 2>&1
echo "    -> results/pdb_open.txt"

sqlp after_recovery.txt FREEPDB1 sql/14_after_recovery.sql

# ------------------------------------------------------------------- summary

step "done"
printf '%s\n' "recovered to SCN $SCN"
ls -1 "$RESULTS"
