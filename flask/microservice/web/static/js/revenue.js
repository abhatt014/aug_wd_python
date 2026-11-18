/* =========================================================
   revenue.js — revenue report: date presets, totals, CSV download.

   CSV download works the same with or without Flask: it reads the
   rows that are currently shown in the table and saves them as a
   .csv file that opens in Excel.

     <button data-csv="#dailyTable" data-filename="daily-revenue">

   In demo mode the date filter also hides rows outside the range and
   recalculates the tables. In Flask the filter form is a normal GET
   form (/admin/revenue?from=2026-11-01&to=2026-11-05) and your SQL
   query does the work.
   ========================================================= */
(function () {
  "use strict";
  const { rupee, DEMO, toast } = window.App;
  const form = document.getElementById("revenueFilter");
  if (!form) return;
  const from = form.elements.from, to = form.elements.to;

  // ---------- Date presets ----------
  const iso = d => d.toISOString().slice(0, 10);
  document.querySelectorAll("[data-range]").forEach(b => b.addEventListener("click", () => {
    const today = new Date(to.dataset.today || iso(new Date()));
    const start = new Date(today);
    const r = b.dataset.range;
    if (r === "today") { /* same day */ }
    else if (r === "month") start.setDate(1);
    else start.setDate(start.getDate() - (Number(r) - 1));
    from.value = iso(start);
    to.value = iso(today);
    form.requestSubmit();
  }));

  // ---------- Totals from the visible order rows ----------
  function totals() {
    const rows = [...document.querySelectorAll("#ordersReport tbody tr[data-row]")].filter(r => !r.hidden);
    const revenue = rows.reduce((s, r) => s + Number(r.dataset.total), 0);
    set("revTotal", rupee(revenue));
    set("revOrders", rows.length);
    set("revAvg", rows.length ? rupee(revenue / rows.length) : rupee(0));
    set("ordersFootTotal", rupee(revenue));
    return rows;
  }
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };

  // ---------- Demo: filter + rebuild daily and item tables ----------
  function demoFilter() {
    const f = from.value, t = to.value;
    document.querySelectorAll("#ordersReport tbody tr[data-row]").forEach(r => {
      r.hidden = (f && r.dataset.date < f) || (t && r.dataset.date > t);
    });
    const rows = totals();

    // Daily table
    const byDay = {};
    rows.forEach(r => {
      const d = byDay[r.dataset.date] || (byDay[r.dataset.date] = { orders: 0, revenue: 0, label: r.dataset.dateLabel });
      d.orders++; d.revenue += Number(r.dataset.total);
    });
    const daily = document.querySelector("#dailyTable tbody");
    const days = Object.keys(byDay).sort().reverse();
    daily.innerHTML = days.length ? days.map(k => `<tr data-row><td>${byDay[k].label}</td><td class="num">${byDay[k].orders}</td><td class="num" data-csv="${byDay[k].revenue}">${rupee(byDay[k].revenue)}</td></tr>`).join("")
      : `<tr class="no-rows"><td colspan="3">No delivered orders in this period.</td></tr>`;
    set("dailyFootOrders", rows.length);
    set("dailyFootTotal", rupee(rows.reduce((s, r) => s + Number(r.dataset.total), 0)));

    // Items table, from data-items="Pepperoni:3:1347|Garlic Bread:2:298"
    const byItem = {};
    rows.forEach(r => (r.dataset.items || "").split("|").filter(Boolean).forEach(p => {
      const [name, q, amt] = p.split(":");
      const it = byItem[name] || (byItem[name] = { qty: 0, revenue: 0 });
      it.qty += Number(q); it.revenue += Number(amt);
    }));
    const items = document.querySelector("#itemsTable tbody");
    const names = Object.keys(byItem).sort((a, b) => byItem[b].revenue - byItem[a].revenue);
    items.innerHTML = names.length ? names.map(n => `<tr data-row><td>${n}</td><td class="num">${byItem[n].qty}</td><td class="num" data-csv="${byItem[n].revenue}">${rupee(byItem[n].revenue)}</td></tr>`).join("")
      : `<tr class="no-rows"><td colspan="3">No items sold in this period.</td></tr>`;

    const label = document.getElementById("rangeLabel");
    if (label) label.textContent = f && t ? `${fmt(f)} to ${fmt(t)}` : "All time";
    const none = document.querySelector("#ordersReport tr.no-rows");
    if (none) none.hidden = rows.length > 0;
  }
  const fmt = s => new Date(s + "T00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

  window.App.demoHandlers.revenueFilter = () => {
    if (from.value && to.value && from.value > to.value) { toast("The start date is after the end date"); return; }
    demoFilter();
  };

  // ---------- CSV export ----------
  function csvCell(v) {
    v = String(v ?? "").replace(/\s+/g, " ").trim();
    if (/^₹[\d,]+(\.\d+)?$/.test(v)) v = v.replace(/[₹,]/g, ""); // "₹1,645" -> 1645 so Excel can add it up
    return /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
  }
  function tableToCsv(table) {
    const out = [];
    const head = [...table.querySelectorAll("thead th")];
    out.push(head.map(th => csvCell(th.dataset.csv ?? th.textContent)).join(","));
    table.querySelectorAll("tbody tr, tfoot tr").forEach(tr => {
      if (tr.hidden || tr.classList.contains("no-rows")) return;
      const cells = [];
      [...tr.children].forEach(td => {
        cells.push(csvCell(td.dataset.csv ?? td.textContent));
        for (let i = 1; i < (td.colSpan || 1); i++) cells.push(""); // keep columns lined up
      });
      out.push(cells.join(","));
    });
    return out.join("\r\n");
  }
  document.querySelectorAll("[data-csv]").forEach(btn => {
    if (btn.tagName !== "BUTTON") return;
    btn.addEventListener("click", () => {
      const table = document.querySelector(btn.dataset.csv);
      const range = from.value && to.value ? `_${from.value}_to_${to.value}` : "";
      const blob = new Blob(["﻿" + tableToCsv(table)], { type: "text/csv;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${btn.dataset.filename || "report"}${range}.csv`;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
      toast("CSV downloaded");
    });
  });

  if (DEMO) demoFilter(); else totals();
})();
