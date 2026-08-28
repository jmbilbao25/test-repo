package com.bilbao.ecommerce.order;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * A placed order.
 *
 * <p>productName and unitPrice are copied from the Product Service at the time
 * the order was placed, rather than looked up again on every read. That is
 * deliberate: an order is a record of what was agreed, and a later price change
 * must not silently rewrite it.
 */
public record Order(String id,
                    long productId,
                    String productName,
                    int quantity,
                    BigDecimal unitPrice,
                    BigDecimal subtotal,
                    BigDecimal tax,
                    BigDecimal shipping,
                    BigDecimal total,
                    String currency,
                    String servedByProductInstance,
                    Instant placedAt) {
}
