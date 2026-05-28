import io
from pathlib import Path
from typing import List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.config import GOOGLE_CREDS_FILE, GOOGLE_DRIVE_FOLDER_ID

SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveClient:
    def __init__(self):
        if not GOOGLE_DRIVE_FOLDER_ID:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID is not configured")

        creds = Credentials.from_service_account_file(
            GOOGLE_CREDS_FILE,
            scopes=SCOPES
        )

        self.service = build("drive", "v3", credentials=creds)

    def list_audio_files(self):
        return self._list_audio_files_in_folder(
            GOOGLE_DRIVE_FOLDER_ID
        )

    def _list_audio_files_in_folder(self, folder_id: str) -> List[dict]:
        query = (
            f"'{folder_id}' in parents and trashed = false"
        )

        results = (
            self.service.files()
            .list(
                q=query,
                fields="files(id, name, mimeType)"
            )
            .execute()
        )

        files = []

        for item in results.get("files", []):
            mime_type = item.get("mimeType", "")
            name = item.get("name", "")

            if mime_type == "application/vnd.google-apps.folder":
                files.extend(
                    self._list_audio_files_in_folder(
                        item["id"]
                    )
                )
                continue

            if name.lower().endswith(".mp3"):
                files.append(
                    {
                        "id": item["id"],
                        "name": name,
                    }
                )

        return files

    def download_file(self, file_id, filename):
        output_dir = Path("data/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / Path(filename).name

        if path.is_file():
            return str(path)

        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(path, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False

        while not done:
            _, done = downloader.next_chunk()

        return str(path)
