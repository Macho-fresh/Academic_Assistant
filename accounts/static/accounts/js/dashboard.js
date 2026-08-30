/**
 * dashboard.js — frontend-only interactions for dashboard.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 *
 * "Start Recording" and "Upload Lecture" have no backend endpoint yet
 * (see data-action-placeholder). Once the recording system exists, wire
 * these to their real URLs instead of intercepting the click here.
 */
(function () {
  "use strict";

  document.querySelectorAll("[data-action-placeholder]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      console.info(
        "Academic Assistant: '" + el.dataset.actionPlaceholder + "' has no backend endpoint yet."
      );
    });
  });
})();
