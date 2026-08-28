package com.bilbao.ecommerce.product;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * The catalogue API, plus one endpoint that reports the configuration currently
 * in effect so that Step 3 has something to look at.
 */
@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductRepository repository;
    private final CatalogProperties catalog;
    private final StoreProperties store;

    public ProductController(ProductRepository repository,
                             CatalogProperties catalog,
                             StoreProperties store) {
        this.repository = repository;
        this.catalog = catalog;
        this.store = store;
    }

    /** The catalogue, with the configured banner and page size wrapped around it. */
    @GetMapping
    public Map<String, Object> list() {
        List<Product> all = repository.findAll();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("store", store.getName());
        body.put("currency", store.getCurrency());
        // Both of these come from the Config Server, not from this service.
        body.put("featuredMessage", catalog.getFeaturedMessage());
        body.put("pageSize", catalog.getPageSize());
        body.put("count", all.size());
        body.put("products", all.stream().limit(catalog.getPageSize()).toList());
        return body;
    }

    /** One product. This is the endpoint the Order Service calls through Eureka. */
    @GetMapping("/{id}")
    public ResponseEntity<Product> byId(@PathVariable long id) {
        return repository.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /**
     * Everything this service was told by the Config Server.
     *
     * <p>Step 3 reads this before and after editing the YAML, so the effect of
     * {@code POST /actuator/refresh} is visible without having to read the
     * catalogue for a changed banner.
     */
    @GetMapping("/config")
    public Map<String, Object> config() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("source", "Spring Cloud Config Server");
        body.put("store.name", store.getName());
        body.put("store.currency", store.getCurrency());
        body.put("store.taxRate", store.getTaxRate());
        body.put("store.supportEmail", store.getSupportEmail());
        body.put("catalog.featuredMessage", catalog.getFeaturedMessage());
        body.put("catalog.pageSize", catalog.getPageSize());
        body.put("catalog.lowStockThreshold", catalog.getLowStockThreshold());
        return body;
    }

    /** Products at or below the configured low-stock threshold. */
    @GetMapping("/low-stock")
    public Map<String, Object> lowStock() {
        List<Product> low = repository.findAll().stream()
                .filter(p -> p.stock() <= catalog.getLowStockThreshold())
                .toList();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("threshold", catalog.getLowStockThreshold());
        body.put("count", low.size());
        body.put("products", low);
        return body;
    }
}
