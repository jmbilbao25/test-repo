"""Bilbao Bazaar - orders microservice.

Accepts and stores orders. It does not hold a copy of the catalogue, which is
the whole point: to price a line item it has to ask the products service, and
that call is the east-west half of the assignment.

Two things about that call are deliberate:

  * It goes to http://products-service:8000 directly, not back out through the
    gateway. Compose puts both containers on one network and resolves the
    service name, so the internal hop skips the gateway entirely.
  * It forwards the X-Request-ID it was given. The gateway mints the ID, this
    service passes it on, and the products service logs it, so one customer
    request leaves a trail with the same ID in three separate containers.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

SERVICE = "orders-service"
INSTANCE = os.getenv("HOSTNAME", "unknown")

# The dependency arrives as configuration, never as a literal in the code. In
# compose it is the service name; in another environment it could be a load
# balancer, and nothing in this file would change.
PRODUCTS_BASE_URL = os.getenv("PRODUCTS_BASE_URL", "http://products-service:8000")
MAX_QUANTITY = int(os.getenv("MAX_QUANTITY_PER_ORDER", "10"))
# Short on purpose. A dependency that has stopped answering should surface as a
# fast 503, not as a request that hangs until the client gives up.
TIMEOUT = float(os.getenv("PRODUCTS_TIMEOUT_SECONDS", "3.0"))

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format=f"%(asctime)s  {SERVICE}    %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(SERVICE)


class PrettyJSON(JSONResponse):
    """Indented JSON, so a captured response is readable at figure scale."""

    def render(self, content: Any) -> bytes:
        return json.dumps(content, indent=2).encode()


app = FastAPI(
    title="Bilbao Bazaar Orders Service",
    description="Order capture. Prices every line through the products service.",
    version="1.0.0",
    default_response_class=PrettyJSON,
)

ORDERS: dict[int, dict[str, Any]] = {}
_next_id = [5001]


class OrderRequest(BaseModel):
    product_id: int = Field(..., examples=[1001])
    quantity: int = Field(1, ge=1, examples=[2])
    customer: str = Field("walk-in", max_length=60)


@app.exception_handler(StarletteHTTPException)
async def pretty_errors(request: Request, exc: StarletteHTTPException):
    """Indent error bodies too; default_response_class only covers the routes.

    It matters more here than in the catalogue, because the interesting refusals
    put a whole object in `detail` and a compact one-line version of it is hard
    to read.
    """
    return PrettyJSON({"detail": exc.detail}, status_code=exc.status_code)


@app.middleware("http")
async def trace(request: Request, call_next):
    rid = request.headers.get("x-request-id", "-")
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Service"] = SERVICE
    log.info("rid=%s  %s %s -> %s",
             rid, request.method, request.url.path, response.status_code)
    return response


async def fetch_product(product_id: int, rid: str) -> dict[str, Any]:
    """Ask the products service about one product.

    Every failure mode is translated into a status code the caller can act on.
    Letting an httpx exception escape would surface as a 500, which tells a
    client nothing about whose fault it was.
    """
    url = f"{PRODUCTS_BASE_URL}/products/{product_id}"
    log.info("rid=%s  -> GET %s", rid, url)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            reply = await client.get(
                url, headers={"X-Request-ID": rid, "X-Called-By": SERVICE})
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        log.warning("rid=%s  products-service unreachable: %s", rid, exc)
        raise HTTPException(
            status_code=503,
            detail={"error": "products service unavailable",
                    "dependency": PRODUCTS_BASE_URL,
                    "hint": "the catalogue container is not answering, so the "
                            "order cannot be priced",
                    "reason": type(exc).__name__}) from exc
    except httpx.ReadTimeout as exc:
        raise HTTPException(
            status_code=504,
            detail={"error": "products service timed out",
                    "dependency": PRODUCTS_BASE_URL,
                    "timeout_seconds": TIMEOUT}) from exc

    if reply.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f"product {product_id} is not in the catalogue")
    if reply.status_code >= 500:
        raise HTTPException(
            status_code=502,
            detail={"error": "products service returned an error",
                    "upstream_status": reply.status_code})
    return reply.json()


@app.get("/health", tags=["ops"])
def health() -> dict[str, Any]:
    return {"service": SERVICE, "status": "up", "instance": INSTANCE,
            "orders": len(ORDERS), "depends_on": PRODUCTS_BASE_URL}


@app.get("/orders/dependency", tags=["ops"])
async def dependency() -> dict[str, Any]:
    """What this service knows about the one it depends on.

    Resolving the name here is the evidence that discovery is happening through
    the container network rather than through anything hard-coded: the address
    is a name in configuration, and the IP underneath it is assigned by the
    network at run time.
    """
    host = urlparse(PRODUCTS_BASE_URL).hostname or ""
    try:
        address = socket.gethostbyname(host)
        resolved = True
    except socket.gaierror as exc:
        address, resolved = f"unresolved ({exc.strerror})", False

    probe: dict[str, Any] = {"reachable": False}
    if resolved:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                reply = await client.get(f"{PRODUCTS_BASE_URL}/health")
            probe = {"reachable": True, "status_code": reply.status_code,
                     "body": reply.json()}
        except httpx.HTTPError as exc:
            probe = {"reachable": False, "error": type(exc).__name__}

    return {"service": SERVICE, "instance": INSTANCE,
            "configured_dependency": PRODUCTS_BASE_URL,
            "dns_name": host, "resolved_to": address,
            "health_probe": probe}


@app.get("/orders", tags=["orders"])
def list_orders() -> dict[str, Any]:
    orders = sorted(ORDERS.values(), key=lambda o: o["id"])
    return {"count": len(orders), "served_by": SERVICE,
            "revenue": round(sum(o["total"] for o in orders), 2),
            "orders": orders}


@app.get("/orders/{order_id}", tags=["orders"])
def get_order(order_id: int) -> dict[str, Any]:
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404,
                            detail=f"no order with id {order_id}")
    return order


@app.post("/orders", status_code=201, tags=["orders"])
async def place_order(body: OrderRequest, request: Request) -> dict[str, Any]:
    """Create an order, pricing it through the products service."""
    rid = request.headers.get("x-request-id", "-")

    if body.quantity > MAX_QUANTITY:
        raise HTTPException(
            status_code=422,
            detail={"error": "quantity above the configured maximum",
                    "requested": body.quantity, "maximum": MAX_QUANTITY})

    product = await fetch_product(body.product_id, rid)

    if product["stock"] == 0:
        raise HTTPException(
            status_code=409,
            detail={"error": "out of stock", "product": product["name"],
                    "product_id": product["id"]})
    if body.quantity > product["stock"]:
        raise HTTPException(
            status_code=409,
            detail={"error": "not enough stock", "product": product["name"],
                    "requested": body.quantity, "available": product["stock"]})

    order_id = _next_id[0]
    _next_id[0] += 1
    unit = float(product["price"])
    order = {
        "id": order_id,
        "customer": body.customer,
        "product_id": product["id"],
        "product_name": product["name"],
        "unit_price": unit,
        "quantity": body.quantity,
        "total": round(unit * body.quantity, 2),
        "currency": product.get("currency", "PHP"),
        "status": "CONFIRMED",
        "placed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
        # Recorded on the order itself, so the trail survives the log buffer.
        "priced_by": product.get("served_by", "products-service"),
        "request_id": rid,
    }
    ORDERS[order_id] = order
    log.info("rid=%s  order %s confirmed: %s x%s = %.2f",
             rid, order_id, product["name"], body.quantity, order["total"])
    return order
