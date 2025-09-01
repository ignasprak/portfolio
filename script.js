document.addEventListener("DOMContentLoaded", () => {
    const hamburger = document.getElementById("hamburger");
    const navLinks = document.getElementById("nav-links");
    const toggleButton = document.getElementById("darkModeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const body = document.body;

    // detect best event for device
    const tapEvent = "ontouchend" in window ? "touchend" : "click";

    // remember dark mode
    if (localStorage.getItem("theme") === "dark") {
        body.classList.add("dark-mode");
        if (themeIcon) themeIcon.src = "media/yellow-moon.png";
    }

    // hamburger
    const toggleNav = (e) => {
        e.preventDefault();
        e.stopPropagation();
        navLinks.classList.toggle("show");
    };

    hamburger.addEventListener("click", toggleNav, false);
    hamburger.addEventListener("touchend", toggleNav, false);

    // close nav when tapping outside
    document.body.addEventListener("click", (e) => {
        if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
            navLinks.classList.remove("show");
        }
    });

    // dark mode toggle
    toggleButton.addEventListener("click", () => {
        const isDark = body.classList.toggle("dark-mode");

        // icon update
        themeIcon.src = isDark ? "media/yellow-moon.png" : "media/dark-moon.png";

        // preference purposes
        localStorage.setItem("theme", isDark ? "dark" : "light");
    });

    const username = "ignasprak";
    const reposContainer = document.getElementById("repos");

    // language colour matching
    const languageColors = {
        JavaScript: "#f1e05a",
        HTML: "#e34c26",
        CSS: "#563d7c",
        Python: "#3572A5",
        "Jupyter Notebook": "#DA5B0B",
        TypeScript: "#2b7489"
    };

    fetch(`https://api.github.com/users/${username}/repos?per_page=100&sort=updated`)
        .then(response => response.json())
        .then(repos => {
            reposContainer.innerHTML = "";

            repos.forEach(repo => {
                if (repo.fork) return; // skip forks

                const langColor = languageColors[repo.language] || "#ccc";

                const repoEl = document.createElement("div");
                repoEl.classList.add("repo");
                repoEl.innerHTML = `
        <h3><a href="${repo.html_url}" target="_blank">${repo.name}</a></h3>
        <p>${repo.description || "No description available"}</p>
        <small>
          <span class="lang-dot" style="background:${langColor}"></span>
          ${repo.language || "Unknown"}
        </small>
      `;
                reposContainer.appendChild(repoEl);
            });
        })
        .catch(err => {
            reposContainer.innerHTML = "Error loading repositories.";
            console.error(err);
        });
});
