import json
import re
from pathlib import Path

import requests

from app.config import (
    ANALYZER_URL,
    OLLAMA_MODEL,
    OLLAMA_RETRIES,
    OLLAMA_TIMEOUT,
)
from app.prompts import SYSTEM_PROMPT


class CallAnalyzer:
    def __init__(self):
        self.url = ANALYZER_URL
        self.timeout = OLLAMA_TIMEOUT
        self.retries = OLLAMA_RETRIES

    def analyze(self, transcript: str, source_name: str):
        output_path = self._analysis_path(source_name)

        if output_path.exists():
            return json.loads(
                output_path.read_text(encoding="utf-8")
            )

        prompt = f"""
{SYSTEM_PROMPT}

Transcript:
{transcript}
"""
        response = None
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    self.url,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                break
            except requests.Timeout:
                if attempt == self.retries:
                    raise

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

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return result

    @staticmethod
    def _analysis_path(source_name: str):
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", source_name).strip("._")
        if not safe_name:
            safe_name = "analysis"

        return Path("data/analysis") / f"{safe_name}.json"
