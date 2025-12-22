# SmartQuizzer 🚀 
### An AI-Powered Adaptive Quiz Generation Platform

SmartQuizzer is a full-stack web application that transforms study notes, PDFs, or general topics into interactive, high-quality quizzes using Generative AI (Llama-3 via Groq). It features an **Adaptive Learning Engine** that adjusts question difficulty based on student performance.

## ✨ Key Features
* **AI Question Generation:** Instantly creates MCQs and Short Answer questions from PDFs, raw text, or topics.
* **Adaptive Learning Core:** Uses a proficiency-tracking algorithm to serve Easy, Medium, or Hard questions based on user accuracy.
* **PDF Intelligence:** Integrated PDF parser to extract and clean text from academic documents.
* **Secure Architecture:** Implements environment variable management for API keys and hashed password security.
* **Study Library:** Users can save generated questions to a personal library for future revision.

## 🛠️ Tech Stack
* **Frontend:** Flask (Jinja2), Bootstrap 5, CSS3 (Custom Glassmorphism/Neumorphic UI)
* **Backend:** Python, Flask
* **Database:** SQLAlchemy (SQLite)
* **AI Model:** Llama-3-70b (via Groq API)
* **Authentication:** Flask-Login

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Simrannnnnnnnnnnn/SmartQuizzer
   cd SmartQuizzer