/**
 * app-shell.js — shared chrome interactions for every authenticated page
 * (Dashboard, My Lectures, Courses, Timetable, Profile).
 * Only handles the mobile sidebar; page-specific JS lives in its own file.
 */
(function () {
  "use strict";

  var sidebar = document.getElementById("sidebar");
  var openBtn = document.getElementById("sidebarOpen");
  var closeBtn = document.getElementById("sidebarClose");
  var backdrop = document.getElementById("sidebarBackdrop");

  if (!sidebar) return;

  function openSidebar() {
    sidebar.classList.add("is-open");
    if (backdrop) backdrop.classList.add("is-visible");
    if (openBtn) openBtn.setAttribute("aria-expanded", "true");
  }

  function closeSidebar() {
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
})();
