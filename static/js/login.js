/*
  login.js
  ---------
  The login page posts directly via a normal HTML <form> to Flask
  (see templates/login.html), so no JS is strictly required for
  submission. This file just adds a small UX touch: clearing the
  error message once the user starts typing again.
*/

document.addEventListener("DOMContentLoaded", () => {
    const errorMsg = document.querySelector(".error-msg");
    const inputs = document.querySelectorAll(".form-group input");

    if (errorMsg) {
        inputs.forEach((input) => {
            input.addEventListener("input", () => {
                errorMsg.style.display = "none";
            });
        });
    }
});