package com.bilbao.ecommerce.config;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.config.server.EnableConfigServer;

/**
 * The Config Server.
 *
 * <p>{@code @EnableConfigServer} is the whole of it. The server reads the YAML
 * files in {@code config-repo/} and serves them over HTTP at
 * {@code /{application}/{profile}}, so the two business services hold no
 * configuration of their own beyond their name and where to find this server.
 */
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
