from .models import db, Question
from sqlalchemy import func

class AdaptiveEngine:
    """
    Tracks user proficiency and selects the optimal next question difficulty.
    Uses simplified Item Response Theory (IRT) concepts.
    """
    def __init__(self, proficiency=0.0):
        # The proficiency (theta) is loaded from the session for continuity
        self.proficiency_theta = proficiency 

    def _calculate_new_proficiency(self, question_difficulty, is_correct):
        """
        Simplified Elo/IRT update: Adjusts user's proficiency (theta).
        """
        difficulty_map = {'Easy': 0.5, 'Medium': 1.0, 'Hard': 1.5}
        d_score = difficulty_map.get(question_difficulty, 1.0)
        
        # K-factor: sensitivity of the proficiency change
        k_factor = 0.2 
        
        # Base change
        change = k_factor * (1 if is_correct else -1)
        
        if is_correct:
            # Reward is smaller if the question was much easier than user's skill
            if self.proficiency_theta > d_score:
                 change *= 0.5
        else:
            # Penalty is smaller if the question was much harder than user's skill
            if d_score > self.proficiency_theta:
                change *= 0.7
        
        self.proficiency_theta += change
        
        # Keep theta bounded between -1.0 (Beginner) and 3.0 (Expert)
        self.proficiency_theta = max(-1.0, min(3.0, self.proficiency_theta))
        
        return self.proficiency_theta

    def _get_target_difficulty(self):
        """Determines the required difficulty label for the next question."""
        if self.proficiency_theta < 0.7:
            return 'Easy'
        elif self.proficiency_theta < 1.3:
            return 'Medium'
        else:
            return 'Hard'

    def get_next_question_id(self, last_question_id, is_correct, all_session_ids, used_ids):
        """
        1. Updates user proficiency based on last answer.
        2. Finds the optimal next question matching the new proficiency.
        """
        last_question = Question.query.get(last_question_id)
        
        if last_question:
            self._calculate_new_proficiency(last_question.difficulty_level, is_correct)
            
        # Filter out questions already answered
        available_ids = [q_id for q_id in all_session_ids if q_id not in used_ids]

        if not available_ids:
            return None # Quiz finished
            
        target_difficulty = self._get_target_difficulty()
        
        # Query for a random question matching the target difficulty
        next_q = Question.query.filter(
            Question.id.in_(available_ids),
            Question.difficulty_level == target_difficulty
        ).order_by(func.random()).first()

        # Fallback: if no questions of that difficulty remain, pick any available
        if not next_q:
             next_q = Question.query.filter(Question.id.in_(available_ids)).order_by(func.random()).first()

        return next_q.id if next_q else None