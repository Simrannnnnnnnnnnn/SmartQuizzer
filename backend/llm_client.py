import json
import os
import time
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.FAST_MODEL = "llama-3.1-8b-instant"      
        self.POWER_MODEL = "llama-3.3-70b-versatile"  

    def _safe_request(self, func, *args, **kwargs):
        
        max_retries = 3
        retry_delay = 2  
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  
                else:
                    raise e

    def get_fun_fact(self):
        prompt = "Generate one short, mind-blowing fun fact about AI. Under 20 words."
        try:
            completion = self._safe_request(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.FAST_MODEL,
                timeout=10.0
            )
            return completion.choices[0].message.content
        except Exception:
            return "AI can process data millions of times faster than a human brain!"

    # llm_client.py ke andar LLMClient class mein ye add karein:
    def get_random_tech_fact(self):
        try:
            prompt = "Give me one interesting, short, and surprising technology or AI fact in one sentence."
        # Aapka jo bhi model calling logic hai (Groq/OpenAI)
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Ya aapka preferred model
                messages=[{"role": "user", "content": prompt}]
        )
            return response.choices[0].message.content
        except Exception as e:
            return "AI is amazing at helping you study!" # Fallback fact
    
    def generate_questions(self, content, count, quiz_format='mcq'):
        if not content: return []
        
        system_prompt = (
            "You are a strict academic examiner. You output ONLY valid JSON. "
            "Structure: {\"questions\": [{\"question\": \"...\", \"options\": {\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\"}, \"correct_answer\": \"A\", \"explanation\": \"...\"}]} "
        )

        format_rule = "Generate MCQs with 4 options. 'correct_answer' must be the key (A, B, C, or D)."
        if quiz_format == 'tf':
            format_rule = "True/False questions. 'options' must be {'A': 'True', 'B': 'False'}."

        user_prompt = f"TASK: Generate {count} {quiz_format} questions.\nSTRICT RULE: {format_rule}\nCONTENT: {content[:3500]}"

        try:
            completion = self._safe_request(
                self.client.chat.completions.create,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.POWER_MODEL,
                response_format={"type": "json_object"},
                temperature=0.3,
                timeout=30.0
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("questions", [])
        except Exception as e:
            print(f"Error in Gen: {e}")
            return []

    def deep_dive(self, text):
        """Sophisticated academic breakdown of the concept."""
        prompt = (
            f"Provide a sophisticated, deep-dive analysis of: {text}. "
            "Focus on core principles and technical applications. Professional tone."
        )
        try:
            completion = self._safe_request(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.FAST_MODEL,
                timeout=20.0
            )
            return completion.choices[0].message.content
        except Exception:
            return "Deep dive unavailable. Please try again."

    def generate_study_material(self, content):
        prompt = (
            f"Analyze: {content[:3000]}. Return JSON ONLY with keys: "
            "\"shorthand_notes\" (list), \"detailed_revision\" (string), \"mnemonic_story\" (string), \"flashcards\" (list)."
        )
        try:
            response = self._safe_request(
                self.client.chat.completions.create,
                model=self.POWER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=35.0
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"shorthand_notes": ["Error loading notes."], "detailed_revision": "", "mnemonic_story": "", "flashcards": []}
    def generate_performance_insight(self, mistakes_list, topic):
       
        if not mistakes_list:
            return f"Outstanding! You have mastered {topic}. Try a harder level or a related subject to keep the momentum going! 🚀"

        mistake_context = "\n".join([f"- {m['question']}" for m in mistakes_list[:3]]) 
        
        prompt = f"""
        User just took a quiz on '{topic}'.
        They struggled with these specific questions:
        {mistake_context}
        
        Provide a 2-line encouraging advice. 
        1st line: Identify the weak sub-topic based on these questions.
        2nd line: Give a specific actionable tip to improve.
        Keep it friendly, concise, and professional.
        """
        
        try:
          
            completion = self._safe_request(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.FAST_MODEL,
                temperature=0.7,
                timeout=15.0
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Insight Error: {e}")
            return f"Keep practicing {topic}! Review your mistakes to strengthen your core concepts."
