from app.drive import GoogleDriveClient

client = GoogleDriveClient()

files = client.list_audio_files()

for file in files:
    print(file)
