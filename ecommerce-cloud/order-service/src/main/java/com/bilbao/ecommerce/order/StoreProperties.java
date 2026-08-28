package com.bilbao.ecommerce.order;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * The same {@code store.*} values the Product Service reads, from the same
 * {@code config-repo/application.yml}. Neither service declares them; both are
 * served them. The tax rate here is the one applied to order totals.
 */
@Component
@RefreshScope
@ConfigurationProperties(prefix = "store")
public class StoreProperties {

    private String name = "(not configured)";
    private String currency = "???";
    private double taxRate;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCurrency() {
        return currency;
    }

    public void setCurrency(String currency) {
        this.currency = currency;
    }

    public double getTaxRate() {
        return taxRate;
    }

    public void setTaxRate(double taxRate) {
        this.taxRate = taxRate;
    }
}
