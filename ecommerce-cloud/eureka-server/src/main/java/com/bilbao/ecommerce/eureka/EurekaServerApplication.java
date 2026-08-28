package com.bilbao.ecommerce.eureka;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

/**
 * The Eureka service registry.
 *
 * <p>{@code @EnableEurekaServer} turns this application into the registry the
 * other two services report to, and serves the dashboard at
 * {@code http://localhost:8761/}. It registers nothing itself, which is why
 * {@code register-with-eureka} and {@code fetch-registry} are both false.
 */
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
