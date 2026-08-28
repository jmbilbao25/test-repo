package com.bilbao.ecommerce.order;

import java.math.BigDecimal;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * The {@code orders.*} values from {@code config-repo/order-service.yml}.
 *
 * <p>These are business rules, not plumbing, which is the honest argument for a
 * Config Server: the free shipping threshold is the sort of thing that changes
 * for a weekend promotion, and it should not need a rebuild and redeploy.
 */
@Component
@RefreshScope
@ConfigurationProperties(prefix = "orders")
public class OrderProperties {

    private int maxItemsPerOrder = 1;
    private BigDecimal freeShippingThreshold = BigDecimal.ZERO;
    private BigDecimal shippingFee = BigDecimal.ZERO;

    public int getMaxItemsPerOrder() {
        return maxItemsPerOrder;
    }

    public void setMaxItemsPerOrder(int maxItemsPerOrder) {
        this.maxItemsPerOrder = maxItemsPerOrder;
    }

    public BigDecimal getFreeShippingThreshold() {
        return freeShippingThreshold;
    }

    public void setFreeShippingThreshold(BigDecimal freeShippingThreshold) {
        this.freeShippingThreshold = freeShippingThreshold;
    }

    public BigDecimal getShippingFee() {
        return shippingFee;
    }

    public void setShippingFee(BigDecimal shippingFee) {
        this.shippingFee = shippingFee;
    }
}
