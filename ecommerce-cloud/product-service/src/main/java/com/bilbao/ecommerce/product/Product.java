package com.bilbao.ecommerce.product;

import java.math.BigDecimal;

/**
 * A catalogue entry. A record because it is immutable data and nothing here
 * needs a setter.
 */
public record Product(long id, String name, String category,
                      BigDecimal price, int stock) {
}
