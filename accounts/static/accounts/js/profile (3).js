/**
 * profile.js — frontend-only interactions for profile.html.
 * No backend update logic lives here: Django handles the actual save.
 */
(function () {
  "use strict";

  /* ---- Mobile sidebar toggle ------------------------------------------ */

  var sidebar = document.getElementById("sidebar");
  var openBtn = document.getElementById("sidebarOpen");
  var closeBtn = document.getElementById("sidebarClose");
  var backdrop = document.getElementById("sidebarBackdrop");

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("is-open");
    if (backdrop) backdrop.classList.add("is-visible");
    if (openBtn) openBtn.setAttribute("aria-expanded", "true");
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("is-open");
    if (backdrop) backdrop.classList.remove("is-visible");
    if (openBtn) openBtn.setAttribute("aria-expanded", "false");
  }

  if (openBtn) openBtn.addEventListener("click", openSidebar);
  if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeSidebar();
  });

  /* ---- Edit profile: toggle view / edit mode ---------------------------- */

  var editBtn = document.getElementById("editProfileBtn");
  var cancelBtn = document.getElementById("cancelEditBtn");
  var actions = document.getElementById("profileFormActions");
  var personalInfoCard = document.getElementById("personalInfoCard");
  var editableFields = ["id_full_name"]; // email and role stay read-only
  var originalValues = {};

  function setEditMode(isEditing) {
    editableFields.forEach(function (id) {
      var input = document.getElementById(id);
      if (!input) return;
      if (isEditing) {
        originalValues[id] = input.value;
        input.removeAttribute("readonly");
      } else {
        input.setAttribute("readonly", "readonly");
      }
    });

    if (actions) actions.hidden = !isEditing;
    if (editBtn) {
      editBtn.setAttribute("aria-pressed", String(isEditing));
      editBtn.hidden = isEditing;
    }
    if (personalInfoCard) personalInfoCard.classList.toggle("is-editing", isEditing);

    if (isEditing) {
      var firstField = document.getElementById(editableFields[0]);
      if (firstField) firstField.focus();
    }
  }

  if (editBtn) {
    editBtn.addEventListener("click", function () {
      setEditMode(true);
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      editableFields.forEach(function (id) {
        var input = document.getElementById(id);
        if (input && originalValues[id] !== undefined) {
          input.value = originalValues[id];
        }
      });
      setEditMode(false);
    });
  }
})();
