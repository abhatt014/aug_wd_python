/* =========================================================
   validate.js — checks form fields in the browser before sending.

   Add  data-validate  to a <form> (and  novalidate  to switch off the
   browser's own pop-ups). Each input sits inside a  .field  wrapper
   that also holds a  .err  message. Rules come from normal HTML
   attributes: required, minlength, maxlength, min, max, pattern,
   type="email". Extra rule:  data-match="#otherInputId".

   Always check again in Flask too — browser checks can be skipped.
   Load this file BEFORE app.js.
   ========================================================= */
(function () {
  "use strict";

  function fieldOk(input, form) {
    if (!input.checkValidity()) return false;
    if (input.dataset.match) {
      const other = form.querySelector(input.dataset.match);
      if (other && other.value !== input.value) return false;
    }
    return true;
  }

  function isVisible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }

  // Capture phase, so this runs before any other submit handler.
  document.addEventListener("submit", e => {
    const form = e.target;
    if (!form.matches("form[data-validate]")) return;

    let first = null;
    form.querySelectorAll(".field").forEach(f => {
      const input = f.querySelector("input, select, textarea");
      if (!input || input.disabled || !isVisible(f)) { f.classList.remove("invalid"); return; }
      const ok = fieldOk(input, form);
      f.classList.toggle("invalid", !ok);
      if (!ok && !first) first = input;
    });

    if (first) {
      e.preventDefault();
      e.stopImmediatePropagation();
      first.focus();
    }
  }, true);

  // Remove the error as soon as the field is fixed.
  document.addEventListener("input", e => {
    const f = e.target.closest(".field.invalid");
    if (!f) return;
    const form = e.target.form;
    if (form && fieldOk(e.target, form)) f.classList.remove("invalid");
  });
})();
