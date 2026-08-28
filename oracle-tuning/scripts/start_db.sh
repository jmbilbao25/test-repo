#!/usr/bin/env bash
# Creates and starts the Oracle Database Free 23ai instance this assignment
# runs against, and waits until it is open for connections.
#
#   scripts/start_db.sh
#
# sqlplus and RMAN are both driven inside the container by scripts/ora.sh, so
# no port is published: nothing outside the container needs to reach 1521.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(dirname "$HERE")

NAME=${NAME:-oradb}
IMAGE=${IMAGE:-gvenzl/oracle-free:23-faststart}
PASSWORD=${ORACLE_PASSWORD:-Day9Oracle_}

if docker exec "$NAME" true 2>/dev/null; then
    echo "container $NAME is already running"
    exit 0
fi

docker rm -f "$NAME" >/dev/null 2>&1

echo "creating the instance from $IMAGE"
docker "run" -d \
    --name "$NAME" \
    -e ORACLE_PASSWORD="$PASSWORD" \
    --shm-size=2g \
    "$IMAGE" >/dev/null || exit 1

# The faststart image opens a prebuilt database rather than running the create
# scripts, so this is normally well under two minutes.
echo -n "waiting for the instance to open"
for _ in $(seq 1 120); do
    if docker logs "$NAME" 2>&1 | grep -q "DATABASE IS READY TO USE"; then
        echo " open."
        exit 0
    fi
    echo -n .
    sleep 5
done

echo " gave up after 10 minutes. Last of the log:"
docker logs "$NAME" 2>&1 | tail -30
exit 1
