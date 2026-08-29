/**
 * auth.js — frontend-only interactions for login.html and register.html.
 * No authentication logic lives here: Django handles submission and validation.
 */
(function () {
  "use strict";

  /* ---- Password show/hide toggle ------------------------------------ */

  document.querySelectorAll("[data-password-toggle]").forEach(function (btn) {
    var fieldId = btn.getAttribute("data-password-toggle");
    var input = document.getElementById(fieldId);
    if (!input) return;

    var eyeIcon = btn.querySelector(".icon-eye");
    var eyeOffIcon = btn.querySelector(".icon-eye-off");

    btn.addEventListener("click", function () {
      var isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      btn.setAttribute("aria-pressed", String(isHidden));
      btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
      if (eyeIcon && eyeOffIcon) {
        eyeIcon.style.display = isHidden ? "none" : "block";
        eyeOffIcon.style.display = isHidden ? "block" : "none";
      }
    });
  });

  /* ---- Password strength indicator (registration only) --------------- */

  var passwordInput = document.getElementById("id_password");
  var strengthFill = document.getElementById("pwStrengthFill");
  var strengthLabel = document.getElementById("pwStrengthLabel");

  function scorePassword(value) {
    var score = 0;
    if (!value) return 0;
    if (value.length >= 8) score++;
    if (value.length >= 12) score++;
    if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
    if (/\d/.test(value)) score++;
    if (/[^A-Za-z0-9]/.test(value)) score++;
    return Math.min(score, 4);
  }

  var strengthMeta = [
    { width: "0%",   color: "var(--border)",  label: "Use 8+ characters" },
    { width: "25%",  color: "var(--danger)",  label: "Weak" },
    { width: "50%",  color: "var(--warning)", label: "Fair" },
    { width: "75%",  color: "var(--gold-500)",label: "Good" },
    { width: "100%", color: "var(--success)", label: "Strong" }
  ];

  if (passwordInput && strengthFill && strengthLabel) {
    passwordInput.addEventListener("input", function () {
      var score = scorePassword(passwordInput.value);
      var meta = strengthMeta[score];
      strengthFill.style.width = meta.width;
      strengthFill.style.background = meta.color;
      strengthLabel.textContent = meta.label;
      validateConfirmPassword();
    });
  }

  /* ---- Confirm password validation ------------------------------------ */

  var confirmInput = document.getElementById("id_confirm_password");
  var confirmError = document.getElementById("confirmPasswordError");

  function validateConfirmPassword() {
    if (!passwordInput || !confirmInput || !confirmError) return true;
    if (!confirmInput.value) {
      confirmError.classList.remove("is-visible");
      confirmInput.classList.remove("has-error");
      return true;
    }
    var matches = confirmInput.value === passwordInput.value;
    confirmError.classList.toggle("is-visible", !matches);
    confirmInput.classList.toggle("has-error", !matches);
    return matches;
  }

  if (confirmInput) {
    confirmInput.addEventListener("input", validateConfirmPassword);
  }

  var registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", function (event) {
      if (!validateConfirmPassword()) {
        event.preventDefault();
        confirmInput.focus();
      }
    });
  }

  /* ---- Account type (role) selection UI -------------------------------- */

  document.querySelectorAll(".role-option input[type=radio]").forEach(function (radio) {
    radio.addEventListener("change", function () {
      document.querySelectorAll(".role-option__card").forEach(function (card) {
        card.setAttribute("aria-checked", "false");
      });
      if (radio.checked) {
        radio.closest(".role-option").querySelector(".role-option__card").setAttribute("aria-checked", "true");
      }
    });
  });
})();
