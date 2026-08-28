package com.bilbao.ecommerce.product;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * The {@code catalog.*} values, which arrive from
 * {@code config-repo/product-service.yml} by way of the Config Server.
 *
 * <p>{@code @RefreshScope} is the part that matters for Step 3. Without it these
 * values are bound once at startup and a configuration change needs a restart to
 * take effect. With it, the bean is thrown away and rebuilt the next time it is
 * used after {@code POST /actuator/refresh}, so an edit to the YAML reaches a
 * running service.
 */
@Component
@RefreshScope
@ConfigurationProperties(prefix = "catalog")
public class CatalogProperties {

    /** Banner text shown with the catalogue. Changed in Step 3 to prove refresh works. */
    private String featuredMessage = "(not configured)";

    /** How many products a page of the catalogue holds. */
    private int pageSize = 10;

    /** At or below this quantity a product is reported as low stock. */
    private int lowStockThreshold = 1;

    public String getFeaturedMessage() {
        return featuredMessage;
    }

    public void setFeaturedMessage(String featuredMessage) {
        this.featuredMessage = featuredMessage;
    }

    public int getPageSize() {
        return pageSize;
    }

    public void setPageSize(int pageSize) {
        this.pageSize = pageSize;
    }

    public int getLowStockThreshold() {
        return lowStockThreshold;
    }

    public void setLowStockThreshold(int lowStockThreshold) {
        this.lowStockThreshold = lowStockThreshold;
    }
}
