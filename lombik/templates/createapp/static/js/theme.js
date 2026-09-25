function applyThemeUI(isDark) {
    var themeIcon = document.getElementById("themeIcon");
    var themeText = document.getElementById("themeText");

    if (!themeIcon || !themeText) return;

    if (isDark) {
        themeIcon.setAttribute("name", "sunny-outline");
        themeText.textContent = "Light mode";
    } else {
        themeIcon.setAttribute("name", "moon-outline");
        themeText.textContent = "Dark mode";
    }
}

function toggleDarkMode() {
    var root = document.documentElement;
    var isDark = root.classList.contains("dark");
    var newState = !isDark;

    root.classList.toggle("dark", newState);
    localStorage.setItem("theme", newState ? "dark" : "light");
    applyThemeUI(newState);
}

document.addEventListener("DOMContentLoaded", function () {
    applyThemeUI(document.documentElement.classList.contains("dark"));
});
