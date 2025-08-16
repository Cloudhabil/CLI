import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials


def ensure_token(client_id: str, client_secret: str, scopes: list, token_path: Path):
    token_path.parent.mkdir(parents=True, exist_ok=True)
    if token_path.exists():
        return Credentials.from_authorized_user_file(token_path, scopes)
    flow = InstalledAppFlow.from_client_config(
        {"installed": {"client_id": client_id, "client_secret": client_secret, "redirect_uris": [
            "urn:ietf:wg:oauth:2.0:oob", "http://localhost"], "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes,
    )
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json())
    return creds


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(".env.local")
    ensure_token(
        os.environ["GOOGLE_CLIENT_ID"],
        os.environ["GOOGLE_CLIENT_SECRET"],
        os.environ["GOOGLE_SCOPES"].split(","),
        Path(os.environ["GOOGLE_TOKEN_PATH"]),
    )
