// static/js/quiz.js
document.addEventListener("DOMContentLoaded", () => {
    const quizForm = document.getElementById("quizForm");
    const explanationPopup = document.getElementById("explanationPopup");

    // We store the next question data globally so we can 
    // update the UI ONLY after the user closes the popup.
    let pendingNextQuestionHTML = null;

    window.closeExplanationPopup = function() {
        explanationPopup.classList.remove("show");
        
        // If we have a new question waiting, swap it in now
        if (pendingNextQuestionHTML) {
            document.getElementById("questionArea").innerHTML = pendingNextQuestionHTML;
            pendingNextQuestionHTML = null;
            // Reset the form scroll or focus if needed
            window.scrollTo(0, 0);
        }
    };

    if (quizForm) {
        quizForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const formData = new FormData(quizForm);
            try {
                const response = await fetch(quizForm.action, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (data.quiz_finished) {
                    window.location.href = data.redirect_url;
                } else {
                    // 1. Fill the popup
                    document.getElementById("explanationText").innerHTML = data.feedback_html;
                    // 2. Show the popup
                    explanationPopup.classList.add("show");
                    // 3. Queue the next question
                    pendingNextQuestionHTML = data.next_question_html;
                }
            } catch (err) {
                alert("Connection lost. Please try again.");
            }
        });
    }
});