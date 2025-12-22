import json
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def generate_questions(self, content, count, quiz_format='mcq'):
        if not content: return []
        
        # Explicitly telling the AI to use A, B, C, D keys
        prompt = f"""
        Generate {count} {quiz_format} questions from: {content[:2000]}
        Return ONLY JSON. 
        For MCQs, the 'options' field MUST be a dictionary with keys "A", "B", "C", "D".
        
        JSON Structure:
        {{
          "questions": [
            {{
              "question_text": "...",
              "options": {{"A": "option1", "B": "option2", "C": "option3", "D": "option4"}},
              "correct_answer": "A",
              "explanation": "..."
            }}
          ]
        }}
        """
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("questions", [])
        except:
            return []