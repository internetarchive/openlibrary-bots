import logging
import pathlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import main
import pytest
from main import EditionCoverData, update_cover_for_edition, verify_and_update_cover
from olclient import OpenLibrary
from requests_mock.mocker import Mocker as RequestsMock
from sqlmodel import Session, select
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget

test_path = pathlib.Path(__file__).parent.resolve()
test_isbns_zip = test_path / "test_isbns.zip"


def test_update_cover_for_edition_completes_successfully(
    requests_mock: RequestsMock, get_ol: OpenLibrary
) -> bool | None:
    """Check that correct data is POSTed to the backend."""
    m = requests_mock
    olid = "OL1234M"
    mime_type = "image/jpeg"
    file_name = "1234567890123.jpg"
    cover_data = Path(f"{test_path}/{file_name}").read_bytes()
    ol = get_ol

    m.post(f"https://openlibrary.org/books/{olid}/-/add-cover", text="Totally Saved!")

    is_success = update_cover_for_edition(olid, file_name, cover_data, mime_type, ol)

    # Use the request header and body from the mocker's request history.
    # Index zero is sending the key, so look at index 1.
    history = m.request_history[1]
    headers: dict[str, str] = history.headers
    body: bytes = history.body

    # Use Streaming multipart/form-data parser to parse the form data.
    # Skip "url" and "upload" as they're not necessary to POST the cover.
    file = ValueTarget()
    headers = {"Content-Type": headers.get("Content-Type", "")}
    assert headers != ""
    parser = StreamingFormDataParser(headers=headers)
    parser.register("file", file)

    # Iterate through the request body based on the boundary between items.
    for chunk in BytesIO(body):
        parser.data_received(chunk)

    assert file_name == file.multipart_filename
    assert mime_type == file.multipart_content_type
    assert (
        file.value
        == b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc0\x00\x0b\x08\x00 \x00 \x01\x01\x11\x00\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xaa`\x00\x00\x00?\xff\xd9"
    )
    assert is_success is True

    return None


def test_update_cover_for_edition_reports_failure(
    requests_mock: RequestsMock, get_ol: OpenLibrary
) -> bool | None:
    """Fail because the response doesn't have the success text."""
    m = requests_mock
    olid = "OL1234M"
    mime_type = "image/jpeg"
    file_name = "1234567890123.jpg"
    cover_data = b"image data"
    ol = get_ol

    m.post(f"https://openlibrary.org/books/{olid}/-/add-cover", text="Fail")

    is_success = update_cover_for_edition(olid, file_name, cover_data, mime_type, ol)

    assert is_success is False

    return None


@dataclass
class ISBN:
    text: str
    id: str
    exp: list[tuple[EditionCoverData]]
    saved_text: str
    cover_exists_in_ol: bool
    is_success: bool
    warning: str
    err: Any


# Test cases for test_verify_and_update_cover()
test_cases = [
    ISBN(
        text="ISBN already seeded into DB. No check of saved_text. Ensure no duplication.",
        id="111",
        exp=[(EditionCoverData(isbn_13="111", cover_exists=True),)],
        saved_text="",
        cover_exists_in_ol=False,
        is_success=False,
        warning="cover exists in dump for 111",
        err=None,
    ),
    ISBN(
        text="Failed save message from the BACK END.",
        id="222",
        exp=[(EditionCoverData(isbn_13="222", cover_exists=False),)],
        saved_text="Fail",
        cover_exists_in_ol=False,
        is_success=False,
        warning="",
        err=None,
    ),
    ISBN(
        text="Successfully added cover.",
        id="333",
        exp=[(EditionCoverData(isbn_13="333", cover_exists=True),)],
        saved_text="Saved!",
        cover_exists_in_ol=False,
        is_success=True,
        warning="",
        err=None,
    ),
    ISBN(
        text="Cover already in OL.",
        id="444",
        exp=[(EditionCoverData(isbn_13="444", cover_exists=True),)],
        saved_text="",
        cover_exists_in_ol=True,
        is_success=False,
        warning="cover exists in OL for 444",
        err=None,
    ),
]


@pytest.mark.parametrize("tc,exp", [(tc, tc.exp) for tc in test_cases])
def test_verify_and_update_cover(
    requests_mock: RequestsMock, get_db: Session, get_ol: OpenLibrary, tc, exp, caplog
) -> None:
    """See the "text" field in test_cases for an explanation of each test case."""

    caplog.set_level(logging.INFO)
    m = requests_mock
    archive_contents = ZipFile(test_isbns_zip, "r")

    # Override scope rather than refactoring.
    ol = get_ol
    main.db_session = get_db

    db_session = main.db_session  # For consistency/clarity.

    bibkey = {
        f"ISBN:{tc.id}": {
            "bib_key": f"ISBN:{tc.id}",
            "info_url": f"https://openlibrary.org/books/OL{tc.id}M/Test_Book",
        }
    }
    edition_response = {"olid": f"OL{tc.id}M", "covers": tc.cover_exists_in_ol}
    m.get(f"https://openlibrary.org/api/books.json?bibkeys=ISBN:{tc.id}", json=bibkey)
    m.get(f"https://openlibrary.org/books/OL{tc.id}M.json", json=edition_response)
    m.post(
        f"https://openlibrary.org/books/OL{tc.id}M/-/add-cover", text=f"{tc.saved_text}"
    )

    is_success = verify_and_update_cover(
        isbn_13=tc.id, archive_contents=archive_contents, ol=ol
    )

    # Check command output and logged statements.
    assert is_success == tc.is_success
    assert f"{tc.warning}" in caplog.text

    # Finally, ensure the database looks as expected for each test case.
    statement = select(EditionCoverData).where(EditionCoverData.isbn_13 == tc.id)
    res = db_session.execute(statement).fetchall()
    assert res == exp
