from unittest.mock import Mock, patch


@patch("app.transcriber.shutil.which")
@patch("app.transcriber.Transcriber._prepare_audio_path")
@patch("app.transcriber.whisper.load_audio")
@patch("app.transcriber.whisper.pad_or_trim")
@patch("app.transcriber.whisper.log_mel_spectrogram")
@patch("app.transcriber.whisper.load_model")
@patch("app.transcriber.Path.write_text")
@patch("app.transcriber.Path.mkdir")
def test_transcribe_creates_transcript_directory(
    mock_mkdir,
    mock_write_text,
    mock_load_model,
    mock_log_mel,
    mock_pad_or_trim,
    mock_load_audio,
    mock_prepare_audio_path,
    mock_which,
):
    mock_which.side_effect = ["/usr/bin/ffmpeg", "/usr/bin/ffprobe"]
    mock_prepare_audio_path.return_value = "records/call.vad.wav"
    mock_load_audio.return_value = "audio"
    mock_pad_or_trim.return_value = "trimmed-audio"
    mel = Mock()
    mel.to.return_value = "mel-on-device"
    mock_log_mel.return_value = mel
    model = Mock()
    model.transcribe.return_value = {
        "text": "hello",
        "language": "uk",
    }
    model.detect_language.return_value = (
        None,
        {"uk": 0.8, "ru": 0.2},
    )
    model.device = "cpu"
    model.dims.n_mels = 128
    mock_load_model.return_value = model

    from app.transcriber import LANGUAGE_PROMPTS, Transcriber

    text, transcript_path = Transcriber().transcribe("records/call.mp3")

    assert text == "hello"
    assert transcript_path == "data/transcripts/call.txt"
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_write_text.assert_called_once_with("hello", encoding="utf-8")
    model.transcribe.assert_called_once_with(
        "records/call.vad.wav",
        language="uk",
        fp16=False,
        initial_prompt=LANGUAGE_PROMPTS["uk"],
        temperature=0,
        condition_on_previous_text=False,
    )
    mock_log_mel.assert_called_once_with(
        "trimmed-audio",
        n_mels=128,
    )


@patch("app.transcriber.shutil.which")
def test_transcriber_requires_ffmpeg(mock_which):
    mock_which.return_value = None

    from app.transcriber import Transcriber

    try:
        Transcriber()
    except RuntimeError as exc:
        assert "ffmpeg is not installed or is not in PATH" in str(exc)
    else:
        raise AssertionError("RuntimeError was not raised")


@patch("app.transcriber.shutil.which")
@patch("app.transcriber.Path.mkdir")
@patch("app.transcriber.whisper.load_model")
@patch("app.transcriber.subprocess.run")
def test_prepare_audio_path_runs_vad_for_long_audio(
    mock_run,
    mock_load_model,
    mock_mkdir,
    mock_which,
):
    mock_which.side_effect = ["/usr/bin/ffmpeg", "/usr/bin/ffprobe"]
    mock_load_model.return_value = Mock()
    mock_run.side_effect = [
        Mock(stdout="180\n"),
        Mock(stdout=""),
    ]

    from app.transcriber import Transcriber

    path = Transcriber()._prepare_audio_path("records/call.mp3")

    assert path == "data/processed_audio/call.vad.wav"
    assert mock_run.call_count == 2


@patch("app.transcriber.shutil.which")
@patch("app.transcriber.whisper.log_mel_spectrogram")
@patch("app.transcriber.whisper.pad_or_trim")
@patch("app.transcriber.whisper.load_audio")
@patch("app.transcriber.whisper.load_model")
def test_detect_language_prefers_ukrainian_or_russian(
    mock_load_model,
    mock_load_audio,
    mock_pad_or_trim,
    mock_log_mel,
    mock_which,
):
    mock_which.side_effect = ["/usr/bin/ffmpeg", "/usr/bin/ffprobe"]
    mock_load_audio.return_value = "audio"
    mock_pad_or_trim.return_value = "trimmed-audio"
    mel = Mock()
    mel.to.return_value = "mel-on-device"
    mock_log_mel.return_value = mel
    model = Mock()
    model.detect_language.return_value = (
        None,
        {"en": 0.9, "uk": 0.7, "ru": 0.1},
    )
    model.device = "cpu"
    model.dims.n_mels = 128
    mock_load_model.return_value = model

    from app.transcriber import Transcriber

    language = Transcriber()._detect_language("records/call.mp3")

    assert language == "uk"
