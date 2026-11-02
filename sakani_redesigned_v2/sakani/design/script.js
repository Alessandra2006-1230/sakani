// Sakani design mockup helpers. Visual reference only; the app is Tkinter.

document.querySelectorAll(".sidebar nav a").forEach(function (link) {
  link.addEventListener("click", function (event) {
    event.preventDefault();
    document.querySelectorAll(".sidebar nav a").forEach(function (item) {
      item.classList.remove("active");
    });
    link.classList.add("active");
  });
});

// Simple password reveal for the mockup login form.
var loginPassword = document.querySelector('.auth-card input[type="password"]');
if (loginPassword) {
  loginPassword.addEventListener("dblclick", function () {
    var isPassword = loginPassword.type === "password";
    loginPassword.type = isPassword ? "text" : "password";
  });
}
