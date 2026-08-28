"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment. Values quoted in the prose are parsed out of results/, the same
source the figures are built from.
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

TITLE = ("Spring Cloud Service Discovery and Configuration: "
         "An E-Commerce Use Case")
DAY = "Day 13 Hands-on Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 28, 2026"


def _read(name: str, folder: str = RESULTS) -> str:
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read()


def _find(pattern: str, capture: str, group: int = 1) -> str:
    m = re.search(pattern, _read(capture))
    if not m:
        raise SystemExit(f"{pattern!r} not found in {capture}")
    return m.group(group)


JAVA = _find(r'Java:\s+openjdk version "([^"]+)"', "build_summary.txt")
REFRESHED_KEYS = _find(r'refresh\n(\[[^\]]*\])', "refresh.txt")
OLD_PORT = "9081"
NEW_PORT = "9091"
# The order placed after the service came back on a different port.
REREG_TOTAL = _find(r'"total" : ([\d.]+)', "reregister.txt")
REREG_INSTANCE = _find(r'"servedByProductInstance" : "([^"]+)"', "reregister.txt")
LOW_STOCK_COUNT = _find(r'"threshold" : 8,\n\s+"count" : (\d+)', "refresh.txt")


def _code(path: str, first: str, last: str) -> list[str]:
    """Lines of a real source file, so quoted code cannot drift."""
    folder, filename = os.path.split(path)
    rows = _read(filename, os.path.join(HERE, folder)).rstrip("\n").split("\n")
    a = next(i for i, l in enumerate(rows) if first in l)
    b = next(i for i, l in enumerate(rows) if last in l and i >= a)
    return rows[a:b + 1]


def blocks() -> list[tuple]:
    return [
        ("h1", "The application"),
        ("p",
         "Bilbao Bazaar is a small e-commerce back end split into two business "
         "services. The Product Service owns the catalogue: eight products, "
         "their prices and their stock. The Order Service places orders, and to "
         "price one it has to ask the Product Service what the item costs."),
        ("p",
         "That single cross-service call is where the whole assignment lives. "
         "The Order Service has to find the Product Service without being told "
         "where it is, which is service discovery, and both services have to "
         "agree on the tax rate and the currency without either of them "
         "declaring it, which is configuration management. Two more "
         "applications exist to make that possible: a Eureka server that holds "
         "the registry, and a Config Server that holds the configuration."),
        ("table", [
            ["Application", "Port", "What it does"],
            ["config-server", "8888",
             "Serves the YAML in config-repo/ over HTTP"],
            ["eureka-server", "8761",
             "The service registry, and the dashboard"],
            ["product-service", OLD_PORT,
             "The catalogue. Registers with Eureka, configured by the Config Server"],
            ["order-service", "9082",
             "Places orders. Finds the Product Service through Eureka"],
        ], [1.5, 0.7, 4.3]),
        ("p",
         f"Everything below ran on Java {JAVA} with Spring Boot 3.4.1 and "
         "Spring Cloud 2024.0.0. The Eureka dashboard, the Config Server and "
         "both service APIs were photographed in a real browser at the URLs "
         "shown in each address bar; the terminal figures are captured command "
         "output. Nothing is retyped, so no figure can show something the "
         "applications did not do."),
        ("note",
         "The one design decision worth stating up front: no host and no port "
         "for the Product Service appears anywhere in the Order Service. It "
         "calls http://product-service/products/{id} and lets the registry "
         "resolve the name. The proof that this is real rather than incidental "
         "comes at the end, where the Product Service is restarted on a "
         f"different port ({NEW_PORT} instead of {OLD_PORT}) and the Order "
         "Service keeps working without a restart or a configuration change."),

        ("break",),
        ("h1", "Step 1: setting up the environment"),
        ("p",
         "The four applications are Maven modules under one aggregator pom. "
         "Declaring the Spring Cloud BOM once there is what keeps the Eureka "
         "and Config dependencies in the modules version-free, and stops the "
         "two from drifting apart."),
        ("fig", "fig-code-parent-pom.png",
         "The aggregator pom: the module list, and the Spring Cloud BOM "
         "imported once for all four.", 6.3),
        ("fig", "fig-build.png",
         "One mvn package builds all four executable jars.", 6.5),

        ("break",),
        ("h1", "Step 3 comes first: the Config Server"),
        ("p",
         "The assignment lists configuration third, but it has to be built "
         "second, because the two business services ask the Config Server for "
         "their configuration during startup rather than after it. With no "
         "Config Server running there is nothing for them to be configured "
         "from, so it is the first thing that has to exist after the build."),
        ("fig", "fig-code-config-java.png",
         "The entire Config Server. One annotation.", 6.3),
        ("fig", "fig-code-config-yml.png",
         "The native profile points the server at a directory instead of a Git "
         "repository. Git is the usual production choice; the HTTP contract the "
         "clients see is identical either way, and this keeps the assignment to "
         "one moving part.", 6.3),
        ("p",
         "The configuration itself is split in two, and the split is the "
         "argument for having a Config Server at all. Anything both services "
         "need lives in application.yml. Anything only one service needs lives "
         "in a file named after that service."),
        ("fig", "fig-code-config-repo-shared.png",
         "config-repo/application.yml: the store name, currency and tax rate, "
         "defined once for every service that asks.", 6.3),
        ("fig", "fig-code-config-repo-product.png",
         "config-repo/product-service.yml. The file name is not arbitrary: it "
         "has to match the service's spring.application.name, which is how the "
         "server knows which file to serve to whom.", 6.3),
        ("p",
         "The server exposes it at /{application}/{profile}, and merges the two "
         "files for the caller. Asking for the shared file directly shows what "
         "every service receives:"),
        ("fig", "shot-config-application.png",
         "The Config Server serving the shared configuration, in a browser at "
         "localhost:8888/application/default.", 6.5),
        ("fig", "shot-config-product.png",
         "The same endpoint for product-service. Two property sources come "
         "back: the service-specific file first, then the shared one. That "
         "order is the precedence rule, and it is why a service can override a "
         "shared default.", 6.5),
        ("fig", "shot-config-order.png",
         "And for order-service, which gets its own orders.* values plus the "
         "same shared store.* block.", 6.5),
        ("fig", "fig-config-yaml.png",
         "The same configuration served as plain YAML rather than as the "
         "server's JSON envelope, which is the form that is easiest to check by "
         "eye.", 6.5),

        ("break",),
        ("h1", "Step 2: service discovery with Eureka"),
        ("p",
         "The Eureka server is the registry: services report in when they start, "
         "renew a lease while they are alive, and are removed when they stop or "
         "stop renewing. It is as small as the Config Server."),
        ("fig", "fig-code-eureka-java.png",
         "The Eureka server. It registers nothing itself, which is why both "
         "client flags are false in its configuration.", 6.3),
        ("fig", "fig-code-eureka-yml.png",
         "Two settings here are deliberate departures from the defaults, and "
         "the comment says why: self preservation would stop Eureka evicting a "
         "stopped instance, and this assignment has to show one actually "
         "disappearing.", 6.3),
        ("fig", "fig-eureka-empty.png",
         "The registry immediately after the server starts: empty.", 6.5),
        ("p",
         "A service becomes a client by adding the Eureka client starter and "
         "pointing it at the registry. Its spring.application.name does double "
         "duty: Eureka registers the instance under it, and the Config Server "
         "uses it to choose a file."),
        ("fig", "fig-code-product-yml.png",
         "All the Product Service knows: its own name, where the Config Server "
         "is, and where Eureka is. The lease intervals are shortened from the "
         "30-second defaults so registration and eviction are quick enough to "
         "observe.", 6.3),
        ("p",
         "Both services then start, and the startup logs show the two "
         "mechanisms in sequence: fetch configuration, then register."),
        ("fig", "fig-startup-product.png",
         "product-service: it fetches its configuration from localhost:8888, "
         f"then registers with Eureka and Tomcat starts on {OLD_PORT}. "
         "Registration status 204 is Eureka acknowledging the lease.", 6.5),
        ("fig", "fig-startup-order.png",
         "order-service doing the same thing.", 6.5),
        ("fig", "shot-eureka-dashboard.png",
         "The Eureka dashboard with both services registered and UP. This is "
         "the screenshot the assignment asks for.", 6.5),
        ("fig", "fig-eureka-both.png",
         "The same registry over Eureka's REST API rather than the dashboard, "
         "which is what a client actually consumes.", 6.5),
        ("fig", "fig-eureka-lease.png",
         "One lease in full. The interesting fields are vipAddress, the logical "
         "name callers use, and leaseInfo, which carries the renewal interval "
         "and the duration after which the lease expires.", 6.5),

        ("h1", "Using the registry, rather than just filling it"),
        ("p",
         "Registering is the easy half. The Order Service has to resolve the "
         "name to an address, and that is one bean."),
        ("fig", "fig-code-loadbalanced.png",
         "The bean that makes discovery useful. @LoadBalanced adds an "
         "interceptor that treats the host in the URL as a name to look up in "
         "Eureka, picks a registered instance, and rewrites the URL before the "
         "request goes out.", 6.3),
        ("fig", "fig-code-productclient.png",
         "The client. Every URL uses the logical name; no host or port appears "
         "anywhere in the Order Service.", 6.3),
        ("p",
         "It is worth proving that the lookup is really happening here, and not "
         "that something else is quietly resolving the name. The same call on a "
         "plain RestTemplate, with no interceptor, is exposed as its own "
         "endpoint:"),
        ("fig", "fig-code-nodiscovery.png",
         "The deliberately broken call, kept as an endpoint so the failure can "
         "be captured rather than described.", 6.3),
        ("fig", "fig-without-discovery.png",
         "UnknownHostException: product-service. The name is not a DNS name and "
         "nothing on the machine can resolve it, so the working call must be "
         "going through the registry.", 6.5),

        ("break",),
        ("h1", "Step 4: the two services working together"),
        ("p",
         "With both mechanisms in place the application does something. The "
         "catalogue response is wrapped in values the Product Service did not "
         "declare: the store name and currency came from the shared file, the "
         "banner and page size from its own."),
        ("fig", "shot-product-list.png",
         "GET /products in a browser. featuredMessage and pageSize are "
         "configuration, not code.", 6.5),
        ("fig", "fig-product-one.png",
         "GET /products/3, the endpoint the Order Service calls through "
         "Eureka.", 6.5),
        ("fig", "shot-product-config-before.png",
         "GET /products/config reports everything this service was told, which "
         "makes the effect of a configuration change visible in one place.",
         6.5),
        ("p",
         "The Order Service exposes the same idea from the other side: one "
         "endpoint that answers whether discovery is working and whether "
         "configuration is working at the same time."),
        ("fig", "shot-order-discovery.png",
         "GET /orders/discovery: the service names Eureka knows, the concrete "
         "instances of product-service with their host and port, and the "
         "configuration this service received.", 6.5),
        ("p",
         "Placing an order uses both. The price is fetched from the Product "
         "Service found through Eureka; the tax rate, the shipping fee and the "
         "free-shipping threshold all come from the Config Server."),
        ("fig", "fig-order-place.png",
         "Two orders. The monitor is over the 2,000 free-shipping threshold so "
         "shipping is zero; the mouse is under it and is charged 150. Both "
         "figures are configuration, and servedByProductInstance records which "
         "discovered instance answered.", 6.5),
        ("fig", "fig-order-limit.png",
         "A configured business rule refusing an order. The maximum is not a "
         "constant in the Order Service; it is a value the Config Server "
         "supplied, and the error message quotes it.", 6.5),
        ("fig", "shot-orders-list.png",
         "GET /orders in a browser, with both orders and the configured store "
         "name and currency.", 6.5),
        ("note",
         "One deliberate choice in the Order model: productName and unitPrice "
         "are copied from the Product Service when the order is placed, not "
         "looked up again on every read. An order is a record of what was "
         "agreed, and a later price change must not silently rewrite it. This "
         "is the kind of decision service boundaries force you to make "
         "explicitly, which is an argument in their favour."),

        ("break",),
        ("h1", "Step 3: changing configuration on a running service"),
        ("p",
         "The assignment asks for configuration values to be updated and "
         "retrieved. Retrieving them is already shown. Updating them is more "
         "interesting than it sounds, because there are three separate states "
         "and it is easy to mistake one for another."),
        ("fig", "fig-code-refreshscope.png",
         "@RefreshScope is what makes an update possible without a restart. "
         "Without it these values are bound once at startup; with it, the bean "
         "is discarded and rebuilt on next use after a refresh.", 6.3),
        ("fig", "fig-refresh-before.png",
         "The value the running service is using, then the edit: a new banner, "
         "the page size cut from 20 to 4, and the low-stock threshold raised "
         "from 5 to 8.", 6.5),
        ("fig", "fig-refresh-lag.png",
         "The state that is easy to miss. The Config Server serves the new "
         "values the moment the file is saved, and the running service is still "
         "on the old ones. Checking the Config Server alone would have looked "
         "like success.", 6.5),
        ("fig", "shot-config-product-after.png",
         "The Config Server in a browser after the edit, serving the new "
         "values.", 6.5),
        ("fig", "fig-refresh-after.png",
         f"POST /actuator/refresh returns {REFRESHED_KEYS}, the keys it found "
         "changed, and the service now reports the new values.", 6.5),
        ("fig", "shot-product-config-after.png",
         "The same endpoint in a browser after the refresh. Compare with the "
         "earlier screenshot of this URL.", 6.5),
        ("p",
         "A configuration endpoint reporting a new number is still only a "
         "report. The threshold is used to decide which products count as low "
         "stock, so raising it from 5 to 8 should change what a different "
         "endpoint returns:"),
        ("fig", "fig-refresh-behaviour.png",
         f"The new threshold changing behaviour: {LOW_STOCK_COUNT} products now "
         "count as low stock, including the monitor with 7 in stock, which did "
         "not qualify under the old threshold of 5.", 6.5),
        ("fig", "shot-product-low-stock.png",
         "The same result in a browser.", 6.5),

        ("break",),
        ("h1", "Step 2 again: deregistering, and coming back somewhere else"),
        ("p",
         "The assignment asks for service discovery to be tested by registering "
         "and deregistering. Registering is shown above. Deregistering is where "
         "a registry earns its place, because the interesting question is what "
         "happens to the caller."),
        ("fig", "fig-dereg-goodbye.png",
         "The Product Service on the way out. Spring's shutdown hook runs the "
         "DiscoveryClient shutdown, which sends an explicit deregistration and "
         "gets 200 back. A service that is stopped cleanly does not wait to be "
         "evicted; it says it is going.", 6.5),
        ("fig", "shot-eureka-deregistered.png",
         "The dashboard with only ORDER-SERVICE left. The assignment's "
         "deregistration test, in the browser.", 6.5),
        ("fig", "fig-dereg-registry.png",
         "The same absence over the REST API.", 6.5),
        ("fig", "shot-order-discovery-empty.png",
         "The Order Service now sees an empty instance list for "
         "product-service, while its own configuration is untouched. Discovery "
         "and configuration fail independently, which is worth knowing when "
         "something breaks.", 6.5),
        ("fig", "fig-dereg-order.png",
         "Placing an order now fails with 503 and a readable reason rather than "
         "a stack trace. A missing dependency is an operational state, not a "
         "bug in the Order Service, and orders already placed are unaffected.",
         6.5),
        ("p",
         "Then the Product Service is started again, deliberately on port "
         f"{NEW_PORT} rather than the {OLD_PORT} it had before. Nothing in the "
         "Order Service is changed, and it is not restarted."),
        ("fig", "fig-rereg-port.png",
         f"The Product Service answering on {NEW_PORT}.", 6.5),
        ("fig", "fig-rereg-registry.png",
         "It registers under the same logical name, PRODUCT-SERVICE, with the "
         "new port in the lease.", 6.5),
        ("fig", "shot-eureka-restored.png",
         f"The dashboard: both services UP again, product-service now on "
         f"{NEW_PORT}.", 6.5),
        ("fig", "fig-rereg-order.png",
         f"The payoff. The Order Service finds it at the new port and prices an "
         f"order, total {REREG_TOTAL}, served by {REREG_INSTANCE} - with no "
         "restart and no configuration change of its own.", 6.5),
        ("note",
         "This is the part of the assignment that is hard to fake and easy to "
         "underrate. Had the Order Service held the Product Service's address "
         "in a config file, this restart would have broken it, and fixing it "
         "would have meant editing configuration and refreshing. Because the "
         "address is resolved from the registry on every call, the move cost "
         "nothing. That is the entire practical argument for service discovery, "
         "and it took a port change to actually demonstrate it."),

        ("break",),
        ("h1", "How it was implemented, in order"),
        ("bullets", [
             "One aggregator pom with the Spring Cloud BOM imported once, so "
             "the four modules cannot disagree on versions.",

             "Config Server: spring-cloud-config-server and "
             "@EnableConfigServer, pointed at config-repo/ with the native "
             "profile. Shared values in application.yml, per-service values in "
             "a file named after the service's spring.application.name.",

             "Eureka server: spring-cloud-starter-netflix-eureka-server and "
             "@EnableEurekaServer, with register-with-eureka and fetch-registry "
             "off because it is the registry, and self preservation off so "
             "eviction can be observed.",

             "Both business services: the Eureka client starter to register, "
             "spring-cloud-starter-config plus spring.config.import to be "
             "configured at startup, and actuator to expose /actuator/refresh.",

             "@RefreshScope on the @ConfigurationProperties beans, which is "
             "what lets POST /actuator/refresh rebind them without a restart.",

             "A @LoadBalanced RestTemplate in the Order Service, so "
             "http://product-service/... resolves through the registry. This is "
             "the only place discovery is actually consumed rather than merely "
             "configured.",
         ]),

        ("h1", "The two pieces of code that matter"),
        ("p",
         "Everything else is annotations and YAML. These two are the "
         "load-bearing parts, quoted from the source."),
        ("code", _code(
            "order-service/src/main/java/com/bilbao/ecommerce/order/"
            "OrderServiceApplication.java",
            "    @Bean", "    public RestTemplate loadBalancedRestTemplate")),
        ("p",
         "And the call that uses it, where the logical name appears instead of "
         "an address:"),
        ("code", _code(
            "order-service/src/main/java/com/bilbao/ecommerce/order/"
            "ProductClient.java",
            "    public ProductView fetch", "    }")),

        ("h1", "Reproducing it"),
        ("code", [
            "cd ecommerce-cloud",
            "./run.sh                         # builds, starts all four, exercises everything",
            "python3 scripts/make_figures.py  # results/ and screenshots/ into figures/",
            "python3 build.py                 # figures/ into the .docx and .pdf",
        ]),
        ("p",
         "run.sh does the whole thing in one invocation, because the four "
         "services are its child processes and splitting the steps across "
         "separate shells would lose them in between. It starts them in "
         "dependency order, waits on each health endpoint, exercises both "
         "mechanisms, drives a real browser for the screenshots, and shuts "
         "everything down and restores the edited YAML on the way out."),

        ("h1", "Conclusion and takeaways"),
        ("p",
         "Both mechanisms did what they claim, and building them was less work "
         "than expected: the Config Server and the Eureka server are one "
         "annotation each. What took the actual thinking was working out how to "
         "show they were working rather than merely running."),
        ("bullets", [
             "A registry is only doing something if the caller uses it. "
             "Registering both services and screenshotting the dashboard "
             "demonstrates almost nothing on its own; the same dashboard would "
             "look identical if the Order Service had the Product Service's "
             "port hard-coded. Restarting the Product Service on a different "
             "port is what turns the claim into evidence.",

             "The failing case is the clearest proof. UnknownHostException on a "
             "plain RestTemplate shows that the logical name is genuinely "
             "unresolvable, and therefore that the working call is doing a "
             "registry lookup. A test that only ever passes cannot tell you "
             "which mechanism made it pass.",

             "There are three states in a configuration change, not two: the "
             "file, the Config Server's view of it, and the running service's "
             "view of it. The Config Server picked up the edit immediately "
             "while the service was still serving old values. Checking the "
             "server alone would have looked like success and been wrong.",

             "Refreshing a value is not the same as changing behaviour. The "
             "config endpoint reported the new threshold, and it was worth "
             "checking a second endpoint that uses it to confirm the new value "
             "was actually being applied.",

             "Startup order is a real dependency. The business services fetch "
             "configuration during startup, so the Config Server has to be up "
             "first. Using optional: in spring.config.import means they still "
             "start without it, which is a better failure than refusing to "
             "boot, but they start unconfigured.",

             "Ordinary defaults get in the way of demonstrating things. Eureka's "
             "self preservation and its 30-second lease intervals are correct "
             "for production and wrong for an assignment that needs to show a "
             "service disappearing within a screenshot's patience.",
         ]),
    ]
