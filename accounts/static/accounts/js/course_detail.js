/**
 * course_detail.js — frontend-only interactions for course_detail.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 *
 * "Start Recording" is a real link to record_lecture. "Upload Lecture" has
 * no backend endpoint/URL yet (see data-action-placeholder).
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
