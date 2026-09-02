"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment. Numbers quoted in the prose are read back out of results/, the same
source the figures are built from, so the sentences and the screenshots cannot
end up disagreeing with each other.
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

TITLE = ("Designing an API Gateway and Service Communication "
         "for a Simple E-commerce Application")
DAY = "Day 14 Hands-on Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "September 2, 2026"


def _read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read()


def _find(pattern: str, capture: str, group: int = 1) -> str:
    m = re.search(pattern, _read(capture))
    if not m:
        raise SystemExit(f"{pattern!r} not found in {capture}")
    return m.group(group)


RID = _find(r"RID=([0-9a-f]+)", "correlation.txt")
GATEWAY_MS = _find(r"gateway\s+200\s+([\d.]+)s", "routing.txt")
DIRECT_MS = _find(r"direct\s+200\s+([\d.]+)s", "routing.txt")
ROUTABLE_IP = _find(r"routable\s+(\d+\.\d+\.\d+\.\d+)", "isolation.txt")
GW_SIZE = _find(r"api-gateway\s+1\.0\s+\w+\s+([\d.]+ MB)", "docker_running.txt")
PROD_SIZE = _find(r"products-service\s+1\.0\s+\w+\s+([\d.]+ MB)",
                  "docker_running.txt")
REVENUE = _find(r'"revenue": ([\d.]+)', "east_west.txt")

GATEWAY_MS = f"{float(GATEWAY_MS) * 1000:.1f}"
DIRECT_MS = f"{float(DIRECT_MS) * 1000:.1f}"


def blocks() -> list[tuple]:
    B: list[tuple] = []
    h1 = lambda t: B.append(("h1", t))                       # noqa: E731
    p = lambda t: B.append(("p", t))                         # noqa: E731
    note = lambda t: B.append(("note", t))                   # noqa: E731
    bullets = lambda ls: B.append(("bullets", ls))           # noqa: E731
    table = lambda rows, w: B.append(("table", rows, w))     # noqa: E731
    fig = lambda n, c, w=6.3: B.append(("fig", n, c, w))     # noqa: E731
    brk = lambda: B.append(("break",))                       # noqa: E731

    # ----------------------------------------------------- introduction
    h1("Introduction")
    p("Bilbao Bazaar is a small online shop split into two microservices. One "
      "owns the catalogue: what is for sale, what it costs, how many are left. "
      "The other takes orders. They are separate programs in separate "
      "containers, and neither can read the other's data.")
    p("That split is why the assignment needs a gateway. A customer should not "
      "have to know that products live on one port and orders on another, and "
      "the browser should not be making requests to two different origins to "
      "draw one page. So a third container sits in front of both and is the only "
      "thing anybody talks to. It is an NGINX instance, and it does the routing.")
    p("There is a second kind of traffic that has nothing to do with the "
      "customer. When an order arrives, the orders service does not know what "
      "anything costs, so it has to ask the catalogue. That call goes sideways, "
      "service to service, and it turned out to be the more interesting half of "
      "the design.")
    p("Everything runs on Docker: three images, three containers, one compose "
      "file. run.sh builds, starts, exercises and tears down the whole stack in "
      "one invocation and writes every command and response into results/. The "
      "figures below are rendered from those captures and from real Chromium "
      "screenshots, so nothing here is retyped by hand.")

    table([
        ["Container", "Image", "Listens on", "What it does"],
        ["bazaar-gateway", "bazaar/api-gateway:1.0", "0.0.0.0:8091",
         "NGINX. Routes /api/... to both services, serves the storefront."],
        ["bazaar-products", "bazaar/products-service:1.0", "127.0.0.1:8000",
         "The catalogue. Products, prices, stock. Calls nobody."],
        ["bazaar-orders", "bazaar/orders-service:1.0", "127.0.0.1:8001",
         "Takes orders. Prices every line through products-service."],
    ], [1.35, 1.75, 1.15, 2.2])

    p("The two services are FastAPI applications on Python 3.12. The gateway is "
      f"nginx 1.27 on Alpine, which is why its image is {GW_SIZE} against "
      f"{PROD_SIZE} for a service carrying a Python runtime.")

    note("A note on the networking, because it is not the shape a textbook would "
         "draw. The intended compose file put all three containers on a bridge "
         "network and published only the gateway's port. That does not run on "
         "the machine I built this on: the container runtime is Podman without "
         "CAP_NET_ADMIN, so it allocates addresses on the bridge and then "
         "programs no routes to them. All three containers share the host "
         "network namespace instead, and the isolation is done with bind "
         "addresses. The last section explains how I worked that out.")

    # ----------------------------------------------------- the services
    h1("The two microservices")
    p("The catalogue is eight products with an id, a name, a category, a price "
      "in pesos and a stock count, held in memory. Two of the rows are chosen "
      "rather than invented: product 1006 has zero stock and product 1004 has "
      "three units, so there is something for the order rules to refuse. "
      "Without them every request succeeds and the validation code never "
      "appears in a screenshot.")
    fig("fig-code-products-catalogue.png",
        "The catalogue. Two rows exist to make the order rules do something "
        "visible")
    p("The endpoint the orders service depends on is the single-product one. It "
      "returns a 404 for an id that is not there, and that 404 is what makes an "
      "order for a nonexistent product fail with a 404 rather than a 500.")
    fig("fig-code-products-endpoint.png",
        "GET /products/{id}, the endpoint the orders service calls")
    p("The orders service holds no prices at all. It takes a product id and a "
      "quantity, asks the catalogue what that product costs, checks the answer "
      "against its own rules, and only then writes an order. The address it asks "
      "is configuration, never a literal:")
    fig("fig-code-orders-config.png",
        "The dependency and the two limits, all arriving as environment "
        "variables")

    # ================================================= TASK 1
    brk()
    h1("Task 1: Designing the API gateway")
    p("I used NGINX rather than a managed gateway because the whole design then "
      "fits in one file I can show, and because it runs in a container next to "
      "the services instead of in somebody's cloud console.")
    p("The first decision is how the services are named. Each gets an upstream "
      "block, so the address appears exactly once and the routes below refer to "
      "it by name. Adding a second replica of the catalogue is one more line "
      "inside the block and no change anywhere else.")
    fig("fig-code-nginx-upstreams.png",
        "The two upstreams, and the proxy defaults that apply to both")
    p("The headers under them are the gateway's responsibility. X-Forwarded-For "
      "and X-Forwarded-Proto are there so a service can still tell who is asking "
      "after the hop. X-Request-ID is the one that matters for Task 2: NGINX "
      "generates a fresh value per request and the services log it. The timeouts "
      "are deliberately short, so a service that has stopped answering becomes a "
      "fast error rather than a client that hangs.")
    p("The routes are prefixes. Because proxy_pass is given a URI as well as a "
      "host, the matched prefix is replaced rather than appended, so the public "
      "path and the internal path are free to differ.")
    fig("fig-code-nginx-routes.png",
        "Path-based routing. /api/products/1002 reaches the service as "
        "/products/1002")

    table([
        ["Public route", "Goes to", "Methods"],
        ["/api/products", "products-service:8000/products", "GET"],
        ["/api/products/{id}", "products-service:8000/products/{id}", "GET"],
        ["/api/orders", "orders-service:8001/orders", "GET, POST"],
        ["/api/orders/{id}", "orders-service:8001/orders/{id}", "GET"],
        ["/api/orders/dependency", "orders-service:8001/orders/dependency",
         "GET"],
        ["/api/status/products", "products-service:8000/health", "GET"],
        ["/api/status/orders", "orders-service:8001/health", "GET"],
        ["/health", "answered by the gateway itself", "GET"],
        ["/", "the storefront, served from disk", "GET"],
    ], [1.9, 3.1, 1.4])

    p("The last two rows are why the storefront is worth having. The page and "
      "the API sit on one origin, so the JavaScript fetches /api/products as a "
      "same-origin request and there is no CORS configuration anywhere in this "
      "project. That is a real benefit of a gateway and it is easy to miss, "
      "because what it produces is the absence of work.")
    p("Finally, a gateway that returns NGINX's default HTML error page is a "
      "strange thing for a JSON API to do, so failures NGINX generates itself "
      "are shaped into JSON:")
    fig("fig-code-nginx-errors.png",
        "A JSON 503 for failures NGINX produces itself")
    p("proxy_intercept_errors is left off, which is the default but worth "
      "stating, because it is what lets a 409 or a 503 that a service produced "
      "on purpose reach the client exactly as the service wrote it. Only errors "
      "NGINX generates get replaced.")

    h1("Building it, and a check I had to remove")
    fig("fig-build.png", "docker build, three images from three Dockerfiles",
        6.1)
    fig("fig-code-gateway-dockerfile.png",
        "The gateway image, and the comment explaining what is missing from it")
    p("What is missing there is a validation step. I had written RUN nginx -t "
      "into the Dockerfile, on the reasoning that a bad directive should fail "
      "the build rather than produce an image that crash-loops. The build then "
      "failed on a file that was completely valid, because nginx -t resolves "
      "every name in an upstream block, and during a build there is no network "
      "and no products-service to resolve.")
    p("Running the same check on the same image twice, with nothing different "
      "but whether the names resolve, shows exactly that:")
    fig("fig-nginx-validate.png",
        "The same image and the same config file. Only name resolution differs")
    p("That is worth more than the build-time check I lost. NGINX resolves "
      "upstream names once, at startup, which is why the containers must exist "
      "before the gateway starts and why compose declares depends_on. It also "
      "comes back in the very last test.")
    fig("fig-code-compose-services.png",
        "The two services in docker-compose.yml")
    fig("fig-code-compose-gateway.png",
        "The gateway. The names it needs are mapped here, not written into "
        "nginx.conf")
    p("With the images built, all three containers come up and the gateway is "
      "the only one with a reachable address:")
    fig("fig-docker-running.png",
        "docker ps, the three images, and what each container binds")
    p("The gateway answers for itself without touching either service, which is "
      "what makes it useful to poll:")
    fig("fig-gateway-health.png", "GET /health, answered by NGINX", 5.6)
    fig("shot-gateway-health.png", "The same endpoint in a browser", 5.4)
    p("And on a proxied route, the two headers the gateway adds come back with "
      "the response:")
    fig("fig-gateway-headers.png",
        "X-Request-ID and X-Served-By are added by the gateway; x-service came "
        "from the service")

    note("Getting those headers onto every route took two attempts. NGINX does "
         "not merge add_header across levels: the moment a location block "
         "declares one of its own, every add_header inherited from the server "
         "block is dropped. My /health block set Content-Type that way, and "
         "/health came back with no X-Request-ID while every proxied route had "
         "one. The fix is to set the type with default_type and repeat the two "
         "headers inside the block, which is why they appear twice in the file.")

    fig("fig-gateway-status.png",
        "Both services' health, reached through the gateway under a tidier path "
        "than they use internally")

    # ================================================= TASK 2
    brk()
    h1("Task 2: Service communication patterns")
    p("There are two directions of traffic here and they are not the same "
      "problem.")
    bullets([
        "North-south: a client to a service, through the gateway. The client "
        "knows one address and one set of paths. This is what Task 1 built.",
        "East-west: the orders service to the products service. No client is "
        "involved and no browser is waiting. This call does not go through the "
        "gateway at all.",
    ])
    p("I chose synchronous REST over HTTP for the east-west call rather than a "
      "message queue, and the reason is the nature of the work: the orders "
      "service cannot write an order until it knows the price. There is nothing "
      "to do while it waits, so a queue would add a broker to run and a reply to "
      "correlate without removing any waiting. A queue earns its place when the "
      "caller does not need the answer to continue, and pricing is the opposite "
      "of that.")
    p("The internal call also skips the gateway on purpose. Routing sideways "
      "traffic through the front door adds a hop to every internal request and "
      "makes the gateway a single point of failure for calls no client is "
      "waiting on.")
    fig("fig-code-orders-fetch.png",
        "The east-west call. Every failure mode becomes a status code the caller "
        "can act on")
    p("Most of that function is error translation, and that is the point of it. "
      "If an httpx exception were allowed to escape, a stopped catalogue would "
      "surface to the customer as a 500, which says only that something broke. "
      "Instead a refused connection becomes a 503 naming the dependency, a slow "
      "answer becomes a 504 with the timeout that was exceeded, and the "
      "catalogue's own 404 is passed along as a 404.")
    fig("fig-code-orders-place.png",
        "Placing an order: the local rule first, then the call, then the stock "
        "checks")
    p("The quantity limit is checked before the call, because there is no reason "
      "to ask the catalogue about an order that is already invalid. The stock "
      "checks have to come after it, because stock is the catalogue's data and "
      "the orders service has no copy of it.")

    h1("Where the address comes from")
    p("Nothing in the orders service image knows where the catalogue runs. It "
      "reads a name from PRODUCTS_BASE_URL and the name is resolved when the "
      "call is made. The service will report what it currently sees:")
    fig("fig-dependency.png", "GET /api/orders/dependency, through the gateway")
    fig("shot-api-dependency.png", "The same view in a browser", 6.0)
    p("The configured value is a name, the address underneath it was resolved at "
      "run time, and the health probe was made just now. On the bridge network "
      "this was meant to run on, that address would have been the catalogue "
      "container's address, resolved by the runtime's DNS. Here it resolves to "
      "loopback. The mechanism is the same either way: the code holds a name and "
      "the environment supplies the mapping.")

    h1("An order, end to end")
    p("A POST to /api/orders goes through both patterns in one request. The "
      "gateway routes it north-south to the orders service; the orders service "
      "calls the catalogue east-west to price it; the order comes back with a "
      "total the orders service never had the data to compute on its own.")
    fig("fig-east-west-order.png",
        "One POST /api/orders. unit_price and priced_by both came from the other "
        "service")

    h1("Following one request through three containers")
    p("This is the part I would keep if I had to throw the rest away. The "
      "gateway stamps every incoming request with an X-Request-ID. The orders "
      "service logs it and forwards it on its own outbound call. The products "
      "service logs it again, with who called. So one customer request leaves "
      "the same identifier in three separate container logs, and grep is enough "
      "to reconstruct the whole path.")
    fig("fig-correlation.png",
        f"One POST /api/orders. The id {RID[:12]} appears in all three logs")
    p("Read top to bottom that is the entire journey of one request: NGINX "
      "accepted it and sent it to 127.0.0.1:8001, the orders service asked "
      "products-service for a price on product 1001, the catalogue answered 200 "
      "and recorded that the caller was orders-service, and the order was "
      "confirmed. Nobody configured the identifier. NGINX generated it, and the "
      "only reason it travels is one proxy_set_header line plus the header the "
      "orders service copies onto its outbound call.")
    p("It is also stored on the order, so a support question about one order can "
      "be turned back into the log lines that produced it:")
    fig("fig-order-rid.png", "The same id, recorded on the order", 5.8)
    p("The gateway's access log is worth a look on its own, because "
      "$upstream_addr records which container actually served each request. That "
      "is the difference between believing the routing works and being able to "
      "show it.")
    fig("fig-logs-gateway.png",
        "The gateway access log. The upstream column shows :8000 or :8001 per "
        "request")
    fig("fig-logs-orders.png",
        "The orders service log. Every outbound call is logged before it is made")
    fig("fig-logs-products.png",
        "The catalogue log. from= distinguishes the gateway from the orders "
        "service")

    # ================================================= TASK 3
    brk()
    h1("Task 3: Testing the gateway and the service communication")
    p("I tested with curl for the API and a real browser for the storefront. All "
      "of it goes through http://localhost:8091, and no test addresses a service "
      "directly apart from one comparison where that is the point.")

    h1("Routing")
    fig("fig-routing-one.png",
        "GET /api/products/1002. served_by names the service that answered", 5.9)
    p("The same product fetched twice, once through the gateway and once straight "
      f"at the service on loopback: {GATEWAY_MS} ms through the gateway against "
      f"{DIRECT_MS} ms direct.")
    fig("fig-routing-hops.png", "The extra hop, measured", 6.1)
    p("The gateway came out marginally faster, which is not a real result. Both "
      "numbers are around a millisecond and a millisecond is mostly noise on "
      "loopback; run it again and they swap. What it does establish is that the "
      "extra hop costs nothing measurable at this scale, which is the useful "
      "half of the question.")
    fig("fig-routing-filter.png",
        "A query string, passed through untouched, so filtering stays the "
        "service's job", 6.1)
    fig("fig-routing-404.png",
        "An id that is not in the catalogue gives the service's own 404, not a "
        "generic gateway error", 6.1)

    h1("The refusals")
    p("Four requests that should not succeed. The interesting thing is not that "
      "they fail but that each fails at the layer that owns the rule, with a "
      "status code that says which:")
    table([
        ["Request", "Status", "Refused by", "Why"],
        ["1006, qty 1", "409", "orders-service",
         "Stock is zero. Needs the catalogue's answer first."],
        ["1004, qty 5", "409", "orders-service",
         "Only three in stock. Also needs the catalogue."],
        ["1003, qty 25", "422", "orders-service",
         "Over the configured maximum of 10. No call is made."],
        ["4242, qty 1", "404", "products-service",
         "No such product. The 404 travels back through two hops."],
    ], [1.25, 0.75, 1.5, 2.9])
    fig("fig-rules-stock.png",
        "Two refusals that both required the catalogue to answer first")
    fig("fig-rules-limits.png",
        "A purely local rule, and a 404 that travelled back from the other "
        "service")
    p("The 422 shows the boundary clearly. The quantity limit is the orders "
      "service's own configuration, so it refuses without ever contacting the "
      "catalogue, and the products service log has no line for that request.")

    h1("The storefront")
    fig("fig-code-storefront-call.png",
        "The only place the storefront talks to the API. Every path is relative")
    fig("shot-storefront.png",
        "The storefront in Chromium. Eight products from products-service, "
        "orders from orders-service, and the gateway's own headers along the "
        "bottom")
    p("Everything on that page arrived through the gateway. The three pills top "
      "right are live polls of /health, /api/status/products and "
      "/api/status/orders. The catalogue is a GET /api/products. Each Place "
      "order button is a POST /api/orders, so every row in the orders table is a "
      "service-to-service call that has already happened: the priced by column "
      f"names products-service, and the {REVENUE} peso total was computed from "
      "prices the orders service had to ask for.")
    p("Product 1006 is the one to look at. It shows Out of stock with its button "
      "disabled, and the storefront was not told which product that is. It "
      "renders whatever stock the catalogue reports.")
    fig("shot-api-products.png",
        "GET /api/products in the browser, through the gateway", 6.0)
    fig("shot-api-orders.png",
        "GET /api/orders. Every order carries the id of the request that created "
        "it", 6.0)

    h1("Is the gateway really the only way in?")
    p("The claim that the services are unreachable is easy to assert and easy to "
      "get wrong, so it is tested rather than stated. The same three ports are "
      f"dialled twice: once on loopback and once on {ROUTABLE_IP}, the address "
      "another machine would use to reach this one.")
    fig("fig-isolation.png", "The same three ports, dialled two ways", 6.1)
    p("Only 8091 answers on the routable address. The two services accept "
      "connections from processes on this machine, which includes the gateway, "
      "and refuse everything else. On a runtime where the bridge network works "
      "the same property comes from the compose file instead, with expose on the "
      "services and ports on the gateway only.")

    h1("What happens when a service dies")
    p("The last test says the most about the design. I stopped the catalogue "
      "container and left everything else running.")
    fig("fig-outage-stop.png",
        "docker stop bazaar-products. Two containers left, and the gateway still "
        "answering for itself", 6.0)
    fig("fig-outage-503.png", "One 503 from NGINX, one from the orders service")
    p("Those two 503s are not the same 503. The first is the gateway's: NGINX "
      "could not connect to an upstream at all, so error_page produced the "
      "shaped JSON from Task 1 instead of an HTML page. The second is the orders "
      "service's own, and it is the more useful message, because the orders "
      "service is perfectly healthy and it says which dependency is missing, at "
      "which address, and why that stops it pricing an order. From those two "
      "responses a caller can tell that the catalogue is the problem and the "
      "order pipeline is not.")
    fig("fig-outage-survives.png",
        "Orders already placed are still readable, and the dependency probe "
        "reports what it now sees", 6.0)
    fig("shot-storefront-degraded.png",
        "The same page with the catalogue container stopped. The "
        "products-service pill has gone red, the catalogue is a message, and the "
        "orders table is still there")
    p("That screenshot is the clearest thing in this document. The page is not "
      "broken, it is partly available, and it is obvious from looking at it "
      "which service is down.")
    fig("fig-recovery.png",
        "docker start, and the catalogue route recovering with no gateway "
        "restart and no reload", 6.0)
    fig("shot-storefront-restored.png",
        "The storefront after the catalogue came back. The pill recovers on its "
        "own; the poll runs every five seconds")

    note("This one deserves a caveat I only understood because of the nginx -t "
         "finding earlier. NGINX resolved products-service once, at startup, so "
         "recovery worked here because the container came back at the same "
         "address. Had it come back somewhere else, the gateway would have kept "
         "sending traffic to the old address until it was reloaded. Getting that "
         "right needs a resolver directive and the upstream in a variable, and "
         "it is the difference between a gateway that survives a restart and one "
         "that only appears to.")

    # ================================================= what went wrong
    brk()
    h1("What went wrong")
    p("The application was the quick part. Most of the time went on the "
      "container runtime, and the sequence is worth recording because none of it "
      "announced itself clearly.")
    p("The first version was ordinary: a bridge network, the gateway publishing "
      "8080, the two services on expose so only the gateway could reach them. "
      "The gateway would not start, because 8080 was already taken on the "
      "machine. I moved it to 8090, and the container started, answered exactly "
      "one health check, and died.")
    p("From there it got stranger. Podman reported the port as published while "
      "nothing was listening on it. Container-to-container calls failed by name, "
      "so I tried by address and they failed that way too, which ruled out DNS "
      "and pointed at the network itself. Both containers had addresses on the "
      "bridge that no packet could reach from anywhere. docker exec refused to "
      "run at all, complaining it could not find root in the passwd file. Then "
      "podman deadlocked hard enough to need podman system renumber before it "
      "would delete a container.")
    p("The cause is in podman info, a few lines below where I first looked. The "
      "runtime is not rootless, but its capability list has no CAP_NET_ADMIN. "
      "Without that, netavark can allocate addresses on a bridge and cannot "
      "program any routes to them, so containers get addresses that do not work, "
      "and publishing a port fails for the same reason because publishing is "
      "NAT. Running podman rootless instead would have given it full "
      "capabilities inside a user namespace, and that failed too, with a bare "
      "permission denied.")
    p("The deadlock had a separate cause worth knowing: podman-compose puts "
      "every service in a pod, so the containers shared an infra container's "
      "network namespace, and that combination is what wedged the runtime. So "
      "docker-compose.yml is validated with docker compose config and is the "
      "declarative description of the system, but run.sh starts the containers "
      "with explicit docker run commands carrying the same environment. I would "
      "rather ship a compose file that says what the system is and be honest "
      "that the evidence came from the equivalent commands.")
    p("Host networking was the way out: all three containers share the host "
      "network namespace, the services bind loopback, the gateway binds "
      "everything. The isolation test earlier is what convinced me the property "
      "I wanted had actually survived the change.")
    p("One more, which cost the most time for the least reason. After all that, "
      "the gateway was demonstrably listening on 8090 in the right namespace and "
      "no connection to it ever completed. A plain Python HTTP server on the "
      "same port behaved identically, which finally removed NGINX from "
      "suspicion. Port 8090 is filtered somewhere in that sandbox: a process "
      "binds it happily and nothing ever arrives. 8091 works. Nothing was wrong "
      "with the configuration at all.")
    note("The lesson I will actually keep: when a component looks broken, "
         "replace it with the most boring possible substitute before reading its "
         "configuration again. One python3 -m http.server would have saved me an "
         "hour if I had reached for it first, instead of assuming that a web "
         "server failing to serve was a web server problem.")

    h1("Bugs in my own work")
    p("Three, all found by looking at output rather than by reasoning about code.")
    bullets([
        "The X-Request-ID came back twice. The gateway adds it and the services "
        "echo it, and the storefront duly displayed the identifier, a comma, and "
        "the same identifier again, because fetch joins repeated headers. "
        "proxy_hide_header drops the upstream copy so only the one from the "
        "component that minted it leaves.",
        "/health returned no X-Request-ID while every other route had one. That "
        "is the add_header inheritance rule described in Task 1, and I would not "
        "have noticed if the health endpoint had not been in the same table of "
        "captured headers as the proxied routes.",
        "Successful responses were indented and error responses were not, "
        "because FastAPI's default_response_class applies to routes and not to "
        "exception handlers. Two figures side by side disagreeing about "
        "formatting is what made me look.",
    ])

    # ================================================= conclusion
    h1("Conclusion")
    p("The routing was the smallest part of this. Two upstream blocks and four "
      "location blocks and the gateway does what the assignment asked, and I had "
      "that working before I understood anything interesting.")
    p("What the gateway is actually worth showed up around the routing. The "
      "storefront needs no CORS configuration because the page and the API share "
      "an origin, and that is work I never had to do rather than a feature I can "
      "point at. A stopped container produces a JSON 503 instead of an HTML "
      "error page because of four lines near the bottom of the file. Every "
      "request gets an identifier that makes it traceable across three "
      "containers, and no service had to be taught to generate one.")
    p("On the service-to-service side, the thing I would carry into a bigger "
      "system is that most of the code in the east-west call is error "
      "translation, and that this is correct rather than defensive clutter. The "
      "outage test proved it: an orders service returning a 503 that names its "
      "missing dependency is genuinely more useful than a 500, and it cost about "
      "ten lines. Choosing REST over a queue was right here for a boring reason, "
      "which is that the caller cannot proceed without the answer, and I would "
      "rather be able to say why than have reached for a broker because the "
      "assignment mentioned one.")
    p("The rest of what I learned was about being wrong efficiently. A build "
      "failing on a valid config file taught me when NGINX resolves upstream "
      "names, which then explained both why compose needs depends_on and why the "
      "recovery test only worked because the container came back at the same "
      "address. An hour lost to a filtered port taught me to substitute the "
      "simplest possible component before rereading configuration. Both came "
      "from things not working, which is not the part of an assignment I would "
      "have chosen and is most of what I took away from it.")

    return B
