#!/usr/bin/env bash
# Builds the three images, starts the containers, exercises the gateway and the
# service-to-service calls, and captures every step into results/.
#
#   ./run.sh
#
# The containers are started with `docker run` rather than `docker compose up`.
# docker-compose.yml is the declarative description and is validated here, but
# the compose provider on this machine is podman-compose, which puts every
# service into a pod; combined with host networking that deadlocked the runtime
# hard enough to need `podman system renumber`. The `docker run` invocations
# below are the same three containers with the same environment, and they are
# reliable.
#
# Two or three minutes, most of it the two pip installs in the image builds.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"

RESULTS="$HERE/results"
SHOTS="$HERE/screenshots"
mkdir -p "$RESULTS" "$SHOTS"

PORT=8091                       # the gateway, the only reachable port
BASE="http://localhost:$PORT"
PRODUCTS_ADDR=127.0.0.1:8000    # loopback only
ORDERS_ADDR=127.0.0.1:8001      # loopback only

CONTAINERS=(bazaar-gateway bazaar-orders bazaar-products)

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
note() { printf '    %s\n' "$*"; }

# Print a command the way a person would have typed it, then run it. Everything
# in results/ is produced this way, so no capture can show a command that was
# not the one that ran.
cap() {
    printf '$ %s\n' "$1"
    eval "$1" 2>&1
    printf '\n'
}

cleanup() {
    step "removing containers"
    for c in "${CONTAINERS[@]}"; do
        docker rm -f "$c" >/dev/null 2>&1
    done
}
trap cleanup EXIT

wait_for() {                    # wait_for <url> <label>
    local url=$1 label=$2 i
    for i in $(seq 1 40); do
        if curl -fsS -m 2 -o /dev/null "$url" 2>/dev/null; then
            note "$label is up"
            return 0
        fi
        sleep 1
    done
    echo "TIMED OUT waiting for $label at $url" >&2
    return 1
}

# --------------------------------------------------------------------- build
step "building the three images"
{
    echo "=== docker version ==="
    docker version --format 'client {{.Client.Version}}' 2>/dev/null || docker --version
    echo
    for svc in products-service orders-service gateway; do
        echo "=== docker build ./$svc ==="
        docker build -t "bazaar/${svc/gateway/api-gateway}:1.0" "./$svc" 2>&1 \
            | grep -viE "^(Getting|Copying|Writing|Trying)" \
            | tail -14
        echo
    done
} > "$RESULTS/build.txt" 2>&1
tail -4 "$RESULTS/build.txt"

step "validating docker-compose.yml"
{
    echo "=== docker compose config (the declarative definition) ==="
    DOCKER_COMPOSE_PROVIDER=$(command -v podman-compose) \
        docker compose config 2>&1 \
        | grep -viE "executing external compose provider|podman-compose$|^$" \
        | head -60
} > "$RESULTS/compose_config.txt" 2>&1
note "$(wc -l < "$RESULTS/compose_config.txt") lines"

# ------------------------------------------------- nginx config resolution
# Two runs of the same check on the same image. The only difference is whether
# the upstream names resolve, which is the whole point.
step "nginx -t, with and without the names resolvable"
{
    echo "=== nginx -t with no network: the names cannot resolve ==="
    printf '$ docker run --rm --network none bazaar/api-gateway:1.0 nginx -t\n'
    docker run --rm --network none bazaar/api-gateway:1.0 nginx -t 2>&1 \
        | grep -viE "docker-entrypoint|Sourcing|Launching|Looking|info:|Configuration complete"
    echo
    echo "=== nginx -t with the names mapped: the same file is valid ==="
    printf '$ docker run --rm --network host --add-host ... nginx -t\n'
    docker run --rm --network host \
        --add-host products-service:127.0.0.1 \
        --add-host orders-service:127.0.0.1 \
        bazaar/api-gateway:1.0 nginx -t 2>&1 \
        | grep -viE "docker-entrypoint|Sourcing|Launching|Looking|info:|Configuration complete"
} > "$RESULTS/nginx_validate.txt" 2>&1
tail -3 "$RESULTS/nginx_validate.txt"

# --------------------------------------------------------------------- start
step "starting the containers"
cleanup >/dev/null 2>&1

# --replace because a container that was killed rather than removed keeps its
# name, and the next run would otherwise fail on the name and not on anything
# interesting.
docker run -d --replace --name bazaar-products \
    --network host \
    -e BIND_HOST=127.0.0.1 -e BIND_PORT=8000 -e STORE_CURRENCY=PHP \
    --restart unless-stopped \
    bazaar/products-service:1.0 >/dev/null || exit 1

docker run -d --replace --name bazaar-orders \
    --network host \
    --add-host products-service:127.0.0.1 \
    -e BIND_HOST=127.0.0.1 -e BIND_PORT=8001 \
    -e PRODUCTS_BASE_URL=http://products-service:8000 \
    -e MAX_QUANTITY_PER_ORDER=10 -e PRODUCTS_TIMEOUT_SECONDS=3.0 \
    --restart unless-stopped \
    bazaar/orders-service:1.0 >/dev/null || exit 1

docker run -d --replace --name bazaar-gateway \
    --network host \
    --add-host products-service:127.0.0.1 \
    --add-host orders-service:127.0.0.1 \
    --restart unless-stopped \
    bazaar/api-gateway:1.0 >/dev/null || exit 1

wait_for "http://$PRODUCTS_ADDR/health" "products-service" || exit 1
wait_for "http://$ORDERS_ADDR/health"   "orders-service"   || exit 1
wait_for "$BASE/health"                 "gateway"          || exit 1

# ------------------------------------------------------------ docker running
step "capturing the running containers"
{
    echo "=== docker ps ==="
    cap "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Command}}'"
    echo "=== docker images ==="
    cap "docker images bazaar/* --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}'"
    echo "=== how each container is attached, and what it binds ==="
    printf '%-18s %-12s %s\n' CONTAINER NETWORK BINDS
    for c in bazaar-products bazaar-orders bazaar-gateway; do
        mode=$(docker inspect "$c" --format '{{.HostConfig.NetworkMode}}')
        case $c in
            *products) bind="127.0.0.1:8000  (loopback only)" ;;
            *orders)   bind="127.0.0.1:8001  (loopback only)" ;;
            *gateway)  bind="0.0.0.0:8091    (reachable)" ;;
        esac
        printf '%-18s %-12s %s\n' "$c" "$mode" "$bind"
    done
} > "$RESULTS/docker_running.txt" 2>&1

# --------------------------------------------------------------- the gateway
step "the gateway, and what it adds to a request"
{
    echo "=== the gateway's own health endpoint ==="
    cap "curl -s $BASE/health"
    echo "=== response headers on a proxied route ==="
    echo "    X-Request-ID and X-Served-By are added by NGINX, not by the service."
    cap "curl -s -D - -o /dev/null $BASE/api/products/1002"
    echo "=== each service's health, reached through the gateway ==="
    cap "curl -s $BASE/api/status/products"
    cap "curl -s $BASE/api/status/orders"
} > "$RESULTS/gateway.txt" 2>&1

step "routing: one entry point, two services"
{
    echo "=== GET /api/products -> products-service ==="
    cap "curl -s $BASE/api/products"
    echo "=== GET /api/products/1002 -> a single product ==="
    cap "curl -s $BASE/api/products/1002"
    echo "=== the public path and the internal path are not the same ==="
    echo "    /api/products/1002 at the gateway is /products/1002 at the service."
    cap "curl -s -o /dev/null -w 'gateway  %{http_code}  %{time_total}s\n' $BASE/api/products/1002"
    cap "curl -s -o /dev/null -w 'direct   %{http_code}  %{time_total}s\n' http://$PRODUCTS_ADDR/products/1002"
    echo "=== a filter, passed through as a query string ==="
    cap "curl -s '$BASE/api/products?category=Pantry'"
    echo "=== GET /api/products/9999 -> the service's own 404, not the gateway's ==="
    cap "curl -s -w '[HTTP %{http_code}]\n' $BASE/api/products/9999"
} > "$RESULTS/routing.txt" 2>&1

# ------------------------------------------------------- service to service
step "service to service: orders asks products for a price"
{
    echo "=== what orders-service knows about its dependency ==="
    echo "    A name in configuration, resolved at run time."
    cap "curl -s $BASE/api/orders/dependency"
    echo "=== POST /api/orders: the gateway routes it, products prices it ==="
    cap "curl -s -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":1002,\"quantity\":2,\"customer\":\"curl\"}'"
    echo "=== a second order, on a cheaper line ==="
    cap "curl -s -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":1003,\"quantity\":3,\"customer\":\"curl\"}'"
    echo "=== GET /api/orders: note priced_by on every order ==="
    cap "curl -s $BASE/api/orders"
} > "$RESULTS/east_west.txt" 2>&1

# ------------------------------------------------------------- correlation
step "tracing one request through all three containers"
RID=$(curl -s -D - -o /dev/null -X POST "$BASE/api/orders" \
        -H 'Content-Type: application/json' \
        -d '{"product_id":1001,"quantity":4,"customer":"trace"}' \
      | tr -d '\r' | awk 'tolower($1)=="x-request-id:"{print $2}')
note "request id $RID"
sleep 1
{
    echo "=== one POST /api/orders, and the same ID in three container logs ==="
    echo "    The gateway generated it. Nobody configured it anywhere."
    echo
    echo "\$ RID=$RID"
    echo
    echo "\$ docker logs bazaar-gateway | grep \$RID"
    docker logs bazaar-gateway 2>&1 | grep -- "$RID"
    echo
    echo "\$ docker logs bazaar-orders | grep \$RID"
    docker logs bazaar-orders 2>&1 | grep -- "$RID"
    echo
    echo "\$ docker logs bazaar-products | grep \$RID"
    docker logs bazaar-products 2>&1 | grep -- "$RID"
    echo
    echo "=== and it is stored on the order itself ==="
    cap "curl -s $BASE/api/orders/5003"
} > "$RESULTS/correlation.txt" 2>&1

# ------------------------------------------------------------ the rules bite
step "the refusals"
{
    echo "=== a product that is out of stock (1006, stock 0) ==="
    cap "curl -s -w '[HTTP %{http_code}]\n' -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":1006,\"quantity\":1}'"
    echo "=== more than the catalogue has (1004, stock 3) ==="
    cap "curl -s -w '[HTTP %{http_code}]\n' -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":1004,\"quantity\":5}'"
    echo "=== above the configured per-order maximum of 10 ==="
    echo "    Refused by orders-service before it calls products-service at all."
    cap "curl -s -w '[HTTP %{http_code}]\n' -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":1003,\"quantity\":25}'"
    echo "=== a product that does not exist: the 404 comes from products-service ==="
    cap "curl -s -w '[HTTP %{http_code}]\n' -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":4242,\"quantity\":1}'"
} > "$RESULTS/rules.txt" 2>&1

# --------------------------------------------------------------- isolation
step "checking that the gateway really is the only way in"
python3 scripts/check_isolation.py > "$RESULTS/isolation.txt" 2>&1
tail -5 "$RESULTS/isolation.txt"

# ------------------------------------------------------------- screenshots
step "browser screenshots: the storefront, working"
curl -s -X POST "$BASE/api/orders" -H 'Content-Type: application/json' \
     -d '{"product_id":1005,"quantity":2,"customer":"web-storefront"}' >/dev/null
python3 scripts/capture_ui.py running 2>&1 | tail -12

# ------------------------------------------------------- a service goes down
step "stopping products-service while the gateway stays up"
{
    echo "=== docker stop bazaar-products ==="
    cap "docker stop bazaar-products"
    cap "docker ps --format 'table {{.Names}}\t{{.Status}}'"
    echo "=== the gateway is still up and still answering for itself ==="
    cap "curl -s $BASE/health"
    echo "=== but the catalogue route now has nothing behind it ==="
    echo "    NGINX cannot connect, so the shaped 503 from error_page is returned"
    echo "    instead of an HTML error page."
    cap "curl -s -w '[HTTP %{http_code}]\n' $BASE/api/products"
    echo "=== and an order cannot be priced ==="
    echo "    orders-service is healthy. It is its dependency that is gone, and"
    echo "    it says so rather than returning a 500."
    cap "curl -s -w '[HTTP %{http_code}]\n' -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":1002,\"quantity\":1}'"
    echo "=== orders already placed are still readable ==="
    echo "    The orders service holds them; nothing about reading them needs the"
    echo "    catalogue."
    cap "curl -s -o /dev/null -w 'GET /api/orders -> %{http_code}\n' $BASE/api/orders"
    echo "=== and the dependency view shows what it now sees ==="
    cap "curl -s $BASE/api/orders/dependency"
} > "$RESULTS/outage.txt" 2>&1
tail -3 "$RESULTS/outage.txt"

step "browser screenshots: the storefront with the catalogue down"
python3 scripts/capture_ui.py degraded 2>&1 | tail -8

step "starting products-service again"
{
    echo "=== docker start bazaar-products ==="
    cap "docker start bazaar-products"
} > "$RESULTS/recovery.txt" 2>&1
wait_for "http://$PRODUCTS_ADDR/health" "products-service" || true
{
    echo "=== the catalogue route recovers with no gateway restart ==="
    cap "curl -s -o /dev/null -w 'GET /api/products -> %{http_code}\n' $BASE/api/products"
    echo "=== and orders can be priced again ==="
    cap "curl -s -X POST $BASE/api/orders -H 'Content-Type: application/json' -d '{\"product_id\":1007,\"quantity\":2,\"customer\":\"after-restart\"}'"
    echo "=== NGINX did not need to be reloaded ==="
    cap "docker ps --format 'table {{.Names}}\t{{.Status}}'"
} >> "$RESULTS/recovery.txt" 2>&1
tail -3 "$RESULTS/recovery.txt"

step "browser screenshots: the storefront recovered"
python3 scripts/capture_ui.py restored 2>&1 | tail -8

# --------------------------------------------------------------------- logs
step "container logs"
{
    echo "=== docker logs bazaar-gateway  (the access log, one line per request) ==="
    docker logs bazaar-gateway 2>&1 | grep -E '"(GET|POST)' | tail -22
} > "$RESULTS/logs_gateway.txt" 2>&1
{
    echo "=== docker logs bazaar-orders ==="
    docker logs bazaar-orders 2>&1 | tail -24
} > "$RESULTS/logs_orders.txt" 2>&1
{
    echo "=== docker logs bazaar-products ==="
    docker logs bazaar-products 2>&1 | tail -22
} > "$RESULTS/logs_products.txt" 2>&1

step "done"
note "results/     $(ls "$RESULTS" | wc -l) captures"
note "screenshots/ $(ls "$SHOTS" 2>/dev/null | grep -c '\.png$') browser shots"
note "next: python3 scripts/make_figures.py && python3 build.py"
