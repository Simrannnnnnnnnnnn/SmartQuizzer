import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"

headers = {"Authorization": f"Bearer {key}"}
payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [{"role": "user", "content": "say hello"}]
}

res = requests.post(url, json=payload, headers=headers)
print(res.json())