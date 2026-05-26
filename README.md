# call-analyzer

`call-analyzer` pulls call recordings from Google Drive, transcribes them with Whisper, scores the calls with a local Ollama model, and appends the results to a Google Sheet.

## What the project does

Pipeline:

1. Read `.mp3` files from a configured Google Drive folder, including nested folders.
2. Download each audio file into `data/audio/`.
3. Preprocess long calls with `ffmpeg` silence removal.
4. Transcribe the call with Whisper.
5. Send the transcript to Ollama for QA analysis.
6. Append the result to a Google Sheet.
7. Highlight bad calls in red.

## Project structure

```text
app/
  analyzer.py      # Sends transcripts to Ollama and computes total_score
  config.py        # Loads environment variables and resolves credentials path
  drive.py         # Google Drive client for listing and downloading audio
  main.py          # End-to-end batch runner
  prompts.py       # System prompt for the call QA model
  sheets.py        # Google Sheets writer and row highlighter
  transcriber.py   # Whisper transcription and audio preprocessing
scripts/
  list_drive_files.py
tests/
  test_analyzer.py
  test_config.py
  test_drive.py
  test_transcriber.py
data/
  audio/
  processed_audio/
  transcripts/
credentials/
```

## Requirements

- Python `>=3.14`
- `ffmpeg`
- `ffprobe`
- Access to:
  - a Google Drive folder with call recordings
  - a Google Sheet for output
  - a Google service account JSON credential file
- Ollama running locally on `http://localhost:11434`
- An Ollama model available locally, default: `qwen2.5:7b`

## Installation

Install dependencies with your preferred tool. This repo is configured with `uv`.

```bash
uv sync
```

If you are not using `uv`, install the dependencies declared in `pyproject.toml`.

## Configuration

Create `.env` in the project root.

```env
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_CREDS_FILE=credentials/service-account.json
OLLAMA_MODEL=qwen2.5:7b
WHISPER_MODEL=base
WHISPER_VAD_MIN_SECONDS=120
```

### Environment variables

- `GOOGLE_DRIVE_FOLDER_ID`: Root Drive folder that contains call recordings.
- `GOOGLE_SHEET_ID`: Target Google Sheet ID.
- `GOOGLE_CREDS_FILE`: Path to the Google service account credentials file.
- `OLLAMA_MODEL`: Ollama model name used for transcript analysis.
- `WHISPER_MODEL`: Whisper model name used for transcription.
- `WHISPER_VAD_MIN_SECONDS`: Calls longer than this are preprocessed with silence removal.

### Credentials lookup behavior

If `GOOGLE_CREDS_FILE` is not set, the app tries:

1. `credentials/google_credentials.json`
2. The only `*.json` file in `credentials/`, if exactly one exists
3. `credentials/google_credentials.json` as a fallback path

The service account must have access to both the Drive folder and the Google Sheet.

## Running Ollama

Start Ollama separately and make sure the configured model is available:

```bash
ollama serve
ollama pull qwen2.5:7b
```

## Usage

Run the full pipeline:

```bash
uv run python -m app.main
```

List visible Drive audio files without processing them:

```bash
uv run python scripts/list_drive_files.py
```

## Output

- Downloaded audio: `data/audio/`
- Preprocessed audio: `data/processed_audio/`
- Saved transcripts: `data/transcripts/`
- Analysis rows: appended to the configured Google Sheet

The analyzer expects JSON from Ollama with these fields:

- `greeting`
- `politeness`
- `identified_need`
- `car_body`
- `car_year`
- `mileage`
- `diagnostic_offer`
- `closing`
- `farewell`
- `toxicity`
- `result`
- `comment`
- `bad_call`
- `top_work`

`total_score` is computed locally as the sum of:

- `greeting`
- `politeness`
- `identified_need`
- `car_body`
- `car_year`
- `mileage`
- `diagnostic_offer`
- `closing`
- `farewell`

## Testing

Run tests with:

```bash
uv run pytest
```

Current tests cover:

- analyzer scoring
- credentials path resolution
- Drive recursion and filename sanitization
- transcript persistence
- ffmpeg presence checks
- long-audio preprocessing
- language detection preference

## Notes and assumptions

- Only `.mp3` files are processed from Google Drive.
- Drive traversal is recursive.
- The transcriber is currently configured to return Ukrainian (`uk`) as the supported transcription language.
- Long-call preprocessing depends on local `ffmpeg` and `ffprobe`.
- Ollama analysis is done against a local HTTP endpoint and is not retried on failure.

## Main entry points

- [app/main.py](/home/nft/Desktop/call-analyzer/app/main.py)
- [scripts/list_drive_files.py](/home/nft/Desktop/call-analyzer/scripts/list_drive_files.py)
