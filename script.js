document.addEventListener("DOMContentLoaded", () => {
    const hamburger = document.getElementById("hamburger");
    const navLinks = document.getElementById("nav-links");
    const toggleButton = document.getElementById("darkModeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const body = document.body;

    // rememeber dark mode
    if (localStorage.getItem("theme") === "dark") {
        body.classList.add("dark-mode");
        if (themeIcon) themeIcon.src = "media/yellow-moon.png";
    }

    // hamburgah
    hamburger.addEventListener("click", () => {
        navLinks.classList.toggle("show");
    });

    // dark mode toggle
    toggleButton.addEventListener("click", () => {
        const isDark = body.classList.toggle("dark-mode");

        // icon update
        themeIcon.src = isDark ? "media/yellow-moon.png" : "media/dark-moon.png";

        // preference purposes
        localStorage.setItem("theme", isDark ? "dark" : "light");
    });
});
