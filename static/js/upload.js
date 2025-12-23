// File: static/js/upload.js (renamed from generator.js)
console.log("upload.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    // These IDs are assumed to be present in upload.html
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const loader = document.getElementById("fullScreenLoader"); // Assumes you have a loader element

    if (uploadForm) {
        uploadForm.addEventListener("submit", (e) => {
            // Basic client-side validation for file selection
            if (!fileInput || !fileInput.value) {
                alert("Please upload a document first.");
                e.preventDefault();
                return;
            }

            // --- Show Loader during Upload ---
            if (loader) {
                loader.style.display = "flex"; // Show loader (assumes CSS sets display: none initially)
            }
        });
    }
});