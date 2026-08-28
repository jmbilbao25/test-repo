package com.bilbao.ecommerce.product;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

/**
 * Product Service: owns the catalogue.
 *
 * <p>It registers itself with Eureka under the name {@code product-service} and
 * takes its configuration from the Config Server. It does not know the Order
 * Service exists.
 */
@SpringBootApplication
@EnableDiscoveryClient
public class ProductServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ProductServiceApplication.class, args);
    }
}
