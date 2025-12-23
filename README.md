# 🧠 SmartQuizzer: AI-Powered Quiz Generator
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Render](https://img.shields.io/badge/Render-%23430098.svg?style=for-the-badge&logo=render&logoColor=white)

SmartQuizzer is a full-stack web application designed to help students and educators generate high-quality quizzes instantly using Artificial Intelligence. Users can input topics, raw text, or even upload PDF documents to create customized multiple-choice questions.

**Live Demo:** [https://smartquizzer.onrender.com](https://smartquizzer.onrender.com)

---

## 🚀 Features

- **AI Generation:** Leverages the Groq API (LLM) to generate accurate MCQs with explanations.
- **Multiple Inputs:** Generate quizzes from text, specific topics, or uploaded PDF files.
- **User Authentication:** Secure Signup/Login system using Flask-Login.
- **Personal Library:** Save generated quizzes to a personal dashboard to review or retake later.
- **Progress Tracking:** Interactive quiz interface with real-time scoring and streak tracking.
- **Responsive Design:** Mobile-friendly interface built with modern CSS.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML5, CSS3, JavaScript
- **Database:** SQLAlchemy (SQLite)
- **AI Integration:** Groq API / LLM Client
- **File Processing:** PyPDF
- **Deployment:** Render

---

## 📂 Project Structure

```text
SmartQuizzer/
├── app/                # Backend logic
│   ├── routes.py       # Flask Blueprints & routing
│   ├── models.py       # Database schemas (User, Question)
│   └── llm_client.py   # AI integration logic
├── templates/          # HTML files (Root level)
├── static/             # CSS, JS, and Images
├── main.py             # App entry point
├── requirements.txt    # Python dependencies
└── .env                #Environment variables (Hidden)


---

## ⚙️ **Installation & Setup** Follow these steps to get the project running on your local machine.

# 1. Clone the repository
git clone https://github.com/Simrannnnnnnnnnnn/SmartQuizzer.git
cd ai-quiz-generator

# 2. Create and activate a Virtual Environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up Environment variables
# Create a .env file and add:
# GROQ_API_KEY=your_api_key_here
# SECRET_KEY=your_secret_key

# 5. Run the application
python main.py

---
# Contact 
### Simran Kaur 
### kaur.simran1542@gmail.com
### https://github.com/Simrannnnnnnnnnnn/SmartQuizzer