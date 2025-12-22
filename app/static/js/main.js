// main.js
console.log("main.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach(link => {
        link.addEventListener("mouseenter", () => {
            link.classList.add("nav-hover");
        });
        link.addEventListener("mouseleave", () => {
            link.classList.remove("nav-hover");
        });
    });

    // Button hover glow
    const primaryButtons = document.querySelectorAll(".btn-primary");

    primaryButtons.forEach(btn => {
        btn.addEventListener("mouseenter", () => {
            btn.classList.add("btn-glow");
        });
        btn.addEventListener("mouseleave", () => {
            btn.classList.remove("btn-glow");
        });
    });

});
