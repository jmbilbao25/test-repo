package com.bilbao.ecommerce.order;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

/**
 * The Order Service's view of the Product Service.
 *
 * <p>Every URL in here uses the logical name {@code product-service}. No host
 * and no port appears anywhere in this class, or anywhere else in the Order
 * Service. That is the practical payoff of service discovery: the Product
 * Service can move, restart on a different port, or run as three instances, and
 * nothing here changes.
 */
@Component
public class ProductClient {

    private final RestTemplate loadBalanced;
    private final RestTemplate plain;
    private final DiscoveryClient discoveryClient;
    private final String serviceName;

    public ProductClient(RestTemplate loadBalancedRestTemplate,
                         RestTemplate plainRestTemplate,
                         DiscoveryClient discoveryClient,
                         org.springframework.core.env.Environment env) {
        this.loadBalanced = loadBalancedRestTemplate;
        this.plain = plainRestTemplate;
        this.discoveryClient = discoveryClient;
        this.serviceName = env.getProperty("product-service.name", "product-service");
    }

    /** Fetch one product through Eureka. Empty if the product does not exist. */
    public ProductView fetch(long productId) {
        Map<?, ?> body = loadBalanced.getForObject(
                "http://" + serviceName + "/products/{id}", Map.class, productId);
        if (body == null) {
            throw new ProductLookupException(
                    "product-service returned an empty body for product " + productId);
        }
        return new ProductView(
                ((Number) body.get("id")).longValue(),
                String.valueOf(body.get("name")),
                new BigDecimal(String.valueOf(body.get("price"))),
                ((Number) body.get("stock")).intValue());
    }

    /**
     * The instances Eureka currently lists for the Product Service.
     *
     * <p>This is the registry as the Order Service sees it, which is not
     * necessarily the same as the dashboard: the client caches the registry and
     * refreshes it on an interval, so there is a window where the dashboard and
     * this disagree. Step 2 shows that window.
     */
    public List<ServiceInstance> instances() {
        return discoveryClient.getInstances(serviceName);
    }

    /** Every service name the registry knows about. */
    public List<String> registeredServices() {
        return discoveryClient.getServices();
    }

    /**
     * The same call as {@link #fetch}, but through a RestTemplate with no
     * load balancer attached.
     *
     * <p>It always fails, and the failure is the point: it shows that
     * "product-service" is not resolvable by ordinary means, so the working call
     * must be doing a registry lookup rather than relying on DNS or a hosts
     * entry.
     */
    public String fetchWithoutDiscovery(long productId) {
        try {
            plain.getForObject("http://" + serviceName + "/products/{id}",
                    String.class, productId);
            return "unexpectedly succeeded";
        } catch (RestClientException e) {
            Throwable root = e;
            while (root.getCause() != null) {
                root = root.getCause();
            }
            return root.getClass().getSimpleName() + ": " + root.getMessage();
        }
    }

    /** What the Order Service needs to know about a product to price an order. */
    public record ProductView(long id, String name, BigDecimal price, int stock) {
    }

    /** Thrown when the Product Service cannot be reached or answers unusably. */
    public static class ProductLookupException extends RuntimeException {
        public ProductLookupException(String message) {
            super(message);
        }
    }
}
