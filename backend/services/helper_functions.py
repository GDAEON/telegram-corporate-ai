from urllib.parse import urlparse
import uuid
import os
import re

def guess_filename(file_url: str, headers: dict) -> str:
    disposition = headers.get("Content-Disposition", "")
    match = re.search(r'filename="?([^";]+)"?', disposition)
    if match:
        return match.group(1)

    parsed = urlparse(file_url)
    name = os.path.basename(parsed.path)
    return name or "file"

def generate_uuid():
    return str(uuid.uuid4())
