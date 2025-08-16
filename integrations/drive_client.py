from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from kb import add_entry


def upload_file(path: str, parent: str, name: str, creds: Credentials = None):
    service = build("drive", "v3", credentials=creds)
    file_metadata = {"name": name, "parents": [parent]}
    media = MediaFileUpload(path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields="id,webViewLink,webContentLink").execute()
    add_entry(kind="drive_upload", file=file)
    return file.get("id")
