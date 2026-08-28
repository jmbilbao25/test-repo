package com.bilbao.ecommerce.product;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.stereotype.Repository;

/**
 * An in-memory catalogue.
 *
 * <p>A real service would talk to a database. This assignment is about service
 * discovery and configuration, and a database would add a moving part without
 * changing anything either of those does, so the catalogue is a fixed map.
 */
@Repository
public class ProductRepository {

    private final Map<Long, Product> products = new LinkedHashMap<>();

    public ProductRepository() {
        add(new Product(1, "Wireless Mouse", "Peripherals", new BigDecimal("899.00"), 42));
        add(new Product(2, "Mechanical Keyboard", "Peripherals", new BigDecimal("3450.00"), 18));
        add(new Product(3, "27-inch Monitor", "Displays", new BigDecimal("12999.00"), 7));
        add(new Product(4, "USB-C Hub", "Accessories", new BigDecimal("1650.00"), 3));
        add(new Product(5, "Laptop Stand", "Accessories", new BigDecimal("1200.00"), 25));
        add(new Product(6, "Noise-cancelling Headset", "Audio", new BigDecimal("5799.00"), 11));
        add(new Product(7, "1080p Webcam", "Video", new BigDecimal("2450.00"), 2));
        add(new Product(8, "Laptop Sleeve 14-inch", "Accessories", new BigDecimal("749.00"), 30));
    }

    private void add(Product p) {
        products.put(p.id(), p);
    }

    public List<Product> findAll() {
        return List.copyOf(products.values());
    }

    public Optional<Product> findById(long id) {
        return Optional.ofNullable(products.get(id));
    }
}
