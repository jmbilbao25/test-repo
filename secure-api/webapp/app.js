/*
 * The demo client.
 *
 * It signs in against POST /auth/token, keeps the access token in memory, and
 * sends it as a bearer header on every call. What is worth noticing is how it
 * handles the three refusals: a 401 means the token is no longer good and the
 * user is sent back to the sign-in screen, a 403 means this token may not do
 * that and the control is disabled, and a 429 means slow down.
 *
 * The token is deliberately not put in localStorage. Anything stored there is
 * readable by any script on the page, so a single injected script could take it.
 * Keeping it in a variable means it is gone when the tab closes, which is the
 * right trade for a short lived token.
 */

const API = window.location.origin;

const session = {
  accessToken: null,
  refreshToken: null,
  username: null,
  scopes: [],
  can(scope) {
    return this.scopes.includes(scope);
  },
};

const el = (id) => document.getElementById(id);
const peso = (n) =>
  "\u20b1" + n.toLocaleString("en-PH", { minimumFractionDigits: 2 });

// ----------------------------------------------------------------- requests
async function call(path, options = {}) {
  const headers = Object.assign({}, options.headers);
  if (session.accessToken) {
    headers.Authorization = "Bearer " + session.accessToken;
  }
  if (options.body) headers["Content-Type"] = "application/json";

  const response = await fetch(API + path, Object.assign({}, options, { headers }));

  if (response.status === 401) {
    // The token is missing, expired or not trusted. Nothing to do but sign in.
    signOut("Your session has expired. Please sign in again.");
    throw new Error("unauthorised");
  }

  const text = await response.text();
  const body = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const error = new Error((body && body.message) || response.statusText);
    error.status = response.status;
    error.code = body && body.error;
    if (response.status === 429) {
      error.retryAfter = (body && body.retry_after_seconds) || 60;
    }
    throw error;
  }
  return body;
}

// ------------------------------------------------------------------ sign in
el("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = el("login-error");
  error.hidden = true;

  // The token endpoint takes form fields, not JSON: that is what the OAuth2
  // password grant specifies.
  const form = new URLSearchParams({
    username: el("username").value,
    password: el("password").value,
  });

  try {
    const response = await fetch(API + "/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    const body = await response.json();

    if (!response.ok) {
      error.textContent =
        response.status === 429
          ? body.message + " (" + body.limit + ")"
          : body.message;
      error.hidden = false;
      return;
    }

    session.accessToken = body.access_token;
    session.refreshToken = body.refresh_token;
    session.scopes = body.scope ? body.scope.split(" ") : [];

    const me = await call("/auth/me");
    session.username = me.username;

    el("who").textContent = me.full_name + " (" + me.username + ")";
    el("scopes").textContent = session.scopes.join(" \u00b7 ") || "no scopes";

    el("login").hidden = true;
    el("dashboard").hidden = false;
    applyPermissions();
    await refreshView();
  } catch (problem) {
    error.textContent = "Could not reach the API: " + problem.message;
    error.hidden = false;
  }
});

function signOut(message) {
  session.accessToken = null;
  session.refreshToken = null;
  session.scopes = [];
  el("dashboard").hidden = true;
  el("login").hidden = false;
  const error = el("login-error");
  if (message) {
    error.textContent = message;
    error.hidden = false;
  }
}

el("signout").addEventListener("click", () => signOut(null));

// --------------------------------------------------------------- the screen
function applyPermissions() {
  // Hiding what a token cannot do is a courtesy, not a security measure. The
  // API refuses these calls whatever the page allows.
  const canWrite = session.can("reports:write");
  el("add-form").hidden = !canWrite;
  document.querySelectorAll(".delete").forEach((button) => {
    button.disabled = !session.can("reports:delete");
  });
}

function notify(message, kind) {
  const notice = el("notice");
  notice.textContent = message;
  notice.className = "notice " + (kind || "");
  notice.hidden = false;
}

async function refreshView() {
  const [list, summary] = await Promise.all([
    call("/reports"),
    call("/reports/summary"),
  ]);

  el("totals").innerHTML = [
    tile("Reports", summary.report_count),
    tile("Total", peso(summary.total_amount)),
    tile("Largest", summary.largest ? summary.largest.title : "\u2014"),
  ].join("");

  const body = document.querySelector("#reports tbody");
  body.innerHTML = "";
  list.reports.forEach((report) => {
    const row = document.createElement("tr");
    row.innerHTML =
      "<td>" + report.id + "</td>" +
      "<td>" + escapeHtml(report.title) + "</td>" +
      "<td>" + escapeHtml(report.category) + "</td>" +
      '<td class="right">' + peso(report.amount) + "</td>" +
      '<td><span class="pill ' + report.status + '">' + report.status +
        "</span></td>" +
      "<td>" + escapeHtml(report.submitted_by) + "</td>" +
      '<td><button class="delete" data-id="' + report.id +
        '" type="button">Delete</button></td>';
    body.appendChild(row);
  });

  document.querySelectorAll(".delete").forEach((button) => {
    button.addEventListener("click", () => remove(button.dataset.id));
  });
  applyPermissions();
}

function tile(label, value) {
  return (
    '<div class="tile"><span class="label">' + label +
    '</span><span class="value">' + value + "</span></div>"
  );
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ----------------------------------------------------------------- actions
el("add-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await call("/reports", {
      method: "POST",
      body: JSON.stringify({
        title: el("new-title").value,
        category: el("new-category").value,
        amount: Number(el("new-amount").value),
      }),
    });
    el("new-title").value = "";
    el("new-amount").value = "";
    notify("Report added.", "ok");
    await refreshView();
  } catch (problem) {
    handle(problem);
  }
});

async function remove(id) {
  try {
    await call("/reports/" + id, { method: "DELETE" });
    notify("Report " + id + " deleted.", "ok");
    await refreshView();
  } catch (problem) {
    handle(problem);
  }
}

function handle(problem) {
  if (problem.message === "unauthorised") return;
  if (problem.status === 403) {
    notify("Refused: " + problem.message, "warn");
  } else if (problem.status === 429) {
    notify(
      "Rate limited. " + problem.message + " Retry in " +
        problem.retryAfter + "s.",
      "warn"
    );
  } else {
    notify(problem.message, "warn");
  }
}
