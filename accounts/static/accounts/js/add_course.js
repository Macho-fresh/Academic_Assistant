/**
 * add_course.js — frontend-only interactions for add_course.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 *
 * Django owns validation and saving; this only clears a field's error
 * styling once the user starts correcting it, so stale red borders don't
 * linger after a resubmission attempt.
 */
(function () {
  "use strict";

  document.querySelectorAll(".field__input.has-error").forEach(function (input) {
    input.addEventListener("input", function () {
      input.classList.remove("has-error");
      var error = input.closest(".field").querySelector(".field__error");
      if (error) error.classList.remove("is-visible");
    }, { once: true });
  });
})();
