/**
 * timetable.js — frontend-only interactions for timetable.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 */
(function () {
  "use strict";

  var GRID_START_MINUTES = 8 * 60; // grid begins at 8:00 AM

  function toMinutes(hhmm) {
    var parts = (hhmm || "").split(":");
    if (parts.length !== 2) return null;
    return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
  }

  /* ---- Position desktop grid events from data-start / data-end ------------ */

  function layoutEvents() {
    var grid = document.querySelector(".timetable-grid");
    if (!grid) return;

    var hourHeight = parseFloat(getComputedStyle(grid).getPropertyValue("--hour-height")) || 64;

    document.querySelectorAll(".timetable-event").forEach(function (el) {
      var start = toMinutes(el.dataset.start);
      var end = toMinutes(el.dataset.end);
      if (start === null || end === null) return;

      var top = ((start - GRID_START_MINUTES) / 60) * hourHeight;
      var height = ((end - start) / 60) * hourHeight;

      el.style.top = top + "px";
      el.style.height = Math.max(height, 28) + "px";
    });
  }

  layoutEvents();
  window.addEventListener("resize", layoutEvents);

  /* ---- Mobile day switcher --------------------------------------------------- */

  var tabs = document.querySelectorAll(".timetable-tab");
  var dayColumns = document.querySelectorAll(".timetable-day");

  function setActiveDay(dayKey) {
    tabs.forEach(function (tab) {
      tab.classList.toggle("is-active", tab.dataset.dayTab === dayKey);
    });
    dayColumns.forEach(function (day) {
      day.classList.toggle("is-active", day.dataset.day === dayKey);
    });
  }

  if (tabs.length) {
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        setActiveDay(tab.dataset.dayTab);
      });
    });

    var todayColumn = document.querySelector(".timetable-day.is-today");
    setActiveDay(todayColumn ? todayColumn.dataset.day : tabs[0].dataset.dayTab);
  }
})();

document.addEventListener("DOMContentLoaded", () => {
  const timetableEvents = document.querySelectorAll(".timetable-event");

  const gridStartHour = 8;
  const hourHeight = 64;

  timetableEvents.forEach((event) => {
    const start = event.dataset.start;
    const end = event.dataset.end;

    if (!start || !end) {
      return;
    }

    const [startHour, startMinute] = start.split(":").map(Number);
    const [endHour, endMinute] = end.split(":").map(Number);

    const startTotalMinutes =
      startHour * 60 + startMinute;

    const endTotalMinutes =
      endHour * 60 + endMinute;

    const gridStartMinutes =
      gridStartHour * 60;

    const minutesFromGridStart =
      startTotalMinutes - gridStartMinutes;

    const durationMinutes =
      endTotalMinutes - startTotalMinutes;

    const pixelsPerMinute =
      hourHeight / 60;

    const top =
      minutesFromGridStart * pixelsPerMinute;

    const height =
      durationMinutes * pixelsPerMinute;

    event.style.top = `${top}px`;
    event.style.height = `${height}px`;
  });
});