#!/usr/bin/env bash
# Runs the whole assignment: builds the four applications, starts them in
# dependency order, exercises service discovery and configuration management,
# takes the browser screenshots, and captures every step into results/.
#
#   ./run.sh
#
# Everything happens in one invocation on purpose. The four services are child
# processes of this script, so splitting the steps across separate shells would
# lose them in between; the same constraint shaped the Day 9 setup script.
#
# About seven minutes, most of it Maven and four JVM startups.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"

RESULTS="$HERE/results"
LOGS="$HERE/logs"
export CONFIG_REPO="$HERE/config-repo"
# Pinned rather than inherited: the pom targets Java 21, and a report that says
# 21 while the JVM was 25 would be wrong in a way nobody would notice.
JAVA21=${JAVA21:-/root/.local/share/mise/installs/java/21.0.2}
[ -d "$JAVA21" ] && export JAVA_HOME="$JAVA21"
export PATH="$JAVA_HOME/bin:$PATH"

mkdir -p "$RESULTS" "$LOGS"
PIDS=()

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
note() { printf '    %s\n' "$*"; }

cleanup() {
    step "shutting down"
    for pid in "${PIDS[@]:-}"; do
        [ -n "$pid" ] && kill "$pid" 2>/dev/null
    done
    sleep 2
    for pid in "${PIDS[@]:-}"; do
        [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
    done
    # Put the configuration file back, so a second run starts from the same
    # place as the first.
    if [ -f "$RESULTS/.product-service.yml.orig" ]; then
        cp "$RESULTS/.product-service.yml.orig" "$CONFIG_REPO/product-service.yml"
        rm -f "$RESULTS/.product-service.yml.orig"
        note "config-repo/product-service.yml restored"
    fi
}
trap cleanup EXIT

# Start a jar in the background and wait for its health endpoint.
# $1 module, $2 port, $3 friendly name
# Any arguments after the third are passed through to the JVM, which is how the
# restart later on comes back on a different port.
start_service() {
    local module=$1 port=$2 name=$3
    shift 3
    local jar="$HERE/$module/target/$module-1.0.0.jar"
    [ -f "$jar" ] || { echo "missing $jar"; exit 1; }

    java -jar "$jar" "$@" >>"$LOGS/$module.log" 2>&1 &
    local pid=$!
    PIDS+=("$pid")

    printf '    starting %-16s pid %-7s port %s' "$name" "$pid" "$port"
    for _ in $(seq 1 90); do
        if curl -fsS "http://localhost:$port/actuator/health" >/dev/null 2>&1; then
            printf '  up\n'
            return 0
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            printf '  DIED\n'
            tail -25 "$LOGS/$module.log"
            exit 1
        fi
        printf '.'
        sleep 2
    done
    printf '  TIMED OUT\n'
    tail -25 "$LOGS/$module.log"
    exit 1
}

# curl into a results file, with the request echoed above the response.
cap() {
    local out=$1 label=$2
    shift 2
    {
        echo "=== $label ==="
        echo "\$ curl $*"
        curl -sS -w '\n[HTTP %{http_code}]\n' "$@" 2>&1
        echo
    } >>"$RESULTS/$out"
}

# ----------------------------------------------------------------- step 1

step "Step 1: build the four applications"
mvn -q -B package -DskipTests >"$RESULTS/build.txt" 2>&1
rc=$?
{
    echo "=== mvn -B package -DskipTests ==="
    echo "Java:  $(java -version 2>&1 | head -1)"
    echo "Maven: $(mvn -v 2>&1 | head -1)"
    echo
    echo "Spring Boot 3.4.1, Spring Cloud 2024.0.0 (see pom.xml)"
    echo
    for m in config-server eureka-server product-service order-service; do
        printf '%-16s %s\n' "$m" \
            "$(ls -la "$m/target/$m-1.0.0.jar" 2>/dev/null | awk '{print $5" bytes"}')"
    done
    echo
    echo "[mvn exit $rc]"
} >"$RESULTS/build_summary.txt"
[ $rc -eq 0 ] || { cat "$RESULTS/build.txt" | tail -30; exit 1; }
note "-> results/build_summary.txt"

# ----------------------------------------------------------------- step 3 first

# The Config Server has to be up before the two services, because they ask it
# for their configuration during startup rather than after it.
step "Config Server first: the two services cannot start configured without it"
start_service config-server 8888 "config-server"

rm -f "$RESULTS/config_server.txt"
cap config_server.txt "the shared configuration, as the server resolves it" \
    "http://localhost:8888/application/default"
cap config_server.txt "product-service configuration" \
    "http://localhost:8888/product-service/default"
cap config_server.txt "order-service configuration" \
    "http://localhost:8888/order-service/default"
cap config_server.txt "the same file served as plain YAML" \
    "http://localhost:8888/product-service-default.yml"
note "-> results/config_server.txt"

# ----------------------------------------------------------------- step 2

step "Step 2: the Eureka registry"
start_service eureka-server 8761 "eureka-server"

rm -f "$RESULTS/eureka.txt"
cap eureka.txt "the registry, empty apart from itself" \
    -H "Accept: application/json" "http://localhost:8761/eureka/apps"

step "registering the two services"
start_service product-service 9081 "product-service"
start_service order-service 9082 "order-service"

note "waiting for both leases to appear in the registry"
sleep 12

cap eureka.txt "both services registered" \
    -H "Accept: application/json" "http://localhost:8761/eureka/apps"
cap eureka.txt "the product-service lease in detail" \
    -H "Accept: application/json" "http://localhost:8761/eureka/apps/PRODUCT-SERVICE"
note "-> results/eureka.txt"

# What the startup logs say about the two things being demonstrated.
{
    echo "=== product-service: fetching configuration from the Config Server ==="
    grep -iE "Fetching config|config server|Located property source|profiles are active" \
        "$LOGS/product-service.log" | head -6
    echo
    echo "=== product-service: registering with Eureka ==="
    grep -iE "DiscoveryClient.*register|registration status|Tomcat started|Started ProductServiceApplication" \
        "$LOGS/product-service.log" | head -8
    echo
    echo "=== order-service: fetching configuration from the Config Server ==="
    grep -iE "Fetching config|config server|Located property source|profiles are active" \
        "$LOGS/order-service.log" | head -6
    echo
    echo "=== order-service: registering with Eureka ==="
    grep -iE "DiscoveryClient.*register|registration status|Tomcat started|Started OrderServiceApplication" \
        "$LOGS/order-service.log" | head -8
} >"$RESULTS/startup_logs.txt"
note "-> results/startup_logs.txt"

# ----------------------------------------------------------------- step 4

step "Step 4: the two services working together"
rm -f "$RESULTS/product_api.txt" "$RESULTS/order_api.txt"

cap product_api.txt "the catalogue, wrapped in configured values" \
    "http://localhost:9081/products"
cap product_api.txt "one product, the endpoint order-service calls" \
    "http://localhost:9081/products/3"
cap product_api.txt "everything the Config Server told this service" \
    "http://localhost:9081/products/config"

cap order_api.txt "what order-service can see in the registry" \
    "http://localhost:9082/orders/discovery"
cap order_api.txt "placing an order: 1 x 27-inch Monitor" \
    -X POST -H "Content-Type: application/json" \
    -d '{"productId":3,"quantity":1}' "http://localhost:9082/orders"
cap order_api.txt "placing a second order below the free shipping threshold" \
    -X POST -H "Content-Type: application/json" \
    -d '{"productId":1,"quantity":1}' "http://localhost:9082/orders"
cap order_api.txt "a quantity above the configured maximum is refused" \
    -X POST -H "Content-Type: application/json" \
    -d '{"productId":1,"quantity":25}' "http://localhost:9082/orders"
cap order_api.txt "both orders" "http://localhost:9082/orders"
note "-> results/product_api.txt, results/order_api.txt"

cap without_discovery.txt "the same URL without the load balancer" \
    "http://localhost:9082/orders/without-discovery/3"
note "-> results/without_discovery.txt"

step "browser screenshots: registry, config server, both services"
python3 scripts/capture_ui.py registered

# ----------------------------------------------------------------- step 3 refresh

step "Step 3: change a configuration value and pick it up without a restart"
cp "$CONFIG_REPO/product-service.yml" "$RESULTS/.product-service.yml.orig"

rm -f "$RESULTS/refresh.txt"
{
    echo "=== before: the value the running service is using ==="
    curl -sS http://localhost:9081/products/config
    echo
} >>"$RESULTS/refresh.txt"

# The edit. sed rather than a here-doc so the diff below is small and readable.
sed -i \
    -e 's/^  featured-message: .*/  featured-message: MID-YEAR SALE - up to 40% off peripherals/' \
    -e 's/^  page-size: .*/  page-size: 4/' \
    -e 's/^  low-stock-threshold: .*/  low-stock-threshold: 8/' \
    "$CONFIG_REPO/product-service.yml"

{
    echo "=== the edit ==="
    echo "\$ diff -u config-repo/product-service.yml"
    diff -u "$RESULTS/.product-service.yml.orig" \
            "$CONFIG_REPO/product-service.yml" \
        | sed -e 's#.*\.product-service\.yml\.orig#--- product-service.yml (before)#' \
              -e 's#.*config-repo/product-service\.yml#+++ product-service.yml (after)#'
    echo
    echo "=== the Config Server serves the new value immediately ==="
    curl -sS http://localhost:8888/product-service/default \
        | grep -A6 '"source"'
    echo
    echo "=== but the running service is still on the old one ==="
    curl -sS http://localhost:9081/products/config
    echo
    echo "=== POST /actuator/refresh ==="
    echo "\$ curl -X POST http://localhost:9081/actuator/refresh"
    curl -sS -X POST http://localhost:9081/actuator/refresh
    echo
    echo
    echo "=== and now it is not ==="
    curl -sS http://localhost:9081/products/config
    echo
    echo "=== the change reaches behaviour, not just the config endpoint ==="
    echo "\$ curl http://localhost:9081/products/low-stock"
    curl -sS http://localhost:9081/products/low-stock
    echo
} >>"$RESULTS/refresh.txt"
note "-> results/refresh.txt"

step "browser screenshots: the refreshed configuration"
python3 scripts/capture_ui.py refreshed

# ----------------------------------------------------------------- deregistration

step "Step 2 continued: deregistering a service"
rm -f "$RESULTS/deregister.txt"

PRODUCT_PID=""
for pid in "${PIDS[@]}"; do
    if ps -p "$pid" -o args= 2>/dev/null | grep -q product-service; then
        PRODUCT_PID=$pid
    fi
done

{
    echo "=== product-service is registered, and order-service can use it ==="
    curl -sS http://localhost:9082/orders/discovery
    echo
    echo "=== shutting product-service down through the actuator ==="
    echo "\$ curl -X POST http://localhost:9081/actuator/shutdown"
    echo "(not exposed; SIGTERM to pid $PRODUCT_PID instead, which triggers the"
    echo " same DiscoveryClient shutdown hook and an explicit DELETE to Eureka)"
} >>"$RESULTS/deregister.txt"

kill "$PRODUCT_PID" 2>/dev/null
note "sent SIGTERM to product-service (pid $PRODUCT_PID)"
sleep 3

{
    echo
    echo "=== product-service says goodbye on the way out ==="
    grep -iE "Unregistering|DiscoveryClient.*shutdown|Shutting down DiscoveryClient|deregister" \
        "$LOGS/product-service.log" | tail -6
    echo
} >>"$RESULTS/deregister.txt"

note "waiting for the registry to drop the lease"
sleep 12

{
    echo "=== the registry no longer lists PRODUCT-SERVICE ==="
    echo "\$ curl -H 'Accept: application/json' http://localhost:8761/eureka/apps"
    curl -sS -H "Accept: application/json" http://localhost:8761/eureka/apps
    echo
    echo
    echo "=== order-service sees an empty instance list ==="
    curl -sS http://localhost:9082/orders/discovery
    echo
    echo "=== and placing an order now fails, with a reason ==="
    echo "\$ curl -X POST -d '{\"productId\":3,\"quantity\":1}' http://localhost:9082/orders"
    curl -sS -w '\n[HTTP %{http_code}]\n' -X POST \
        -H "Content-Type: application/json" \
        -d '{"productId":3,"quantity":1}' http://localhost:9082/orders
    echo
    echo "=== the orders already placed are unaffected ==="
    curl -sS http://localhost:9082/orders | head -20
    echo
} >>"$RESULTS/deregister.txt"
note "-> results/deregister.txt"

step "browser screenshots: the registry with product-service gone"
python3 scripts/capture_ui.py deregistered

# ----------------------------------------------------------------- re-register

step "Step 2 continued: bringing it back on a different port"
# 9091, not the 9081 it was on before. Nothing in order-service is changed or
# restarted. If it can still place an order afterwards, the lookup is real:
# order-service never knew the port in the first place.
start_service product-service 9091 "product-service" --server.port=9091
note "waiting for the lease to reappear"
sleep 12

{
    echo "=== it came back on port 9091, not the 9081 it had before ==="
    echo "\$ curl http://localhost:9091/products/3"
    curl -sS http://localhost:9091/products/3
    echo
    echo
    echo "=== product-service registers again, on the same logical name ==="
    echo "\$ curl -H 'Accept: application/json' http://localhost:8761/eureka/apps/PRODUCT-SERVICE"
    curl -sS -H "Accept: application/json" \
        http://localhost:8761/eureka/apps/PRODUCT-SERVICE
    echo
    echo
    echo "=== order-service finds it again, at the new port, with no restart ==="
    echo "=== and no configuration change of its own                       ==="
    curl -sS http://localhost:9082/orders/discovery
    echo
    echo "=== and orders work again ==="
    curl -sS -w '\n[HTTP %{http_code}]\n' -X POST \
        -H "Content-Type: application/json" \
        -d '{"productId":6,"quantity":2}' http://localhost:9082/orders
    echo
} >"$RESULTS/reregister.txt"
note "-> results/reregister.txt"

step "browser screenshots: the registry restored"
python3 scripts/capture_ui.py restored

# ----------------------------------------------------------------- summary

step "done"
ls -1 "$RESULTS" | grep -v '^\.'
echo
ls -1 "$HERE/screenshots" 2>/dev/null
