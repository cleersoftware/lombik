function applyThemeUI(isDark) {
    const themeIcon = document.getElementById("themeIcon");
    const themeText = document.getElementById("themeText");

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
    const root = document.documentElement;

    const isDark = root.classList.contains("dark");
    const newState = !isDark;

    root.classList.toggle("dark", newState);

    localStorage.setItem("theme", newState ? "dark" : "light");

    applyThemeUI(newState);
}

document.addEventListener("DOMContentLoaded", () => {
    const isDark = document.documentElement.classList.contains("dark");
    applyThemeUI(isDark);
});