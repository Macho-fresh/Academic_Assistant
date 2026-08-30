/**
 * lecture_detail.js — frontend-only interactions for lecture_detail.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 *
 * All timestamps and text come from Django-rendered data attributes/markup —
 * nothing here invents topic, transcript, or summary content.
 */
(function () {
  "use strict";

  /* ---- Custom audio player --------------------------------------------------- */

  var audio = document.getElementById("lectureAudio");
  var toggleBtn = document.getElementById("audioToggle");
  var seekRange = document.getElementById("audioSeek");
  var currentTimeEl = document.getElementById("audioCurrentTime");
  var durationEl = document.getElementById("audioDuration");
  var speedSelect = document.getElementById("audioSpeed");

  function formatTime(seconds) {
    if (!isFinite(seconds)) return "0:00";
    var m = Math.floor(seconds / 60);
    var s = Math.floor(seconds % 60);
    return m + ":" + String(s).padStart(2, "0");
  }

  function setPlayingIcon(isPlaying) {
    if (!toggleBtn) return;
    var playIcon = toggleBtn.querySelector(".icon-play");
    var pauseIcon = toggleBtn.querySelector(".icon-pause");
    if (playIcon) playIcon.style.display = isPlaying ? "none" : "block";
    if (pauseIcon) pauseIcon.style.display = isPlaying ? "block" : "none";
    toggleBtn.setAttribute("aria-label", isPlaying ? "Pause" : "Play");
  }

  function seekTo(seconds) {
    if (!audio) return;
    audio.currentTime = seconds;
    audio.play();
  }

  if (audio && toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      if (audio.paused) audio.play();
      else audio.pause();
    });

    audio.addEventListener("play", function () { setPlayingIcon(true); });
    audio.addEventListener("pause", function () { setPlayingIcon(false); });

    audio.addEventListener("loadedmetadata", function () {
      if (durationEl) durationEl.textContent = formatTime(audio.duration);
      if (seekRange) seekRange.max = audio.duration || 0;
    });

    audio.addEventListener("timeupdate", function () {
      if (currentTimeEl) currentTimeEl.textContent = formatTime(audio.currentTime);
      if (seekRange && !seekRange.matches(":active")) seekRange.value = audio.currentTime;
    });

    if (seekRange) {
      seekRange.addEventListener("input", function () {
        audio.currentTime = parseFloat(seekRange.value);
      });
    }

    if (speedSelect) {
      speedSelect.addEventListener("change", function () {
        audio.playbackRate = parseFloat(speedSelect.value);
      });
    }
  }

  /* ---- Topic + transcript timestamp seeking ------------------------------------ */

  document.querySelectorAll("[data-start-seconds]").forEach(function (el) {
    el.addEventListener("click", function () {
      var seconds = parseFloat(el.dataset.startSeconds);
      if (!isNaN(seconds)) seekTo(seconds);
    });
  });

  /* ---- Transcript search (client-side text highlighting only) ------------------- */

  var transcriptSearch = document.getElementById("transcriptSearch");
  var transcriptTextEls = document.querySelectorAll(".transcript-segment__text, .transcript-raw");

  // Keep each node's original text so repeated searches don't compound <mark> tags.
  var originalTexts = Array.prototype.map.call(transcriptTextEls, function (el) {
    return el.textContent;
  });

  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function highlight(query) {
    transcriptTextEls.forEach(function (el, i) {
      var original = originalTexts[i];
      if (!query) {
        el.textContent = original;
        return;
      }
      var pattern = new RegExp("(" + escapeRegExp(query) + ")", "gi");
      var escaped = original.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      el.innerHTML = escaped.replace(pattern, "<mark>$1</mark>");
    });
  }

  if (transcriptSearch) {
    transcriptSearch.addEventListener("input", function () {
      highlight(transcriptSearch.value.trim());
    });
  }

  /* ---- Retry processing (placeholder — no backend endpoint yet) ------------------ */

  var retryBtn = document.getElementById("retryProcessingBtn");
  if (retryBtn) {
    retryBtn.addEventListener("click", function () {
      console.info(
        "Academic Assistant: retry-processing endpoint for lecture " +
          retryBtn.dataset.lectureId +
          " is not built yet."
      );
    });
  }
})();
