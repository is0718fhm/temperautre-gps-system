document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector(".menu-toggle");
    const links = document.querySelector(".nav-links");

    button.addEventListener("click", () => {
        links.classList.toggle("show");
    });
});
