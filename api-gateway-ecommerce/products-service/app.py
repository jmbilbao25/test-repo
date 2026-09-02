"""Bilbao Bazaar - products microservice.

Owns the catalogue and nothing else. It never calls another service, so it sits
at the bottom of the dependency graph: requests arrive either from the API
gateway, because a customer is browsing, or from the orders service, because it
needs a price before it will accept an order.

Every response carries back the X-Request-ID it was handed, and every log line
prints it. That one header is what makes a single customer request traceable
across all three containers.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

SERVICE = "products-service"
# Compose gives every container a hostname; inside the container it lands in
# $HOSTNAME. Reporting it makes it obvious which replica answered.
INSTANCE = os.getenv("HOSTNAME", "unknown")

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format=f"%(asctime)s  {SERVICE}  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(SERVICE)


class PrettyJSON(JSONResponse):
    """Indented JSON.

    Compact JSON is correct and unreadable. Since every response here ends up
    either in a terminal capture or in a browser screenshot, the two extra
    kilobytes buy a figure somebody can actually read.
    """

    def render(self, content: Any) -> bytes:
        return json.dumps(content, indent=2).encode()


app = FastAPI(
    title="Bilbao Bazaar Products Service",
    description="Catalogue ownership: products, prices and stock levels.",
    version="1.0.0",
    default_response_class=PrettyJSON,
)

# Stock levels are chosen so the order rules have something to refuse:
# 1006 is out of stock entirely, and 1004 has fewer units than a test order asks
# for. Without those two rows every request succeeds and the validation code is
# never shown doing anything.
CATALOGUE: dict[int, dict[str, Any]] = {
    1001: {"id": 1001, "name": "Bamboo Cutting Board",
           "category": "Kitchen", "price": 749.00, "stock": 24},
    1002: {"id": 1002, "name": "Cast Iron Skillet 10in",
           "category": "Kitchen", "price": 1895.00, "stock": 8},
    1003: {"id": 1003, "name": "Barako Coffee Beans 1kg",
           "category": "Pantry", "price": 620.00, "stock": 52},
    1004: {"id": 1004, "name": "Buri Storage Basket",
           "category": "Home", "price": 480.00, "stock": 3},
    1005: {"id": 1005, "name": "Abaca Table Runner",
           "category": "Home", "price": 395.00, "stock": 17},
    1006: {"id": 1006, "name": "Stainless Tumbler 500ml",
           "category": "Kitchen", "price": 559.00, "stock": 0},
    1007: {"id": 1007, "name": "Calamansi Marmalade 250g",
           "category": "Pantry", "price": 185.00, "stock": 41},
    1008: {"id": 1008, "name": "Handwoven Placemat Set",
           "category": "Home", "price": 690.00, "stock": 6},
}

CURRENCY = os.getenv("STORE_CURRENCY", "PHP")


@app.exception_handler(StarletteHTTPException)
async def pretty_errors(request: Request, exc: StarletteHTTPException):
    """Indent error bodies too.

    default_response_class only covers the routes. Without this, every success
    came back indented and every 404 came back as one compact line, which is a
    silly thing for two figures side by side to disagree about.
    """
    return PrettyJSON({"detail": exc.detail}, status_code=exc.status_code)


@app.middleware("http")
async def trace(request: Request, call_next):
    """Echo the correlation ID back, and log it against the request."""
    rid = request.headers.get("x-request-id", "-")
    caller = request.headers.get("x-called-by", "gateway")
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Service"] = SERVICE
    log.info("rid=%s  from=%-14s %s %s -> %s",
             rid, caller, request.method, request.url.path,
             response.status_code)
    return response


@app.get("/health", tags=["ops"])
def health() -> dict[str, Any]:
    return {"service": SERVICE, "status": "up", "instance": INSTANCE,
            "products": len(CATALOGUE)}


@app.get("/products", tags=["catalogue"])
def list_products(category: str | None = None,
                  in_stock: bool = False) -> dict[str, Any]:
    items = list(CATALOGUE.values())
    if category:
        items = [p for p in items if p["category"].lower() == category.lower()]
    if in_stock:
        items = [p for p in items if p["stock"] > 0]
    return {"currency": CURRENCY, "count": len(items),
            "served_by": SERVICE, "products": items}


@app.get("/products/categories", tags=["catalogue"])
def categories() -> dict[str, Any]:
    names = sorted({p["category"] for p in CATALOGUE.values()})
    return {"count": len(names), "categories": names}


@app.get("/products/{product_id}", tags=["catalogue"])
def get_product(product_id: int) -> dict[str, Any]:
    """One product.

    This is the endpoint the orders service calls. A 404 here is what makes an
    order for a product that does not exist fail with a 404 rather than a 500.
    """
    product = CATALOGUE.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"no product with id {product_id} in the catalogue")
    return {"currency": CURRENCY, "served_by": SERVICE, **product}
