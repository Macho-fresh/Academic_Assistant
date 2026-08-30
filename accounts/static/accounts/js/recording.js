/**
 * recording.js — frontend-only interactions for record.html.
 * Mobile sidebar toggling is handled globally by app-shell.js.
 *
 * This file only captures audio in the browser and submits it to Django.
 * Speech-to-text, topic segmentation, and summary generation all happen
 * server-side — nothing here simulates those results.
 */
(function () {
  "use strict";

  var recorder = document.getElementById("recorder");
  if (!recorder) return;

  var form = document.getElementById("recordingForm");
  var titleInput = document.getElementById("id_lecture_title");
  var courseSelect = document.getElementById("id_lecture_course"); // absent when a course is pre-selected
  var titleError = document.getElementById("titleError");
  var courseError = document.getElementById("courseError");

  var requestMicBtn = document.getElementById("requestMicBtn");
  var micDeniedMessage = document.getElementById("micDeniedMessage");

  var statusText = document.getElementById("recorderStatusText");
  var timerEl = document.getElementById("recorderTimer");
  var canvas = document.getElementById("recorderVisualizer");
  var canvasCtx = canvas ? canvas.getContext("2d") : null;

  var startBtn = document.getElementById("startBtn");
  var pauseBtn = document.getElementById("pauseBtn");
  var resumeBtn = document.getElementById("resumeBtn");
  var stopBtn = document.getElementById("stopBtn");

  var reviewPlayer = document.getElementById("reviewPlayer");
  var reviewDuration = document.getElementById("reviewDuration");
  var reviewTitle = document.getElementById("reviewTitle");
  var reviewCourse = document.getElementById("reviewCourse");
  var discardBtn = document.getElementById("discardBtn");

  var uploadStatusText = document.getElementById("uploadStatusText");
  var errorMessage = document.getElementById("recorderErrorMessage");
  var errorRetryBtn = document.getElementById("errorRetryBtn");

  var mediaStream = null;
  var mediaRecorder = null;
  var recordedChunks = [];
  var recordedBlob = null;
  var audioObjectUrl = null;

  var audioContext = null;
  var analyser = null;
  var visualizerFrame = null;

  var elapsedSeconds = 0;
  var timerInterval = null;

  function setState(state) {
    recorder.dataset.state = state;
  }

  function formatTime(totalSeconds) {
    var h = Math.floor(totalSeconds / 3600);
    var m = Math.floor((totalSeconds % 3600) / 60);
    var s = Math.floor(totalSeconds % 60);
    function pad(n) { return String(n).padStart(2, "0"); }
    return pad(h) + ":" + pad(m) + ":" + pad(s);
  }

  /* ---- Timer -------------------------------------------------------------------- */

  function startTimer() {
    timerInterval = window.setInterval(function () {
      elapsedSeconds += 1;
      if (timerEl) timerEl.textContent = formatTime(elapsedSeconds);
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) window.clearInterval(timerInterval);
    timerInterval = null;
  }

  /* ---- Waveform visualizer (Web Audio API, no third-party library) --------------- */

  function startVisualizer(stream) {
    if (!canvasCtx || !window.AudioContext) return;
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    var source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);

    var data = new Uint8Array(analyser.fftSize);
    var lineColor = getComputedStyle(document.documentElement).getPropertyValue("--navy-800").trim() || "#0B2340";

    function draw() {
      visualizerFrame = window.requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(data);

      canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
      canvasCtx.lineWidth = 2;
      canvasCtx.strokeStyle = lineColor;
      canvasCtx.beginPath();

      var sliceWidth = canvas.width / data.length;
      var x = 0;
      for (var i = 0; i < data.length; i++) {
        var v = data[i] / 128.0;
        var y = (v * canvas.height) / 2;
        if (i === 0) canvasCtx.moveTo(x, y);
        else canvasCtx.lineTo(x, y);
        x += sliceWidth;
      }
      canvasCtx.lineTo(canvas.width, canvas.height / 2);
      canvasCtx.stroke();
    }
    draw();
  }

  function stopVisualizer() {
    if (visualizerFrame) window.cancelAnimationFrame(visualizerFrame);
    visualizerFrame = null;
    if (audioContext) {
      audioContext.close();
      audioContext = null;
    }
    if (canvasCtx) canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
  }

  /* ---- Microphone permission ------------------------------------------------------ */

  function goToIdle() {
    elapsedSeconds = 0;
    if (timerEl) timerEl.textContent = "00:00:00";
    if (statusText) statusText.textContent = "Ready to record";
    startBtn.hidden = false;
    pauseBtn.hidden = true;
    resumeBtn.hidden = true;
    stopBtn.hidden = true;
    setState("idle");
  }

  function requestMicrophone() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError("This browser doesn't support in-browser recording. Try a recent version of Chrome, Edge, or Firefox.");
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function (stream) {
        mediaStream = stream;
        if (micDeniedMessage) micDeniedMessage.hidden = true;
        startVisualizer(stream);
        goToIdle();
      })
      .catch(function (err) {
        if (micDeniedMessage) micDeniedMessage.hidden = false;
        console.warn("Academic Assistant: microphone permission error:", err.name);
      });
  }

  if (requestMicBtn) requestMicBtn.addEventListener("click", requestMicrophone);

  // If the browser already knows the mic permission was granted in a past
  // visit, skip straight past the "Allow Microphone" screen.
  if (navigator.permissions && navigator.permissions.query) {
    navigator.permissions.query({ name: "microphone" })
      .then(function (status) {
        if (status.state === "granted") requestMicrophone();
      })
      .catch(function () { /* Permissions API not supported for "microphone" — leave the prompt visible */ });
  }

  /* ---- Recording controls ---------------------------------------------------------- */

  function pickMimeType() {
    var candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
    for (var i = 0; i < candidates.length; i++) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(candidates[i])) {
        return candidates[i];
      }
    }
    return "";
  }

  function startRecording() {
    if (!mediaStream) { requestMicrophone(); return; }
    if (!window.MediaRecorder) {
      showError("This browser doesn't support in-browser recording. Try a recent version of Chrome, Edge, or Firefox.");
      return;
    }

    recordedChunks = [];
    var mimeType = pickMimeType();

    try {
      mediaRecorder = mimeType ? new MediaRecorder(mediaStream, { mimeType: mimeType }) : new MediaRecorder(mediaStream);
    } catch (err) {
      showError("Recording failed to start. Please try again.");
      return;
    }

    mediaRecorder.ondataavailable = function (event) {
      if (event.data && event.data.size > 0) recordedChunks.push(event.data);
    };

    mediaRecorder.onerror = function () {
      showError("Recording failed unexpectedly. Please try again.");
    };

    mediaRecorder.onstop = function () {
      recordedBlob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || "audio/webm" });
      audioObjectUrl = URL.createObjectURL(recordedBlob);
      showReview();
    };

    mediaRecorder.start();
    elapsedSeconds = 0;
    startTimer();

    if (statusText) statusText.textContent = "Recording";
    startBtn.hidden = true;
    pauseBtn.hidden = false;
    resumeBtn.hidden = true;
    stopBtn.hidden = false;
    setState("recording");
  }

  function pauseRecording() {
    if (!mediaRecorder || mediaRecorder.state !== "recording") return;
    mediaRecorder.pause();
    stopTimer();
    if (statusText) statusText.textContent = "Paused";
    pauseBtn.hidden = true;
    resumeBtn.hidden = false;
    setState("paused");
  }

  function resumeRecording() {
    if (!mediaRecorder || mediaRecorder.state !== "paused") return;
    mediaRecorder.resume();
    startTimer();
    if (statusText) statusText.textContent = "Recording";
    pauseBtn.hidden = false;
    resumeBtn.hidden = true;
    setState("recording");
  }

  function stopRecording() {
    if (!mediaRecorder || mediaRecorder.state === "inactive") return;
    stopTimer();
    stopVisualizer();
    mediaRecorder.stop();
  }

  if (startBtn) startBtn.addEventListener("click", startRecording);
  if (pauseBtn) pauseBtn.addEventListener("click", pauseRecording);
  if (resumeBtn) resumeBtn.addEventListener("click", resumeRecording);
  if (stopBtn) stopBtn.addEventListener("click", stopRecording);

  /* ---- Review -------------------------------------------------------------------- */

  function showReview() {
    if (reviewPlayer) reviewPlayer.src = audioObjectUrl;
    if (reviewDuration) reviewDuration.textContent = formatTime(elapsedSeconds);
    if (reviewTitle) reviewTitle.textContent = (titleInput && titleInput.value.trim()) || "Untitled lecture";
    if (reviewCourse) {
      if (courseSelect) {
        var selectedOption = courseSelect.options[courseSelect.selectedIndex];
        reviewCourse.textContent = selectedOption && selectedOption.value ? selectedOption.textContent : "No course selected";
      } else {
        var lockedCourseField = document.querySelector('input[readonly][type="text"]');
        reviewCourse.textContent = lockedCourseField ? lockedCourseField.value : "—";
      }
    }
    setState("review");
  }

  function discardRecording() {
    if (audioObjectUrl) URL.revokeObjectURL(audioObjectUrl);
    audioObjectUrl = null;
    recordedBlob = null;
    recordedChunks = [];
    if (reviewPlayer) reviewPlayer.removeAttribute("src");

    // Mic permission is already granted at this point, so re-acquiring the
    // stream happens silently (no new browser prompt).
    if (mediaStream) {
      requestMicrophone();
    } else {
      goToIdle();
    }
  }

  if (discardBtn) discardBtn.addEventListener("click", discardRecording);

  /* ---- Errors ---------------------------------------------------------------------- */

  function showError(message) {
    stopTimer();
    stopVisualizer();
    if (errorMessage) errorMessage.textContent = message;
    setState("error");
  }

  if (errorRetryBtn) {
    errorRetryBtn.addEventListener("click", function () {
      if (mediaStream) goToIdle();
      else setState("permission");
    });
  }

  function clearFieldErrors() {
    if (titleError) titleError.classList.remove("is-visible");
    if (titleInput) titleInput.classList.remove("has-error");
    if (courseError) courseError.classList.remove("is-visible");
    if (courseSelect) courseSelect.classList.remove("has-error");
  }

  function validateBeforeSubmit() {
    clearFieldErrors();
    var valid = true;

    if (!titleInput || !titleInput.value.trim()) {
      if (titleError) titleError.classList.add("is-visible");
      if (titleInput) titleInput.classList.add("has-error");
      valid = false;
    }
    if (courseSelect && !courseSelect.value) {
      if (courseError) courseError.classList.add("is-visible");
      courseSelect.classList.add("has-error");
      valid = false;
    }
    return valid;
  }

  /* ---- Submission: build FormData and POST to Django ------------------------------- */

  function submitRecording() {
  if (!validateBeforeSubmit()) return;

  if (!recordedBlob) {
    showError("No recording found. Please record a lecture before saving.");
    return;
  }

  setState("uploading");

  if (uploadStatusText) {
    uploadStatusText.textContent = "Saving recording…";
  }

  var formData = new FormData(form);

  var extension = (
    recordedBlob.type.split("/")[1] || "webm"
  ).split(";")[0];

  formData.append(
    "audio_file",
    recordedBlob,
    "recording." + extension
  );

  fetch(form.action, {
    method: "POST",
    body: formData
  })
    .then(function (response) {
      if (!response.ok) {
        throw new Error(
          "Upload failed with status " + response.status
        );
      }

      // Django redirect() is automatically followed by fetch.
      if (response.redirected) {
        if (uploadStatusText) {
          uploadStatusText.textContent = "Lecture saved. Redirecting…";
        }

        window.location.href = response.url;
        return;
      }

      throw new Error(
        "Lecture saved, but Django did not redirect."
      );
    })
    .catch(function (error) {
      console.error("Recording upload error:", error);
      showError(error.message);
    });
}

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      submitRecording();
    });
  }
})();
