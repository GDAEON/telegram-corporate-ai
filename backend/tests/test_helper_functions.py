import re
from backend.services.helper_functions import (
    guess_filename,
    generate_uuid,
    generate_message_id,
    extract_telegram_attachments,
)


def test_guess_filename_content_disposition():
    headers = {"Content-Disposition": 'attachment; filename="test.txt"'}
    assert guess_filename("http://example.com/file", headers) == "test.txt"


def test_guess_filename_from_url():
    assert guess_filename("http://example.com/path/img.jpg", {}) == "img.jpg"


def test_generate_uuid_unique():
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    pattern = re.compile(r"^[a-f0-9-]{36}$")
    assert uuid1 != uuid2
    assert pattern.match(uuid1)
    assert pattern.match(uuid2)


def test_generate_message_id_numeric_and_unique():
    mid1 = generate_message_id()
    mid2 = generate_message_id()
    assert mid1 != mid2
    assert mid1.isdigit()
    assert mid2.isdigit()

