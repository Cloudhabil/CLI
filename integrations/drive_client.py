import os
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .google_oauth import ensure_token
from kb import add_entry


def upload_file(path: str, parent_id: str):
    service = build('drive', 'v3', credentials=ensure_token())
    file_metadata = {'name': Path(path).name, 'parents': [parent_id]}
    media = MediaFileUpload(path)
    file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
    add_entry('drive_upload', path, file['id'])
    return file
