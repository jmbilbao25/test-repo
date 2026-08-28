package com.bilbao.ecommerce.product;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * The {@code store.*} values, which come from {@code config-repo/application.yml}
 * rather than from the product-specific file.
 *
 * <p>Both services read these and neither declares them, which is the point of
 * having a Config Server at all: the currency and the tax rate are defined once
 * and served to everything that needs them.
 */
@Component
@RefreshScope
@ConfigurationProperties(prefix = "store")
public class StoreProperties {

    private String name = "(not configured)";
    private String currency = "???";
    private double taxRate;
    private String supportEmail = "(not configured)";

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

    public String getSupportEmail() {
        return supportEmail;
    }

    public void setSupportEmail(String supportEmail) {
        this.supportEmail = supportEmail;
    }
}
