#!/usr/bin/env bash
# Runs the service under a given set of JVM flags and reports the results.
set -uo pipefail

export JAVA_HOME=/root/.local/share/mise/installs/java/21.0.2
export PATH="$JAVA_HOME/bin:$PATH"

LABEL="$1"; shift
JAR=/projects/sandbox/jvm-tuning-assignment/itemservice/target/itemservice-0.0.1-SNAPSHOT.jar
OUT=/projects/sandbox/jvm-tuning-assignment/results
mkdir -p "$OUT"
GCLOG="$OUT/${LABEL}-gc.log"
rm -f "$GCLOG"

echo "=============================================="
echo "RUN: $LABEL"
echo "FLAGS: $*"
echo "=============================================="

java "$@" -Xlog:gc:file="$GCLOG":time,level,tags -jar "$JAR" > "$OUT/${LABEL}-app.log" 2>&1 &
APP_PID=$!

for _ in $(seq 1 60); do
  if curl -sf http://localhost:8085/actuator/health > /dev/null 2>&1; then break; fi
  sleep 1
done

STARTUP=$(grep -oP 'Started ItemserviceApplication in \K[0-9.]+' "$OUT/${LABEL}-app.log" | head -1)
echo "startup_seconds=$STARTUP"

python3 /projects/sandbox/jvm-tuning-assignment/loadtest.py warmup > /dev/null 2>&1
python3 /projects/sandbox/jvm-tuning-assignment/loadtest.py measure | tee "$OUT/${LABEL}-load.txt"

echo "--- heap after load ---"
jcmd "$APP_PID" GC.heap_info 2>/dev/null | tee "$OUT/${LABEL}-heap.txt"

echo "--- gc summary ---"
PAUSE_COUNT=$(grep -c "Pause Young\|Pause Full" "$GCLOG" 2>/dev/null || echo 0)
FULL_COUNT=$(grep -c "Pause Full" "$GCLOG" 2>/dev/null || echo 0)
TOTAL_PAUSE=$(grep -oP '\d+\.\d+(?=ms)' "$GCLOG" 2>/dev/null | awk '{s+=$1} END {printf "%.1f", s+0}')
echo "gc_collections=$PAUSE_COUNT"
echo "full_gcs=$FULL_COUNT"
echo "total_gc_pause_ms=$TOTAL_PAUSE"
{ echo "startup_seconds=$STARTUP"; echo "gc_collections=$PAUSE_COUNT"; echo "full_gcs=$FULL_COUNT"; echo "total_gc_pause_ms=$TOTAL_PAUSE"; } >> "$OUT/${LABEL}-load.txt"

kill "$APP_PID" 2>/dev/null
wait "$APP_PID" 2>/dev/null
sleep 2
echo "done: $LABEL"
