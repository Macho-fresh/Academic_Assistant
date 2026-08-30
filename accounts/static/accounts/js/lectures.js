/**
 * lectures.js — frontend-only interactions for lecture_list.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 *
 * Filters submit the real toolbar form as a GET request so Django can read
 * request.GET once a view implements filtering — no fake search happens here.
 */
(function () {
  "use strict";

  var toolbar = document.querySelector(".lecture-toolbar");
  if (toolbar) {
    toolbar.querySelectorAll(".filter-select").forEach(function (select) {
      select.addEventListener("change", function () {
        toolbar.submit();
      });
    });
  }

  document.querySelectorAll("[data-action-placeholder]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      console.info(
        "Academic Assistant: '" + el.dataset.actionPlaceholder + "' has no backend endpoint yet."
      );
    });
  });
})();

const file = new File(
    [recordedBlob],
    "lecture.webm",
    {
        type: recordedBlob.type
    }
);

const formData = new FormData(recordingForm);

formData.append(
    "audio_file",
    file
);