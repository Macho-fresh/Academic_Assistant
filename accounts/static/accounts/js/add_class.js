/**
 * add_class.js — frontend-only interactions for add_class.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 *
 * Django owns validation, conflict checking, and saving. This only reflects
 * the `data-lecturer` attribute Django already rendered onto the selected
 * course's <option> — it doesn't invent any course/lecturer relationship.
 */
(function () {
  "use strict";

  var courseSelect = document.getElementById("id_class_course");
  var lecturerHint = document.getElementById("classLecturerHint");

  function updateLecturerHint() {
    if (!courseSelect || !lecturerHint) return;
    var selected = courseSelect.options[courseSelect.selectedIndex];
    var lecturer = selected ? selected.dataset.lecturer : "";
    if (lecturer) {
      lecturerHint.textContent = "Lecturer: " + lecturer;
      lecturerHint.hidden = false;
    } else {
      lecturerHint.hidden = true;
    }
  }

  if (courseSelect) {
    courseSelect.addEventListener("change", updateLecturerHint);
    updateLecturerHint();
  }

  document.querySelectorAll(".field__input.has-error").forEach(function (input) {
    input.addEventListener("input", function () {
      input.classList.remove("has-error");
      var error = input.closest(".field").querySelector(".field__error");
      if (error) error.classList.remove("is-visible");
    }, { once: true });
  });
})();
