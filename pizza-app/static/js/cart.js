/* =========================================================
   cart.js — menu filter, cart drawer and checkout.

   The cart lives in the browser (localStorage) until the customer
   places the order. On the checkout page this script writes the cart
   into hidden inputs, so Flask receives it as normal form data:

       item_id = 3, item_id = 8      -> request.form.getlist("item_id")
       qty     = 2, qty     = 1      -> request.form.getlist("qty")

   Menu items are read from the HTML, so your Jinja loop only has to
   output  <div class="item" data-id=".." data-name=".." data-price="..">.
   Never trust prices from the browser: look them up again in MySQL.
   ========================================================= */
(function () {
  "use strict";
  const { store, rupee, toast, DEMO, getUser, escapeHtml } = window.App;
  const KEY = "crust_cart";

  let cart = store.get(KEY, {}); // { "3": {id, name, price, qty}, ... }
  const save = () => { store.set(KEY, cart); render(); };
  const lines = () => Object.values(cart).filter(l => l.qty > 0);
  const count = () => lines().reduce((s, l) => s + l.qty, 0);
  const subtotal = () => lines().reduce((s, l) => s + l.qty * l.price, 0);

  function add(id, name, price) {
    id = String(id);
    if (!cart[id]) cart[id] = { id, name, price: Number(price), qty: 0 };
    cart[id].qty++;
    save();
  }
  function change(id, delta) {
    if (!cart[id]) return;
    cart[id].qty += delta;
    if (cart[id].qty <= 0) delete cart[id];
    save();
  }

  function linesHtml() {
    return lines().map(l => `
      <div class="line">
        <strong>${escapeHtml(l.name)}</strong><span>${rupee(l.price * l.qty)}</span>
        <span class="qty">
          <button type="button" data-dec="${l.id}" aria-label="Remove one ${escapeHtml(l.name)}">−</button>
          ${l.qty}
          <button type="button" data-inc="${l.id}" aria-label="Add one ${escapeHtml(l.name)}">+</button>
        </span>
        <span class="hint">${rupee(l.price)} each</span>
      </div>`).join("");
  }

  // ---------- Render everything that shows the cart ----------
  function render() {
    document.querySelectorAll("[data-cart-count]").forEach(el => el.textContent = count());

    // Drawer (home page)
    const drawerLines = document.getElementById("drawerLines");
    if (drawerLines) {
      drawerLines.innerHTML = lines().length ? linesHtml()
        : `<p class="empty">Your order is empty. Add a pizza from the menu to get started.</p>`;
      document.getElementById("drawerTotal").textContent = rupee(subtotal());
      document.getElementById("checkoutBtn").setAttribute("aria-disabled", lines().length ? "false" : "true");
    }

    // Checkout page
    const form = document.getElementById("checkoutForm");
    if (form) {
      const has = lines().length > 0;
      document.getElementById("orderLines").innerHTML = has ? linesHtml()
        : `<p class="empty">Your cart is empty. <a class="link" href="index.html#menu">Go to the menu</a> to add pizzas.</p>`;
      document.getElementById("subtotal").textContent = rupee(subtotal());
      document.getElementById("grandTotal").textContent = rupee(subtotal());
      // Hidden inputs that Flask reads
      document.getElementById("cartInputs").innerHTML = lines().map(l =>
        `<input type="hidden" name="item_id" value="${l.id}"><input type="hidden" name="qty" value="${l.qty}">`).join("");
      form.querySelector('[type="submit"]').disabled = !has;
    }
  }

  // ---------- Clicks ----------
  document.addEventListener("click", e => {
    const addBtn = e.target.closest(".add");
    if (addBtn) {
      const item = addBtn.closest(".item");
      add(item.dataset.id, item.dataset.name, item.dataset.price);
      addBtn.textContent = "Added";
      addBtn.classList.add("added");
      setTimeout(() => { addBtn.textContent = "Add"; addBtn.classList.remove("added"); }, 900);
      return;
    }
    if (e.target.dataset.inc) return change(e.target.dataset.inc, 1);
    if (e.target.dataset.dec) return change(e.target.dataset.dec, -1);

    if (e.target.closest("#cartBtn")) return toggleDrawer(true);
    if (e.target.closest("#closeCart, #scrim")) return toggleDrawer(false);

    // Only logged-in customers can check out. In Flask, the /checkout route
    // does this check with @login_required; here we fake it in demo mode.
    const go = e.target.closest("#checkoutBtn");
    if (go && DEMO && !getUser()) {
      e.preventDefault();
      location.href = "login.html?next=checkout.html";
    }
  });

  function toggleDrawer(open) {
    document.body.classList.toggle("cart-open", open);
    const d = document.getElementById("drawer");
    if (!d) return;
    d.setAttribute("aria-hidden", String(!open));
    if (open) document.getElementById("closeCart").focus();
  }
  document.addEventListener("keydown", e => { if (e.key === "Escape") toggleDrawer(false); });

  // ---------- Menu filter chips ----------
  const filters = document.querySelector(".filters");
  if (filters) {
    filters.addEventListener("click", e => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      filters.querySelectorAll(".chip").forEach(c => c.setAttribute("aria-pressed", String(c === chip)));
      const f = chip.dataset.filter;
      document.querySelectorAll(".menu .item").forEach(it => {
        it.hidden = !(f === "all" || it.dataset.type === f || it.dataset.category === f);
      });
    });
  }

  // ---------- Demo: placing the order ----------
  window.App.demoHandlers.placeOrder = form => {
    const order = {
      id: 1049,
      items: lines(),
      total: subtotal(),
      address: form.elements.address.value,
      placed_at: new Date().toISOString()
    };
    store.set("crust_last_order", order);
    cart = {};
    store.set(KEY, cart);
    location.href = form.dataset.next;
  };

  // ---------- Demo: show the order just placed ----------
  const placed = document.getElementById("placedItems");
  if (placed && DEMO) {
    const o = store.get("crust_last_order", null);
    if (o && o.items.length) {
      placed.innerHTML = o.items.map(l =>
        `<li><span>${l.qty} × ${escapeHtml(l.name)}</span><span>${rupee(l.qty * l.price)}</span></li>`).join("") +
        `<li class="tot"><span>Total (cash on delivery)</span><span>${rupee(o.total)}</span></li>`;
      document.querySelectorAll("[data-placed-id]").forEach(el => el.textContent = "#" + o.id);
      const a = document.querySelector("[data-placed-address]");
      if (a && o.address) a.textContent = o.address;
    }
  }

  render();
})();
