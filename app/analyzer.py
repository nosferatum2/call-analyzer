import json
import requests

from app.config import OLLAMA_MODEL
from app.prompts import SYSTEM_PROMPT


class CallAnalyzer:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"

    def analyze(self, transcript: str):
        prompt = f"""
{SYSTEM_PROMPT}

Transcript:
{transcript}
"""

        response = requests.post(
            self.url,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=300
        )
        response.raise_for_status()

        data = response.json()

        text = data["response"].strip()

        result = json.loads(text)

        scores = [
            result.get("greeting", 0),
            result.get("politeness", 0),
            result.get("identified_need", 0),
            result.get("car_body", 0),
            result.get("car_year", 0),
            result.get("mileage", 0),
            result.get("diagnostic_offer", 0),
            result.get("closing", 0),
            result.get("farewell", 0),
        ]

        result["total_score"] = sum(scores)

        return result
