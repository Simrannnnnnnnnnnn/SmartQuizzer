import json
import os
import time
from groq import Groq

class LLMClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.FAST_MODEL = "llama-3.1-8b-instant"      # Fast generation
        self.POWER_MODEL = "llama-3.3-70b-versatile"  # Strict Logic

    def _safe_request(self, func, *args, **kwargs):
        """AI Busy error handles karne ke liye auto-retry logic."""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Attempt {attempt + 1} failed (AI Busy/Error): {e}")
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
            return "Did you know? AI can process data millions of times faster than a human brain!"

    def generate_questions(self, content, count, quiz_format='mcq', source_type='text'):
        if not content: return []
        
        # FIX: Indentation corrected here
        system_prompt = (
            "You are a strict academic examiner. You output ONLY valid JSON. "
            "The JSON must follow this exact structure: {\"questions\": [{\"question\": \"...\", \"options\": {\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\"}, \"correct_answer\": \"A\", \"explanation\": \"...\"}]} "
            "No small talk, no code blocks."
        )

        if quiz_format == 'tf':
            format_rule = "Generate True/False questions. 'options' MUST be {'A': 'True', 'B': 'False'}. 'correct_answer' must be 'A' or 'B'."
        elif quiz_format == 'theory':
            format_rule = "Generate descriptive questions. 'options' MUST be empty {}. Provide an 'ideal_answer' key."
        else:
            format_rule = "Generate MCQs with 4 options (A, B, C, D). 'correct_answer' must be the key (e.g., 'A')."

        user_prompt = f"TASK: Generate {count} {quiz_format} questions.\nSTRICT RULE: {format_rule}\nCONTENT: {content[:3500]}\nOUTPUT: JSON only."

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
            raw_content = completion.choices[0].message.content
            data = json.loads(raw_content)
            
            # AI check logic
            if isinstance(data, list):
                return data
            return data.get("questions", [])
            
        except Exception as e:
            print(f"Strict Error in Question Gen: {e}")
            return []

    def generate_study_material(self, content):
        """Generates structured notes with retry protection."""
        # FIX: Added strict JSON instruction here too
        prompt = (
            f"Analyze: {content[:3000]}. Return JSON ONLY with keys: "
            "\"shorthand_notes\" (list), \"detailed_revision\" (string), \"mnemonic_story\" (string), \"flashcards\" (list of dicts)."
        )
        try:
            response = self._safe_request(
                self.client.chat.completions.create,
                model=self.POWER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=35.0 # Shoda zyaada time diya hai revision ke liye
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Study Material Error: {e}")
            return {"shorthand_notes": ["AI is busy, please try again."], "detailed_revision": "", "mnemonic_story": "", "flashcards": []}

    def simplify_content(self, text):
        prompt = f"Explain like I'm 10 with analogies: {text}"
        try:
            completion = self._safe_request(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.FAST_MODEL,
                timeout=15.0
            )
            return completion.choices[0].message.content
        except Exception:
            return "AI is taking a break. Please click ELI10 again in a few seconds."

    def extend_notes(self, topic_text):
        """Notes extend karne ke liye specific method."""
        prompt = f"Explain this concept briefly in 2-3 simple sentences for quick revision: {topic_text}"
        try:
            completion = self._safe_request(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.FAST_MODEL, 
                temperature=0.5,
                timeout=15.0
            )
            return completion.choices[0].message.content.strip()
        except Exception:
            return "AI busy right now. Please try again."
