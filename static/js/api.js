// Minimal fetch wrapper that adds the CSRF token and unwraps JSON errors.
window.LGApi = (function () {
  "use strict";
  const csrf = () => document.querySelector('meta[name="csrf-token"]').content;

  async function request(method, url, body) {
    const opts = { method, headers: { "X-CSRF-Token": csrf(), Accept: "application/json" }, credentials: "same-origin" };
    if (body instanceof FormData) {
      opts.body = body;
    } else if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(url, opts);
    let data = null;
    try { data = await resp.json(); } catch (_) { /* non-JSON */ }
    if (resp.status === 401) { location.href = "/login?next=" + encodeURIComponent(location.pathname); }
    if (!resp.ok || (data && data.ok === false)) {
      throw new Error((data && data.error) || `${resp.status} ${resp.statusText}`);
    }
    return data;
  }
  return {
    get: (u) => request("GET", u),
    post: (u, b) => request("POST", u, b === undefined ? {} : b),
    del: (u) => request("DELETE", u),
  };
})();
