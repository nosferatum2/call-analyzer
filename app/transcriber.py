from pathlib import Path
import shutil
import subprocess

import whisper

from app.config import WHISPER_MODEL, WHISPER_VAD_MIN_SECONDS

SUPPORTED_LANGUAGES = ("uk",)
LANGUAGE_PROMPTS = {
    "uk": (
        "This is a Ukrainian phone call. "
        "Transcribe it accurately in Ukrainian and keep names, numbers, "
        "and automotive terms literal."
    ),
}


class Transcriber:
    def __init__(
            self,
            model_name=WHISPER_MODEL,
            languages=SUPPORTED_LANGUAGES,
            vad_min_seconds=WHISPER_VAD_MIN_SECONDS,
    ):
        if shutil.which("ffmpeg") is None:
            raise RuntimeError(
                "ffmpeg is not installed or is not in PATH"
            )
        if shutil.which("ffprobe") is None:
            raise RuntimeError(
                "ffprobe is not installed or is not in PATH"
            )

        self.languages = tuple(languages)
        self.vad_min_seconds = vad_min_seconds
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_path: str):
        transcript_path = self._transcript_path(audio_path)
        cached_text = self._read_cached_transcript(
            transcript_path
        )

        if cached_text is not None:
            return cached_text, str(transcript_path)

        prepared_audio_path = self._prepare_audio_path(audio_path)
        language = self._detect_language(prepared_audio_path)

        result = self.model.transcribe(
            prepared_audio_path,
            language=language,
            fp16=False,
            initial_prompt=LANGUAGE_PROMPTS[language],
            temperature=0,
            condition_on_previous_text=False
        )

        text = result["text"]

        transcript_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        transcript_path.write_text(
            text,
            encoding="utf-8"
        )

        return text, str(transcript_path)

    @staticmethod
    def _transcript_path(audio_path: str) -> Path:
        return (
                Path("data/transcripts") /
                f"{Path(audio_path).stem}.txt"
        )

    @staticmethod
    def _read_cached_transcript(transcript_path: Path) -> str | None:
        if transcript_path.exists():
            return transcript_path.read_text(
                encoding="utf-8"
            )

        return None

    def _detect_language(self, audio_path: str) -> str:
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(
            audio,
            n_mels=self.model.dims.n_mels,
        ).to(self.model.device)

        _, probabilities = self.model.detect_language(mel)

        return max(
            self.languages,
            key=lambda language: probabilities.get(
                language,
                float("-inf"),
            ),
        )

    def _prepare_audio_path(self, audio_path: str) -> str:
        if self._probe_duration(audio_path) < self.vad_min_seconds:
            return audio_path

        output_dir = Path("data/processed_audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        processed_path = output_dir / (
            f"{Path(audio_path).stem}.vad.wav"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            audio_path,
            "-af",
            (
                "silenceremove="
                "start_periods=1:"
                "start_silence=0.3:"
                "start_threshold=-45dB:"
                "stop_periods=-1:"
                "stop_silence=0.5:"
                "stop_threshold=-45dB"
            ),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(processed_path),
        ]

        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

        return str(processed_path)

    @staticmethod
    def _probe_duration(audio_path: str) -> float:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

        return float(result.stdout.strip())
