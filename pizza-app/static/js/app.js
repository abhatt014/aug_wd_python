/* =========================================================
   app.js — shared helpers for every page.

   DEMO MODE
   ---------
   When <body> has the attribute  data-demo , the pages run on their own
   in a browser with no server:
     - forms are not sent anywhere; a small handler fakes the result
     - "who is logged in" is kept in the browser (localStorage)
     - blocks marked data-auth="guest" / "user" / "admin" show or hide

   When you move a page into Flask, delete  data-demo  from <body>.
   Forms then submit normally to their action="" URL, and you render
   the right data-auth block with Jinja ({% if session.user_id %} ...).
   Nothing in this file calls a server.
   ========================================================= */
(function () {
  "use strict";

  const DEMO = document.body.hasAttribute("data-demo");

  // ---- Safe browser storage (falls back to memory if blocked) ----
  const memory = {};
  const store = {
    get(key, fallback) {
      try {
        const raw = localStorage.getItem(key);
        return raw === null ? fallback : JSON.parse(raw);
      } catch (e) {
        return key in memory ? memory[key] : fallback;
      }
    },
    set(key, value) {
      memory[key] = value;
      try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* ignore */ }
    },
    remove(key) {
      delete memory[key];
      try { localStorage.removeItem(key); } catch (e) { /* ignore */ }
    }
  };

  // ---- Money ----
  const rupee = n => "₹" + Math.round(Number(n) || 0).toLocaleString("en-IN");

  // ---- Toast message ----
  let toastTimer;
  function toast(msg) {
    let el = document.querySelector(".toast");
    if (!el) {
      el = document.createElement("div");
      el.className = "toast";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.textContent = msg;
    requestAnimationFrame(() => el.classList.add("show"));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 2600);
  }

  // ---- Demo login state ----
  const USER_KEY = "crust_demo_user";
  const getUser = () => store.get(USER_KEY, null);
  const setUser = u => { u ? store.set(USER_KEY, u) : store.remove(USER_KEY); applyAuth(); };

  function applyAuth() {
    if (!DEMO) return; // Flask decides what to render
    const u = getUser();
    document.querySelectorAll("[data-auth]").forEach(el => {
      const want = el.dataset.auth;
      const show = want === "guest" ? !u
                 : want === "user" ? !!u
                 : want === "admin" ? !!(u && u.is_admin)
                 : want === "customer" ? !!(u && !u.is_admin)
                 : true;
      el.hidden = !show;
    });
    if (u) document.querySelectorAll("[data-user-name]").forEach(el => { el.textContent = u.name; });
    // Pre-fill inputs from the demo user:  <input data-user-fill="name|email|phone|address">
    document.querySelectorAll("[data-user-fill]").forEach(el => {
      const v = u && u[el.dataset.userFill];
      if (v && !el.value) el.value = v;
    });
  }

  // ---- Demo banner ----
  function demoBanner() {
    if (!DEMO || document.body.hasAttribute("data-no-banner")) return;
    const u = getUser();
    const bar = document.createElement("div");
    bar.className = "demo-bar";
    bar.innerHTML = `Demo mode: nothing is sent to a server. ${u ? `Signed in as <strong>${escapeHtml(u.name)}</strong>${u.is_admin ? " (admin)" : ""}.` : "Not signed in."} <button type="button" data-reset-demo>Reset demo</button>`;
    document.body.prepend(bar);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // ---- Demo form handlers ----
  // A form opts in with  data-demo="<handler name>".  Other scripts can add handlers:
  //   App.demoHandlers.myName = (form, event) => { ... }
  const demoHandlers = {
    // Go to another page:  data-demo="next" data-next="page.html"
    next(form) { location.href = form.dataset.next; },
    // Just show a message:  data-demo="toast" data-toast="Saved"
    toast(form) { toast(form.dataset.toast || "Saved"); },

    // Fake login. admin@crustandco.in opens the admin dashboard;
    // any other email logs in as a customer.
    login(form) {
      const email = form.elements.email.value.trim().toLowerCase();
      const isAdmin = email === "admin@crustandco.in";
      const known = {
        "admin@crustandco.in": { name: "Shop owner" },
        "rahul@example.com": { name: "Rahul Sharma", phone: "98100 23456", address: "B-14, Green Park Extension, Your City – 110016" }
      };
      const base = known[email] || { name: niceName(email) };
      setUser({ email, is_admin: isAdmin, ...base });
      location.href = isAdmin ? "admin/dashboard.html" : safeNext(form) || "index.html";
    },

    // Fake registration: the new account is logged in straight away.
    register(form) {
      const f = form.elements;
      setUser({ name: f.name.value.trim(), email: f.email.value.trim(), phone: f.phone.value.trim(), address: f.address.value.trim(), is_admin: false });
      location.href = safeNext(form) || "index.html";
    }
  };

  function niceName(email) {
    const n = email.split("@")[0].replace(/[._-]+/g, " ").trim() || "Customer";
    return n.replace(/\b\w/g, c => c.toUpperCase());
  }
  // Only allow redirects to a page in this site (no "//evil.com")
  function safeNext(form) {
    const n = (form.elements.next && form.elements.next.value) || new URLSearchParams(location.search).get("next") || "";
    return /^[a-z0-9\-/]+\.html(#[\w-]+)?$/i.test(n) ? n : "";
  }
  // Copy ?next=... from the URL into the hidden "next" input and into links
  const nextParam = new URLSearchParams(location.search).get("next");
  if (nextParam) {
    document.querySelectorAll('input[name="next"]').forEach(i => i.value = nextParam);
    document.querySelectorAll("[data-keep-next]").forEach(a => a.href += (a.href.includes("?") ? "&" : "?") + "next=" + encodeURIComponent(nextParam));
  }

  // Runs after validate.js (which listens in the capture phase and stops invalid forms).
  document.addEventListener("submit", e => {
    if (!DEMO || e.defaultPrevented) return;
    const form = e.target;
    const name = form.dataset.demo;
    if (!name) return;
    e.preventDefault();
    const fn = demoHandlers[name];
    if (fn) fn(form, e);
  });

  // ---- Logout + reset (demo only) ----
  document.addEventListener("click", e => {
    const out = e.target.closest("[data-logout]");
    if (out && DEMO) {
      e.preventDefault();
      store.remove(USER_KEY);
      location.href = out.getAttribute("href");
      return;
    }
    if (e.target.closest("[data-reset-demo]")) {
      ["crust_demo_user", "crust_cart", "crust_last_order"].forEach(k => store.remove(k));
      location.reload();
    }
  });

  // ---- "Open now" status from opening hours ----
  function openStatus() {
    document.querySelectorAll("[data-open-status]").forEach(el => {
      const now = new Date(), d = now.getDay(), h = now.getHours();
      const [open, close] = d === 0 ? [12, 23] : (d === 5 || d === 6) ? [11, 24] : [11, 23];
      const isOpen = h >= open && h < close;
      el.textContent = isOpen ? "Open now. We're taking orders." : "Closed right now. You can still place an order for when we open.";
      el.style.color = isOpen ? "var(--basil)" : "var(--tomato)";
    });
  }

  // ---- Password show/hide ----
  document.addEventListener("click", e => {
    const b = e.target.closest(".pw-toggle");
    if (!b) return;
    const input = b.parentElement.querySelector("input");
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    b.textContent = show ? "Hide" : "Show";
    b.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });

  // ---- Init ----
  document.querySelectorAll("[data-year]").forEach(el => el.textContent = new Date().getFullYear());
  document.querySelectorAll("[data-demo-only]").forEach(el => el.hidden = !DEMO);
  applyAuth();
  demoBanner();
  openStatus();

  window.App = { DEMO, store, rupee, toast, getUser, setUser, applyAuth, demoHandlers, escapeHtml };
})();
