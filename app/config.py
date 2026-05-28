import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
ANALYZER_URL = os.getenv(
    "ANALYZER_URL",
    "http://localhost:11434/api/generate",
)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "900"))
OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "1"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_VAD_MIN_SECONDS = int(
    os.getenv("WHISPER_VAD_MIN_SECONDS", "120")
)


def _default_creds_file() -> str:
    configured_path = os.getenv("GOOGLE_CREDS_FILE")

    if configured_path:
        return configured_path

    credentials_dir = Path("credentials")
    legacy_path = credentials_dir / "google_credentials.json"

    if legacy_path.exists():
        return str(legacy_path)

    matches = sorted(credentials_dir.glob("*.json"))

    if len(matches) == 1:
        return str(matches[0])

    return str(legacy_path)


GOOGLE_CREDS_FILE = _default_creds_file()
