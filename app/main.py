from app.drive import GoogleDriveClient
from app.transcriber import Transcriber
from app.analyzer import CallAnalyzer
from app.sheets import GoogleSheetsClient


def main():
    drive = GoogleDriveClient()
    sheets = GoogleSheetsClient()

    files = drive.list_audio_files()

    print(f"Found {len(files)} files")

    if not files:
        return

    transcriber = Transcriber()
    analyzer = CallAnalyzer()

    for file in files:
        try:
            print(f"Processing: {file['name']}")

            audio_path = drive.download_file(
                file["id"],
                file["name"]
            )

            transcript, _ = transcriber.transcribe(
                audio_path
            )

            analysis = analyzer.analyze(
                transcript
            )

            sheets.append_result(
                file["name"],
                analysis
            )

            print("Done")

        except Exception as e:
            print(
                f"Error processing {file['name']}: {e}"
            )


if __name__ == "__main__":
    main()
