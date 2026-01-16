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

    # FIXED INDENTATION HERE
    def get_random_tech_fact(self):
        try:
            response = self.client.chat.completions.create(
                model=self.POWER_MODEL,
                messages=[{"role": "user", "content": "Tell me one amazing tech fact in one short sentence."}]
            )
            return response.choices[0].message.content
        except Exception:
            return "AI is making learning 10x faster!"

    def get_topic_from_content(self, text):
        try:
            # Added "Direct answer only" to stop AI from talking too much
            prompt = f"Identify the main subject of this text. Return ONLY the topic name in 2-3 words. No extra text: {text}"
            response = self.client.chat.completions.create(
                model=self.POWER_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip().replace('"', '').replace('Topic:', '')
        except Exception:
            return "Study Material"
    
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
    def get_mixed_cases(self, content):
    system_prompt = (
        "You are a strict academic expert. Output ONLY a valid JSON list of objects. "
        "Each object must represent either a 'Case Study Scenario' or a 'Give Reason' question. "
        "STRICT STRUCTURE: "
        "For Case Studies: {'type': 'case', 'scenario': '...', 'question': '...', 'answer': '...', 'key_points': ['word1', 'word2']} "
        "For Direct Reasoning: {'type': 'reason', 'question': '...', 'answer': '...', 'key_points': ['word1', 'word2']} "
        "Ensure the 'answer' is a logical explanation and 'key_points' are essential technical terms."
    )
    
    # Ye hai tera specific style wala instruction
    user_prompt = (
        f"Based on this content: {content[:3000]}\n\n"
        "TASK: Generate a mix of:\n"
        "1. A real-world case study scenario followed by a logical question.\n"
        "2. Two 'Give Reason' type questions that test deep conceptual understanding.\n"
        "Provide correct answers with logical reasoning for all."
    )
    
    try:
        completion = self._safe_request(
            self.client.chat.completions.create,
            model=self.POWER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Note: response_format 'json_object' expects a JSON object {}, 
            # but since we want a list [], we handle it carefully.
            response_format={"type": "json_object"} 
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "[]" # Return empty list string to prevent crash
            
    def deep_dive(self, text):
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
            return f"Outstanding! You have mastered {topic}. Try a harder level or a related subject! 🚀"

        mistake_context = "\n".join([f"- {m['question']}" for m in mistakes_list[:3]]) 
        
        prompt = f"""
        User just took a quiz on '{topic}'.
        They struggled with these questions:
        {mistake_context}
        
        1st line: Identify weak sub-topic.
        2nd line: Actionable tip to improve.
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
        except Exception:
            return f"Keep practicing {topic}! Review your mistakes to strengthen your core concepts."
    
