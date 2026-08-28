package com.bilbao.ecommerce.order;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;

/**
 * Order Service: places orders, and asks the Product Service what things cost.
 */
@SpringBootApplication
@EnableDiscoveryClient
public class OrderServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }

    /**
     * The one bean that makes service discovery useful rather than merely
     * present.
     *
     * <p>{@code @LoadBalanced} wires a Spring Cloud LoadBalancer interceptor
     * into this RestTemplate. Given the URL {@code http://product-service/...},
     * the interceptor treats the host as a name to look up in Eureka, picks one
     * of the registered instances, and rewrites the URL to that instance's real
     * host and port before the request is sent.
     *
     * <p>Without the annotation the same call fails with UnknownHostException,
     * because "product-service" is not a DNS name. That failure is captured in
     * the write-up, because it is the clearest demonstration that the lookup is
     * genuinely happening here and not somewhere else.
     */
    @Bean
    @LoadBalanced
    public RestTemplate loadBalancedRestTemplate() {
        return new RestTemplate();
    }

    /**
     * A plain RestTemplate with no interceptor, used only by the endpoint that
     * demonstrates what happens without load balancing.
     */
    @Bean
    public RestTemplate plainRestTemplate() {
        return new RestTemplate();
    }
}
