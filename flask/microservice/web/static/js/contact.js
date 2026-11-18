/* =========================================================
   contact.js — contact form: party fields, character counter,
   earliest party date. The form itself posts to /contact.
   ========================================================= */
(function () {
  "use strict";
  const form = document.getElementById("contactForm");
  if (!form) return;

  // Party fields only show for "Party or bulk order"
  function syncTopic() {
    const t = form.querySelector('input[name="topic"]:checked');
    form.classList.toggle("is-party", !!t && t.value === "Party / bulk order");
  }
  form.addEventListener("change", e => { if (e.target.name === "topic") syncTopic(); });

  // Party date: tomorrow at the earliest
  const date = form.elements.event_date;
  if (date) {
    const d = new Date(); d.setDate(d.getDate() + 1);
    date.min = d.toISOString().slice(0, 10);
  }

  // Character counter
  const msg = form.elements.message, count = document.getElementById("count");
  if (msg && count) msg.addEventListener("input", () => count.textContent = msg.value.length);

  // Demo: show the "sent" message
  window.App.demoHandlers.contact = () => {
    document.getElementById("contactCard").classList.add("sent");
  };
  const again = document.getElementById("again");
  if (again) again.addEventListener("click", () => {
    form.reset(); syncTopic(); if (count) count.textContent = "0";
    document.getElementById("contactCard").classList.remove("sent");
    form.elements.name.focus();
  });

  syncTopic();
})();
