// File: static/js/generator.js
console.log("generator.js loaded - AJAX submission enabled");

document.addEventListener("DOMContentLoaded", () => {
    // 1. Get the elements
    const generatorForm = document.getElementById("generatorForm");
    const topicInput = document.querySelector("textarea[name='topic']");
    const loader = document.getElementById("fullScreenLoader");

    if (generatorForm) {
        // 2. Attach the submit event listener
        generatorForm.addEventListener("submit", async (e) => {
            // STOP the default form submission (which would cause a page reload)
            e.preventDefault(); 

            // Basic client-side validation
            if (!topicInput.value.trim()) {
                alert("Please enter a topic name.");
                return;
            }

            // --- Show Loader during long-running operation ---
            if (loader) {
                // Assuming CSS is set up to display the loader over the entire screen
                loader.style.display = "flex"; 
            }

            // 3. Prepare form data and submit via AJAX
            const formData = new FormData(generatorForm);

            try {
                // Send data to the Flask endpoint (routes.topic)
                const response = await fetch(generatorForm.action, {
                    method: 'POST',
                    body: formData
                });

                // The server should respond with JSON containing a success status or redirect URL
                const result = await response.json();

                if (result.success && result.redirect) {
                    // 4. On success, redirect to the quiz page
                    window.location.href = result.redirect;
                } else if (result.error) {
                    // Handle server-side errors (e.g., failed scrape, AI error)
                    alert("Error during quiz generation: " + result.error);
                } else {
                    alert("An unknown error occurred on the server.");
                }

            } catch (error) {
                console.error("AJAX Topic Submission Error:", error);
                alert("A network error occurred. Check your connection.");
            } finally {
                // 5. Hide the loader if an error occurred before redirect
                if (loader) {
                    loader.style.display = "none";
                }
            }
        });
    }
});