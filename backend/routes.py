import json, os, io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import request, render_template, redirect, url_for
#import pytesseract # Image se text nikaalne ke liye
from PIL import Image # Image open karne ke liye
import pdfplumber
from dotenv import load_dotenv
from flask import session 
from backend.models import User, Question, QuizResult, TopicMastery, MistakeBank, db
from backend.services import extract_text_from_pdf
from backend.llm_client import LLMClient
from backend.services import extract_text_from_image
def is_allowed():
    return current_user.is_authenticated or session.get('is_guest')
load_dotenv()
routes_bp = Blueprint('routes', __name__)

# Initialize AI Client
llm = LLMClient(api_key=os.getenv("GROQ_API_KEY"))

# Helper: Check if access is allowed (Login OR Guest)
def is_allowed():
    return current_user.is_authenticated or session.get('is_guest')

# ==========================================
# AUTHENTICATION (Login, Signup, Guest)
# ==========================================

@routes_bp.route('/')
def index():
    return render_template('landing.html')

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    if request.method == 'POST':
        login_id = request.form.get('login_id')
        password = request.form.get('password')
        user = User.query.filter(or_(User.email == login_id, User.username == login_id)).first()
        if user and user.check_password(password):
            login_user(user)
            session['is_guest'] = False
            return redirect(url_for('routes.dashboard'))
        flash("Invalid credentials.", "danger")
    return render_template('login.html')

@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("User already exists!", "danger")
            return redirect(url_for('routes.signup'))
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for('routes.login'))
    return render_template('signup.html')

@routes_bp.route('/guest-login')
def guest_login():
    session.clear()
    session['is_guest'] = True
    session['username'] = "Guest User"
    session['streak'] = 0
    flash("Logged in as Guest. Your data won't be saved!", "info")
    return redirect(url_for('routes.dashboard'))

@routes_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('routes.login'))

# ==========================================
# DASHBOARD
# ==========================================

@routes_bp.route('/dashboard')
def dashboard():
    if not is_allowed():
        return redirect(url_for('routes.login'))

    is_guest = session.get('is_guest', False)
    mastery_data = []
    mistake_count = 0
    correct_total = 0
    total_q = 0
    user_streak = 0
    username = "Guest"

    if not is_guest:
        username = current_user.username
        # 2. Data fetch karein
        mistake_count = MistakeBank.query.filter_by(user_id=current_user.id).count()
        results_list = QuizResult.query.filter_by(user_id=current_user.id).all()
        correct_total = sum([r.score for r in results_list]) if results_list else 0
        total_q = sum([r.total_questions for r in results_list]) if results_list else 0
        user_streak = getattr(current_user, 'streak', 0)
        mastery_data = TopicMastery.query.filter_by(user_id=current_user.id).all()

    try:
        ai_fact = llm.get_random_tech_fact()
    except:
        ai_fact = "AI is transforming how students master difficult concepts!"
    
    return render_template('dashboard.html', 
                           username=username,
                           is_guest=is_guest,
                           fun_fact=llm.get_fun_fact(),
                           correct_total=correct_total, 
                           incorrect_total=total_q - correct_total,
                           mistake_count=mistake_count,
                           streak=user_streak, # <--- Ye variable HTML mein use hoga
                           ai_fact=ai_fact,
                           topic_mastery=mastery_data)

# ==========================================
# STUDY HUB & DEEP DIVE (AI TUTOR)
# ==========================================

@routes_bp.route('/study-hub', methods=['GET', 'POST'])
def study_hub():
    if not is_allowed(): return redirect(url_for('routes.login'))
    
    if request.method == 'POST':
        source_type = request.form.get('source_type')
        content = ""
        try:
            if source_type == 'pdf':
                file = request.files.get('pdf_file')
                if file: content = extract_text_from_pdf(file)
            elif source_type == 'text':
                content = request.form.get('raw_text')
            elif source_type == 'topic':
                topic_name = request.form.get('topic_name')
                content = f"Summary for: {topic_name}"

            if not content:
                flash("add some context", "warning")
                return redirect(url_for('routes.study_hub'))

            study_bundle = llm.generate_study_material(content)
            session['last_study_data'] = study_bundle
            session.modified = True # Ensure session updates
            return redirect(url_for('routes.study_result'))
        
        except Exception as e:
            flash(f"AI Study Hub Error: {str(e)}", "danger")
            return redirect(url_for('routes.study_hub'))
    if 'last_study_data' in session:
        return redirect(url_for('routes.study_result'))
            
    return render_template('study_hub.html')

@routes_bp.route('/deep-dive', methods=['POST'])
def deep_dive():
    if not is_allowed(): return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        if not concept: return jsonify({"error": "No concept provided"}), 400
        analysis = llm.deep_dive(concept) 
        return jsonify({"analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes_bp.route('/extend-concept', methods=['POST'])
def extend_concept():
    if not is_allowed(): return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.get_json()
        topic = data.get('topic')
        if not topic: return jsonify({"error": "No topic"}), 400
        explanation = llm.extend_notes(topic)
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes_bp.route('/study-result')
def study_result():
    if not is_allowed(): return redirect(url_for('routes.login'))
    
    # Session se data uthao
    data = session.get('last_study_data')
    
    if not data:
        flash("No active study session found.", "info")
        return redirect(url_for('routes.study_hub'))
        
    return render_template('study_hub_result.html', data=data)
# ==========================================
# INTERACTIVE CASE CHALLENGE ROUTES
# ==========================================
@routes_bp.route('/start-challenge', methods=['POST'])
@login_required
def start_challenge():
    try:
        data = request.get_json()
        content = data.get('content_to_study')
        if not content:
            return jsonify({"success": False, "error": "No content provided"}), 400
        # Yahan 'mixed_cases' ki jagah llm_client ka method call karein
        # 'llm_client' aapka object hona chahiye jo LLMClient() se bana ho
        response = llm.get_mixed_cases(content) 
        
        # Session mein save karein taaki template use kar sake
        session['active_challenges'] = response.get('cases', [])
        
        return jsonify({
            "success": True, 
            "redirect": url_for('routes.view_challenges') # Aapka challenge page route
        })
    except Exception as e:
        print(f"Challenge Gen Error: {e}") # Yahi error logs mein aa rahi thi
        return jsonify({"success": False, "error": str(e)}), 500

@routes_bp.route('/challenges')
@login_required
def view_challenges():
    
    if not is_allowed(): 
        return redirect(url_for('routes.login'))
    
    # Session se save kiye huye cases uthana
    cases = session.get('active_challenges', [])
    
    if not cases:
        flash("No active challenges found. Please generate again.", "warning")
        return redirect(url_for('routes.study_hub'))
    
    return render_template('case_study_mixed.html', cases=cases)

#==========================
# QUIZ GENERATION ENGINE
# ==========================================

@routes_bp.route('/handle_generation', methods=['POST', 'GET'])
def handle_generation():
    if not is_allowed(): return redirect(url_for('routes.login'))
    
    mode = request.form.get('quiz_goal') or request.args.get('quiz_goal') or 'quiz'
    source_type = request.form.get('source_type') or request.args.get('source_type')
    count = int(request.form.get('count', 5))
    q_ids = []
    mastery_label = "General"

    try:
        if source_type == 'mistake':
            if session.get('is_guest'):
                flash("Guest users don't have a Mistake Bank!", "warning")
                return redirect(url_for('routes.dashboard'))
            
            mistakes = MistakeBank.query.filter_by(user_id=current_user.id).limit(count).all()
            if not mistakes:
                flash("Mistake Bank khali hai!", "info")
                return redirect(url_for('routes.dashboard'))
            
            for m in mistakes:
                new_q = Question(
                    question_text=q_data.get('question'), 
                    options_json=json.dumps(q_data.get('options')), 
                    correct_answer=q_data.get('correct_answer'), 
                    explanation=q_data.get('explanation',"Study Hard"), 
                    user_id=current_user.id
                )
                db.session.add(new_q)
                db.session.flush()
                q_ids.append(new_q.id)
            db.session.commit()
        
        else:
            content = ""
            if source_type == 'image':
                file = request.files.get('image_file')
                if file and file.filename != '':
                    
                    content = extract_text_from_image(file)
                    mastery_label = f"Image Scan ({file.filename})"
                    if not content:
                        flash("Image se text nahi nikal paya. Clear photo upload karein.", "danger")
                        return redirect(url_for('routes.dashboard'))
                else:
                    flash("Please upload an image first!", "danger")
                    return redirect(url_for('routes.dashboard'))
            # --- IMAGE UPLOAD LOGIC END ---

            elif source_type == 'pdf':
                file = request.files.get('pdf_file')
                if file and file.filename != '':
                    content = extract_text_from_pdf(file)
                    mastery_label = f"PDF: {file.filename}"
                    if not content:
                        flash("PDF se text nahi nikal paya.", "danger")
                        return redirect(url_for('routes.dashboard'))
                else:
                    flash("Please upload a PDF file!", "danger")
                    return redirect(url_for('routes.dashboard'))
            
            elif source_type == 'text':
                content = request.form.get('raw_text', "")
                mastery_label = "Custom Text"
            
            elif source_type == 'topic':
                mastery_label = request.form.get('topic_name', "General Study")
                content = f"Create a quiz on: {mastery_label}"

            # Final validation before Groq Call
            if not content or content.strip() == "":
                flash("Kuch toh content provide karo!", "warning")
                return redirect(url_for('routes.dashboard'))

            # AI Question Generation (Groq Call)
            raw_qs = llm.generate_questions(content, count)
            
            if not raw_qs:
                flash("AI fails to generate questions. Try again!", "danger")
                return redirect(url_for('routes.dashboard'))
                
            for q_data in raw_qs:
                new_q = Question(
                    question_text=q_data.get('question'),
                    options_json=json.dumps(q_data.get('options')),
                    correct_answer=q_data.get('correct_answer'),
                    explanation=q_data.get('explanation', "Study hard!"),
                    user_id=current_user.id if not session.get('is_guest') else None
                )
                db.session.add(new_q)
                db.session.flush()
                q_ids.append(new_q.id)

        db.session.commit()
        
        session.update({
            'active_questions': q_ids, 
            'current_idx': 0, 
            'score': 0, 
            'quiz_topic': mastery_label, 
            'quiz_goal': mode, 
            'user_answers': []
        })
        
        return redirect(url_for('routes.quiz_page', q_id=q_ids[0]))

    except Exception as e:
        db.session.rollback()
        print(f"Generation Error: {str(e)}")
        flash(f"System Error: {str(e)}", "danger")
        return redirect(url_for('routes.dashboard'))
      
# ==========================================
# QUIZ PAGE & ANSWERS
# ==========================================

@routes_bp.route('/quiz/<int:q_id>')
def quiz_page(q_id):
    if not is_allowed(): return redirect(url_for('routes.login'))
    question = Question.query.get_or_404(q_id)
    options = json.loads(question.options_json)
    q_list = session.get('active_questions', [])
    return render_template('quiz.html', question=question, options=options, 
                           current_num=session.get('current_idx', 0) + 1, 
                           total_num=len(q_list))

@routes_bp.route('/submit_answer/<int:q_id>', methods=['POST'])
def submit_answer(q_id):
    question = Question.query.get_or_404(q_id)
    user_ans = request.form.get('answer', '').strip()
    is_correct = (user_ans.lower() == str(question.correct_answer).lower())
    
    ans_list = session.get('user_answers', [])
    ans_list.append({'question': question.question_text, 'user_ans': user_ans, 
                     'correct_ans': question.correct_answer, 'is_correct': is_correct, 
                     'explanation': question.explanation})
    session['user_answers'] = ans_list
    
    if is_correct:
        session['score'] = session.get('score', 0) + 1
    elif not session.get('is_guest') and session.get('quiz_goal') == 'quiz':
        mistake = MistakeBank(user_id=current_user.id, question_text=question.question_text, 
                              correct_answer=question.correct_answer, options_json=question.options_json,
                              topic=session.get('quiz_topic', 'General'), explanation=question.explanation)
        db.session.add(mistake)
        db.session.commit()

    session['current_idx'] = session.get('current_idx', 0) + 1
    q_list = session.get('active_questions', [])
    if session['current_idx'] < len(q_list):
        return redirect(url_for('routes.quiz_page', q_id=q_list[session['current_idx']]))
    return redirect(url_for('routes.results'))

# ==========================================
# RESULTS, REPORTS & LIBRARY
# ==========================================
@routes_bp.route('/results')
def results():
    score = session.get('score', 0)
    user_answers = session.get('user_answers', [])
    total = len(user_answers)
    raw_topic = session.get('quiz_topic', 'AI Analysis')
    accuracy = (score / total * 100) if total > 0 else 0
    
    history_labels = []
    history_scores = []
    is_guest = session.get('is_guest', False)

    try:
        if not is_guest and current_user.is_authenticated:
            # 1. Aaj ka result save karo
            new_res = QuizResult(
                user_id=current_user.id, 
                score=score, 
                total_questions=total,
                topic=raw_topic,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_res)
            
            # 2. STREAK LOGIC (Strict Check)
            today = datetime.utcnow().date()
            # Pichla result dhoondo jo AAJ se pehle ka ho (timestamp < today)
            last_res = QuizResult.query.filter(
                QuizResult.user_id == current_user.id,
                QuizResult.timestamp < today 
            ).order_by(QuizResult.timestamp.desc()).first()
            
            if last_res:
                last_date = last_res.timestamp.date()
                # Agar pichla result thik KAL ka tha
                if last_date == today - timedelta(days=1):
                    # Check karo ki aaj pehle streak update ho chuki hai? 
                    # (Taaki ek din mein 10 bar quiz dene par 10 streak na badhe)
                    if current_user.last_quiz_date != today:
                        current_user.streak += 1
                # Agar 1 din se zyada ka gap hai
                elif last_date < today - timedelta(days=1):
                    current_user.streak = 1
            else:
                # Agar ye user ka pehla quiz hai
                if current_user.streak == 0:
                    current_user.streak = 1
            
            # Update last quiz date
            current_user.last_quiz_date = today

            # 3. Topic Mastery Update (Dashboard Fix)
            mastery = TopicMastery.query.filter_by(user_id=current_user.id, topic=raw_topic).first()
            if not mastery:
                mastery = TopicMastery(user_id=current_user.id, topic=raw_topic, correct_count=0, total_count=0)
                db.session.add(mastery)
            mastery.correct_count += score
            mastery.total_count += total

            db.session.commit()
            
            # Chart Data
            results_query = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.timestamp.asc()).all()
            for r in results_query[-5:]:
                history_labels.append(r.timestamp.strftime("%d %b"))
                history_scores.append(r.score)
        else:
            history_labels = ["Current"]
            history_scores = [score]

    except Exception as e:
        db.session.rollback()
        print(f"Error in Results: {e}")

    return render_template('results.html', 
                           score=score, 
                           total=total, 
                           accuracy=accuracy, 
                           user_answers=user_answers, 
                           is_guest=is_guest,
                           display_topic=raw_topic,
                           history_labels=history_labels, 
                           history_scores=history_scores)
    
@routes_bp.route('/download_report/<int:res_id>')
@login_required
def download_report(res_id):
    res = QuizResult.query.get_or_404(res_id)
    if res.user_id != current_user.id: return redirect(url_for('routes.dashboard'))

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Quiz Performance Report")
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Score: {res.score} / {res.total_questions}")
    p.drawString(100, 700, f"Date: {res.timestamp.strftime('%d-%m-%Y %H:%M')}")
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Report_{res.id}.pdf")

@routes_bp.route('/library')
@login_required # Ye zaroori hai taaki anonymous user crash na kare
def library():
    # 1. Guest check
    if session.get('is_guest'):
        flash("Library is only for registered users to track progress! 🚀", "info")
        return redirect(url_for('routes.signup'))
    user_questions = Question.query.filter_by(user_id=current_user.id).all()
    print(f"DEBUG: User ID {current_user.id} has {len(user_questions)} quizzes in DB")
    return render_template('library.html', questions=user_questions)

@routes_bp.route('/review-mistakes')
@login_required
def review_mistakes():
    raw_mistakes = MistakeBank.query.filter_by(user_id=current_user.id).all()
    processed_mistakes = []
    for m in raw_mistakes:
        processed_mistakes.append({
            "id": m.id, "question": m.question_text, "correct_answer": m.correct_answer,
            "options": json.loads(m.options_json), "topic": m.topic, "explanation": m.explanation
        })
    return render_template('review.html', mistakes=processed_mistakes)
