/* Bilbao Bazaar storefront.
 *
 * Every path below is relative, which is the point worth noticing: the page was
 * served by the gateway, so /api/products resolves against the same origin and
 * the browser makes an ordinary same-origin request. No service address appears
 * anywhere in this file, and there is no CORS handling, because from the
 * browser's point of view there is only one server.
 */
"use strict";

const peso = new Intl.NumberFormat("en-PH",
  { style: "currency", currency: "PHP" });

/* One wrapper around fetch, so every call updates the trace bar. The headers it
 * reads are added by NGINX, not by the services. */
async function call(path, options = {}) {
  const started = performance.now();
  const response = await fetch(path, options);
  const ms = Math.round(performance.now() - started);

  const method = (options.method || "GET").toUpperCase();
  set("t-request", `${method} ${path}`);
  set("t-status", `${response.status} ${response.statusText}`);
  set("t-served", response.headers.get("x-served-by") || "\u2014");
  set("t-rid", response.headers.get("x-request-id") || "\u2014");
  set("t-time", `${ms} ms`);

  let body = null;
  try { body = await response.json(); } catch { /* empty or not JSON */ }
  return { ok: response.ok, status: response.status, body };
}

function set(id, text) { document.getElementById(id).textContent = text; }

function toast(message, isError) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.className = "toast"; }, 4200);
}

/* --------------------------------------------------------- service status */
async function refreshStatus() {
  const checks = [
    ["pill-gateway", "/health"],
    ["pill-products", "/api/status/products"],
    ["pill-orders", "/api/status/orders"],
  ];
  for (const [id, path] of checks) {
    const pill = document.getElementById(id);
    try {
      const response = await fetch(path);
      pill.className = "pill " + (response.ok ? "up" : "down");
    } catch {
      pill.className = "pill down";
    }
  }
}

/* -------------------------------------------------------------- catalogue */
function stockLabel(stock) {
  if (stock === 0) return ['<span class="stock none">Out of stock</span>', true];
  if (stock <= 5) return [`<span class="stock low">Only ${stock} left</span>`, false];
  return [`<span class="stock">${stock} in stock</span>`, false];
}

async function loadCatalogue() {
  const target = document.getElementById("catalogue");
  const { ok, body } = await call("/api/products");

  if (!ok || !body) {
    target.innerHTML =
      '<p class="muted span">The catalogue could not be loaded \u2014 the ' +
      'gateway answered, but products-service did not.</p>';
    return;
  }

  target.innerHTML = body.products.map((p) => {
    const [label, sold_out] = stockLabel(p.stock);
    const max = Math.max(p.stock, 1);
    return `
      <article class="card">
        <span class="tag">${p.category}</span>
        <h3>${p.name}</h3>
        <div class="price">${peso.format(p.price)}</div>
        <div class="sku">id ${p.id}</div>
        ${label}
        <div class="buy">
          <input type="number" id="q-${p.id}" value="1" min="1" max="${max}"
                 ${sold_out ? "disabled" : ""}>
          <button data-id="${p.id}" ${sold_out ? "disabled" : ""}>
            ${sold_out ? "Unavailable" : "Place order"}
          </button>
        </div>
      </article>`;
  }).join("");

  target.querySelectorAll("button[data-id]").forEach((button) => {
    button.addEventListener("click", () => placeOrder(Number(button.dataset.id)));
  });
}

/* ----------------------------------------------------------------- orders */
async function placeOrder(productId) {
  const quantity = Number(document.getElementById(`q-${productId}`).value) || 1;

  const { ok, status, body } = await call("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, quantity,
                           customer: "web-storefront" }),
  });

  if (ok) {
    toast(`Order ${body.id} confirmed \u2014 ${body.product_name} ` +
          `\u00d7${body.quantity} for ${peso.format(body.total)}`, false);
    await Promise.all([loadOrders(), loadCatalogue()]);
    return;
  }

  /* The services return a JSON object in `detail` for the interesting refusals
   * (out of stock, over the quantity limit, dependency down), so the reason is
   * shown to the customer rather than a bare status code. */
  const detail = body && body.detail;
  const message = !detail ? `Order failed (${status})`
    : typeof detail === "string" ? detail
    : detail.error + (detail.available !== undefined
        ? ` \u2014 only ${detail.available} left` : "");
  toast(message, true);
}

async function loadOrders() {
  const target = document.getElementById("orders");
  const { ok, body } = await call("/api/orders");

  if (!ok || !body || body.count === 0) {
    target.innerHTML = '<p class="muted">No orders yet.</p>';
    return;
  }

  target.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Order</th><th>Product</th><th class="num">Unit</th>
          <th class="num">Qty</th><th class="num">Total</th>
          <th>Priced by</th><th>Request ID</th>
        </tr>
      </thead>
      <tbody>
        ${body.orders.map((o) => `
          <tr>
            <td>#${o.id}</td>
            <td>${o.product_name}</td>
            <td class="num">${peso.format(o.unit_price)}</td>
            <td class="num">${o.quantity}</td>
            <td class="num">${peso.format(o.total)}</td>
            <td>${o.priced_by}</td>
            <td class="rid-cell">${(o.request_id || "").slice(0, 12)}</td>
          </tr>`).join("")}
        <tr class="total-row">
          <td colspan="4">${body.count} order(s)</td>
          <td class="num">${peso.format(body.revenue)}</td>
          <td colspan="2"></td>
        </tr>
      </tbody>
    </table>`;
}

/* ------------------------------------------------------------------- boot */
async function main() {
  await refreshStatus();
  await loadCatalogue();
  await loadOrders();
  setInterval(refreshStatus, 5000);
}

main();
