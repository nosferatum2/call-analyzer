from pathlib import Path
from unittest.mock import Mock, patch


@patch("app.drive.io.FileIO")
@patch("app.drive.MediaIoBaseDownload")
@patch("app.drive.build")
@patch("app.drive.Credentials.from_service_account_file")
@patch("app.drive.Path.mkdir")
def test_download_file_creates_output_directory_and_sanitizes_filename(
    mock_mkdir,
    mock_creds,
    mock_build,
    mock_downloader,
    mock_file_io,
):
    downloader = Mock()
    downloader.next_chunk.side_effect = [(None, False), (None, True)]
    mock_downloader.return_value = downloader
    service = Mock()
    mock_build.return_value = service
    service.files.return_value.get_media.return_value = Mock()
    mock_file_io.return_value = Mock()

    from app.drive import GoogleDriveClient

    client = GoogleDriveClient()
    path = client.download_file("file-id", "../call.mp3")

    assert path == str(Path("data/audio/call.mp3"))
    mock_downloader.assert_called_once()
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


@patch("app.drive.build")
@patch("app.drive.Credentials.from_service_account_file")
def test_list_audio_files_recurses_and_keeps_only_mp3(
    mock_creds,
    mock_build,
):
    service = Mock()
    files_resource = Mock()
    service.files.return_value = files_resource
    mock_build.return_value = service

    root_response = Mock()
    root_response.execute.return_value = {
        "files": [
            {
                "id": "folder-1",
                "name": "Dzvinky",
                "mimeType": "application/vnd.google-apps.folder",
            },
            {
                "id": "doc-1",
                "name": "Report",
                "mimeType": "application/vnd.google-apps.document",
            },
        ]
    }
    nested_response = Mock()
    nested_response.execute.return_value = {
        "files": [
            {
                "id": "audio-1",
                "name": "call-1.mp3",
                "mimeType": "audio/mpeg",
            },
            {
                "id": "audio-2",
                "name": "call-2.wav",
                "mimeType": "audio/wav",
            },
        ]
    }
    files_resource.list.side_effect = [
        root_response,
        nested_response,
    ]

    from app.drive import GoogleDriveClient

    client = GoogleDriveClient()
    result = client.list_audio_files()

    assert result == [{"id": "audio-1", "name": "call-1.mp3"}]
