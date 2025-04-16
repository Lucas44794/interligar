document.addEventListener("DOMContentLoaded", function () {
    const body = document.body;
    const themeToggleBtn = document.getElementById("toggleThemeBtn");

    // Carregar tema salvo no localStorage
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
        body.classList.add(savedTheme);
        themeToggleBtn.textContent = savedTheme === "dark-theme" ? "☀️ Modo Claro" : "🌙 Modo Escuro";
    }

    themeToggleBtn.addEventListener("click", function () {
        if (body.classList.contains("light-theme")) {
            body.classList.remove("light-theme");
            body.classList.add("dark-theme");
            localStorage.setItem("theme", "dark-theme");
            themeToggleBtn.textContent = "☀️ Modo Claro";
        } else {
            body.classList.remove("dark-theme");
            body.classList.add("light-theme");
            localStorage.setItem("theme", "light-theme");
            themeToggleBtn.textContent = "🌙 Modo Escuro";
        }
    });
});