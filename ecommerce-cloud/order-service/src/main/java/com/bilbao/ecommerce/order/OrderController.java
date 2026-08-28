package com.bilbao.ecommerce.order;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.cloud.client.ServiceInstance;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientException;

/**
 * The orders API.
 *
 * <p>Placing an order is the one operation in this application that crosses a
 * service boundary, so it is where discovery and configuration both show up at
 * once: the price comes from the Product Service found through Eureka, and the
 * tax rate, shipping fee and item limit come from the Config Server.
 */
@RestController
@RequestMapping("/orders")
public class OrderController {

    private final Map<String, Order> orders = new ConcurrentHashMap<>();
    private final ProductClient products;
    private final OrderProperties orderProps;
    private final StoreProperties store;

    public OrderController(ProductClient products,
                           OrderProperties orderProps,
                           StoreProperties store) {
        this.products = products;
        this.orderProps = orderProps;
        this.store = store;
    }

    /** A request to place an order. */
    public record OrderRequest(long productId, int quantity) {
    }

    @PostMapping
    public ResponseEntity<?> place(@RequestBody OrderRequest request) {
        if (request.quantity() < 1) {
            return ResponseEntity.badRequest().body(
                    error("quantity must be at least 1"));
        }
        // A configured business rule, enforced with the value the Config Server
        // supplied rather than a constant compiled into this service.
        if (request.quantity() > orderProps.getMaxItemsPerOrder()) {
            return ResponseEntity.badRequest().body(error(
                    "quantity " + request.quantity() + " exceeds the configured "
                    + "maximum of " + orderProps.getMaxItemsPerOrder()
                    + " items per order"));
        }

        ProductClient.ProductView product;
        List<ServiceInstance> instances;
        try {
            instances = products.instances();
            product = products.fetch(request.productId());
        } catch (RestClientException | ProductClient.ProductLookupException e) {
            // The Product Service being unreachable is a real operational state,
            // not a bug in this service, so it gets a 503 and a readable reason
            // rather than a stack trace.
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(error(
                    "could not reach product-service through Eureka: "
                    + e.getMessage()));
        }

        if (product.stock() < request.quantity()) {
            return ResponseEntity.badRequest().body(error(
                    "only " + product.stock() + " of " + product.name()
                    + " in stock"));
        }

        BigDecimal subtotal = product.price()
                .multiply(BigDecimal.valueOf(request.quantity()));
        BigDecimal tax = subtotal
                .multiply(BigDecimal.valueOf(store.getTaxRate()))
                .setScale(2, RoundingMode.HALF_UP);
        // Free shipping over the configured threshold: the other rule that is
        // configuration rather than code.
        BigDecimal shipping =
                subtotal.compareTo(orderProps.getFreeShippingThreshold()) >= 0
                        ? BigDecimal.ZERO
                        : orderProps.getShippingFee();

        String servedBy = instances.isEmpty()
                ? "unknown"
                : instances.get(0).getHost() + ":" + instances.get(0).getPort();

        Order order = new Order(
                UUID.randomUUID().toString().substring(0, 8),
                product.id(),
                product.name(),
                request.quantity(),
                product.price(),
                subtotal.setScale(2, RoundingMode.HALF_UP),
                tax,
                shipping.setScale(2, RoundingMode.HALF_UP),
                subtotal.add(tax).add(shipping).setScale(2, RoundingMode.HALF_UP),
                store.getCurrency(),
                servedBy,
                Instant.now());

        orders.put(order.id(), order);
        return ResponseEntity.status(HttpStatus.CREATED).body(order);
    }

    @GetMapping
    public Map<String, Object> list() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("store", store.getName());
        body.put("currency", store.getCurrency());
        body.put("count", orders.size());
        body.put("orders", orders.values().stream()
                .sorted((a, b) -> b.placedAt().compareTo(a.placedAt()))
                .toList());
        return body;
    }

    @GetMapping("/{id}")
    public ResponseEntity<Order> byId(@PathVariable String id) {
        Order order = orders.get(id);
        return order == null
                ? ResponseEntity.notFound().build()
                : ResponseEntity.ok(order);
    }

    /**
     * The registry as this service sees it, and the configuration it is running
     * on. One endpoint that answers "is discovery working" and "is configuration
     * working" at the same time.
     */
    @GetMapping("/discovery")
    public Map<String, Object> discovery() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("servicesRegisteredInEureka", products.registeredServices());
        body.put("productServiceInstances", products.instances().stream()
                .map(i -> {
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("instanceId", i.getInstanceId());
                    m.put("serviceId", i.getServiceId());
                    m.put("host", i.getHost());
                    m.put("port", i.getPort());
                    m.put("uri", i.getUri().toString());
                    return m;
                })
                .toList());
        Map<String, Object> config = new LinkedHashMap<>();
        config.put("store.name", store.getName());
        config.put("store.currency", store.getCurrency());
        config.put("store.taxRate", store.getTaxRate());
        config.put("orders.maxItemsPerOrder", orderProps.getMaxItemsPerOrder());
        config.put("orders.freeShippingThreshold", orderProps.getFreeShippingThreshold());
        config.put("orders.shippingFee", orderProps.getShippingFee());
        body.put("configurationFromConfigServer", config);
        return body;
    }

    /**
     * Calls the Product Service without the load balancer, which fails. Kept as
     * an endpoint so the failure can be captured as evidence rather than
     * described.
     */
    @GetMapping("/without-discovery/{productId}")
    public Map<String, Object> withoutDiscovery(@PathVariable long productId) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("attempted", "GET http://product-service/products/" + productId
                             + " on a RestTemplate with no @LoadBalanced");
        body.put("result", products.fetchWithoutDiscovery(productId));
        return body;
    }

    private Map<String, Object> error(String message) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("error", message);
        return body;
    }
}
