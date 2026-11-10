/* =========================================================
   admin.js — admin pages: table tabs and search, accept / reject /
   process orders, confirm pop-ups, menu availability switches.

   Every action is a normal <form method="post">. In Flask one route
   handles all status changes:

       POST /admin/orders/<id>/status    fields: status, reason (optional)

   In demo mode (data-demo on <body>) the page updates itself instead
   of sending the form. Load after app.js.
   ========================================================= */
(function () {
  "use strict";
  const { toast, DEMO, escapeHtml } = window.App;

  // Order flow. Rejected is only possible from Pending.
  const NEXT = { "Pending": "Accepted", "Accepted": "Preparing", "Preparing": "Out for delivery", "Out for delivery": "Delivered" };
  const NEXT_LABEL = { "Accepted": "Start preparing", "Preparing": "Send out for delivery", "Out for delivery": "Mark delivered" };

  // ---------- Tabs + search over a table ----------
  // <div class="tabs" data-tabs-for="#ordersTable" data-key="status"> <button data-filter="all">..
  // <input type="search" data-search-for="#ordersTable">
  function applyFilters(table) {
    const tabs = document.querySelector(`[data-tabs-for="#${table.id}"]`);
    const search = document.querySelector(`[data-search-for="#${table.id}"]`);
    const key = tabs ? tabs.dataset.key : null;
    const active = tabs ? (tabs.querySelector('[aria-selected="true"]') || {}).dataset?.filter || "all" : "all";
    const q = search ? search.value.trim().toLowerCase() : "";
    let shown = 0;
    table.querySelectorAll("tbody tr[data-row]").forEach(tr => {
      const okTab = active === "all" || tr.dataset[key] === active;
      const okSearch = !q || tr.textContent.toLowerCase().includes(q);
      tr.hidden = !(okTab && okSearch);
      if (!tr.hidden) shown++;
    });
    const none = table.querySelector("tr.no-rows");
    if (none) none.hidden = shown > 0;
    if (tabs) countTabs(tabs, table);
  }

  function countTabs(tabs, table) {
    const key = tabs.dataset.key;
    const rows = [...table.querySelectorAll("tbody tr[data-row]")];
    tabs.querySelectorAll("button").forEach(b => {
      const f = b.dataset.filter;
      const n = f === "all" ? rows.length : rows.filter(r => r.dataset[key] === f).length;
      let c = b.querySelector(".c");
      if (!c) { c = document.createElement("span"); c.className = "c"; b.appendChild(c); }
      c.textContent = n;
    });
  }

  document.querySelectorAll("[data-tabs-for]").forEach(tabs => {
    const table = document.querySelector(tabs.dataset.tabsFor);
    // Allow ?status=Pending in the URL to pre-select a tab
    const want = new URLSearchParams(location.search).get(tabs.dataset.key);
    if (want) tabs.querySelectorAll("button").forEach(b => b.setAttribute("aria-selected", String(b.dataset.filter === want)));
    tabs.addEventListener("click", e => {
      const b = e.target.closest("button");
      if (!b) return;
      tabs.querySelectorAll("button").forEach(x => x.setAttribute("aria-selected", String(x === b)));
      applyFilters(table);
    });
    applyFilters(table);
  });
  document.querySelectorAll("[data-search-for]").forEach(input => {
    const table = document.querySelector(input.dataset.searchFor);
    input.addEventListener("input", () => applyFilters(table));
    applyFilters(table);
  });

  // ---------- Update the page after a status change (demo) ----------
  function setOrderStatus(id, to, reason) {
    document.querySelectorAll(`[data-order-id="${id}"]`).forEach(el => {
      el.dataset.status = to;
      el.querySelectorAll(".status").forEach(p => { p.dataset.status = to; p.textContent = to === "Pending" ? "Pending approval" : to; });

      // Table row in "All orders"
      const acts = el.querySelector("[data-actions]");
      if (acts && el.matches("tr")) {
        acts.innerHTML = `<a class="link" href="${el.dataset.href || "order-detail.html"}">View</a>`;
      }
      // Card in the dashboard queue
      if (el.matches(".qcard")) {
        el.classList.add("is-done");
        el.querySelector(".acts").innerHTML = `<span class="status" data-status="${to}">${to}</span>`;
      }
      // "Next step" form in the in-progress table
      const nf = el.querySelector("form[data-next-form]");
      if (nf) {
        if (NEXT[to]) {
          nf.elements.status.value = NEXT[to];
          nf.querySelector("button").textContent = NEXT_LABEL[to] || NEXT[to];
        } else {
          nf.replaceWith(Object.assign(document.createElement("span"), { className: "hint", textContent: "Done" }));
        }
      }
      // Order detail page
      if (el.matches("[data-order-detail]")) syncDetail(el, reason);
    });

    // Refresh tab counts and the pending badge
    document.querySelectorAll("[data-tabs-for]").forEach(t => applyFilters(document.querySelector(t.dataset.tabsFor)));
    const pending = new Set([...document.querySelectorAll('[data-order-id][data-status="Pending"]')].map(e => e.dataset.orderId));
    if (document.querySelector("[data-order-id]")) {
      document.querySelectorAll("[data-pending-count]").forEach(b => {
        b.textContent = pending.size;
        if (b.classList.contains("badge")) b.hidden = pending.size === 0;
      });
    }
    const queue = document.querySelector("[data-queue]");
    if (queue) {
      const left = queue.querySelectorAll('.qcard[data-status="Pending"]').length;
      const empty = document.querySelector("[data-queue-empty]");
      if (empty) empty.hidden = left > 0;
    }
  }

  // ---------- Order detail: show the right action for the status ----------
  const STEPS = ["Pending", "Accepted", "Preparing", "Out for delivery", "Delivered"];
  function syncDetail(root, reason) {
    const s = root.dataset.status;
    root.querySelectorAll("[data-when]").forEach(el => {
      el.hidden = !el.dataset.when.split("|").includes(s);
    });
    const idx = STEPS.indexOf(s);
    root.querySelectorAll(".tracker li").forEach((li, i) => {
      li.classList.toggle("done", s !== "Rejected" && i < idx);
      li.classList.toggle("now", s !== "Rejected" && i === idx);
    });
    if (reason !== undefined) {
      const tl = root.querySelector(".timeline");
      if (tl) {
        const t = new Date().toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });
        const li = document.createElement("li");
        li.innerHTML = `${escapeHtml(s === "Rejected" ? "Rejected: " + reason : s)}<time>Today, ${t} by you</time>`;
        tl.prepend(li);
      }
      const r = root.querySelector("[data-reject-reason]");
      if (r && s === "Rejected") { r.textContent = "Reason given to the customer: " + reason; r.hidden = false; }
    }
  }
  document.querySelectorAll("[data-order-detail]").forEach(el => syncDetail(el));

  // Demo handler for every status form:  <form data-demo="status" data-order="1048">
  window.App.demoHandlers.status = form => {
    const id = form.dataset.order;
    const to = form.elements.status.value;
    const reason = form.elements.reason ? form.elements.reason.value.trim() : "";
    setOrderStatus(id, to, reason);
    const dlg = form.closest("dialog");
    if (dlg) dlg.close();
    toast(to === "Rejected" ? `Order #${id} rejected` : to === "Accepted" ? `Order #${id} accepted` : `Order #${id}: ${to}`);
  };

  // ---------- Reject dialog ----------
  const rejectDlg = document.getElementById("rejectDialog");
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-reject]");
    if (b && rejectDlg) {
      const form = rejectDlg.querySelector("form");
      form.action = b.dataset.action;          // e.g. /admin/orders/1048/status
      form.dataset.order = b.dataset.reject;
      form.reset();
      form.querySelectorAll(".invalid").forEach(f => f.classList.remove("invalid"));
      rejectDlg.querySelector("[data-reject-title]").textContent = `Reject order #${b.dataset.reject}?`;
      rejectDlg.showModal();
      return;
    }
    const r = e.target.closest(".reasons button");
    if (r) {
      const ta = r.closest("form").elements.reason;
      ta.value = r.textContent;
      ta.dispatchEvent(new Event("input", { bubbles: true }));
      ta.focus();
      return;
    }
    if (e.target.closest("[data-close-dialog]")) e.target.closest("dialog").close();
  });

  // ---------- Confirm before a dangerous form is sent ----------
  // <form data-confirm="Delete Margherita from the menu?">
  const confirmDlg = document.getElementById("confirmDialog");
  let pending = null;
  document.addEventListener("submit", e => {
    const form = e.target;
    if (!form.dataset.confirm || form.dataset.confirmed === "yes" || !confirmDlg) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    pending = form;
    confirmDlg.querySelector("[data-confirm-text]").textContent = form.dataset.confirm;
    confirmDlg.showModal();
  }, true);
  if (confirmDlg) {
    confirmDlg.querySelector("[data-confirm-yes]").addEventListener("click", () => {
      confirmDlg.close();
      if (!pending) return;
      pending.dataset.confirmed = "yes";
      pending.requestSubmit();
      delete pending.dataset.confirmed;
      pending = null;
    });
  }

  // ---------- Menu: availability switches send their form on change ----------
  document.addEventListener("change", e => {
    if (e.target.matches("[data-autosubmit]")) e.target.form.requestSubmit();
  });
  window.App.demoHandlers.availability = form => {
    const on = form.elements.available.checked;
    const row = form.closest("tr");
    const label = row.querySelector("[data-avail-label]");
    if (label) label.textContent = on ? "On menu" : "Sold out";
    row.dataset.avail = on ? "on" : "off";
    toast(`${row.dataset.name} is ${on ? "back on the menu" : "marked sold out"}`);
  };
  window.App.demoHandlers.remove = form => {
    const row = form.closest("tr");
    const name = row.dataset.name || "Item";
    row.remove();
    document.querySelectorAll("[data-search-for]").forEach(i => applyFilters(document.querySelector(i.dataset.searchFor)));
    toast(`${name} deleted`);
  };
  window.App.demoHandlers.saveItem = form => {
    window.App.store.set("crust_flash", `${form.elements.name.value} saved`);
    location.href = form.dataset.next;
  };
  // ---------- Menu item form: live preview ----------
  const itemForm = document.getElementById("itemForm");
  const preview = document.getElementById("itemPreview");
  if (itemForm && preview) {
    const f = itemForm.elements;
    const upd = () => {
      const type = (itemForm.querySelector('input[name="type"]:checked') || {}).value;
      const isPizza = f.category.value === "pizza";
      preview.querySelector("[data-p-name]").textContent = f.name.value || "Item name";
      preview.querySelector("[data-p-desc]").textContent = f.description.value || "Short description";
      preview.querySelector("[data-p-price]").textContent = window.App.rupee(f.price.value);
      const mark = preview.querySelector("[data-p-mark]");
      mark.hidden = !isPizza;
      mark.className = "mark " + (type === "nonveg" ? "nonveg" : "veg");
      const tag = preview.querySelector("[data-p-tag]");
      const t = f.available.checked ? f.tag.value : "Sold out";
      tag.textContent = t; tag.hidden = !t;
      preview.classList.toggle("sold-out", !f.available.checked);
    };
    itemForm.addEventListener("input", upd);
    itemForm.addEventListener("change", upd);
    upd();
  }

  const flash = window.App.store.get("crust_flash", null);
  if (flash && DEMO) { window.App.store.remove("crust_flash"); toast(flash); }
})();
