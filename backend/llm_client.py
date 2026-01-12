import json
import os
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        
        self.FAST_MODEL = "llama-3.1-8b-instant"      # Fact checking/Fast generation
        self.POWER_MODEL = "llama-3.3-70b-versatile"  # Strict Logic & Theory questions

    def get_fun_fact(self):
        prompt = "Generate one short, mind-blowing fun fact about AI. Under 20 words."
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.FAST_MODEL,
            )
            return completion.choices[0].message.content
        except Exception:
            return "Did you know? AI can process data millions of times faster than a human brain!"

    def generate_questions(self, content, count, quiz_format='mcq', source_type='text'):
        if not content: return []

        system_prompt = (
            "You are a strict academic examiner. You output ONLY valid JSON. "
            "No small talk, no code blocks, no explanations outside the JSON."
        )

        
        if quiz_format == 'tf':
            format_rule = "Generate True/False questions. 'options' MUST be {'A': 'True', 'B': 'False'}. 'correct_answer' must be 'A' or 'B'."
        elif quiz_format == 'theory':
            format_rule = "Generate descriptive questions. 'options' MUST be empty {}. Provide an 'ideal_answer' key with the long-form answer."
        else:
            format_rule = "Generate MCQs with 4 options (A, B, C, D). 'correct_answer' must be the key (e.g., 'A')."

        user_prompt = f"""
        TASK: Generate {count} {quiz_format} questions.
        STRICT RULE: {format_rule}
        CONTENT: {content[:4000]}

        OUTPUT STRUCTURE:
        {{
          "questions": [
            {{
              "question_text": "...",
              "options": {{...}},
              "correct_answer": "...",
              "explanation": "...",
              "ideal_answer": "..."
            }}
          ]
        }}
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.POWER_MODEL,
                response_format={"type": "json_object"},
                temperature=0.1  # Accuracy ke liye temperature low rakha hai
            )
            raw_content = completion.choices[0].message.content
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()
            data = json.loads(raw_content)
            return data.get("questions", [])
        except Exception as e:
            print(f"Strict Error: {e}")
            return []

    def generate_study_material(self, content):
        """Generates structured notes and flashcards."""
        prompt = f"Analyze: {content}. Return JSON with shorthand_notes (list), detailed_revision (paragraph), mnemonic_story, and flashcards."
        try:
            response = self.client.chat.completions.create(
                model=self.POWER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"shorthand_notes": ["Error"], "detailed_revision": "", "mnemonic_story": "", "flashcards": []}

    def simplify_content(self, text):
        prompt = f"Explain like I'm 10 with analogies: {text}"
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.FAST_MODEL
            )
            return completion.choices[0].message.content
        except Exception:
            return "Could not simplify at this moment."
