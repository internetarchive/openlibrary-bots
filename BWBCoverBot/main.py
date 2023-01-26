#!/usr/bin/env python

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from zipfile import ZipFile, ZipInfo

from olclient import OpenLibrary, config
from sqlmodel import Field, Session, SQLModel, create_engine, select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[logging.FileHandler("bwb-cover-bot-debug.log"), logging.StreamHandler()],
)


def get_ol() -> OpenLibrary:
    return OpenLibrary(
        credentials=config.Credentials(
            access=os.environ["OL_ACCESS_KEY"], secret=os.environ["OL_SECRET_KEY"]
        )
    )


class EditionCoverData(SQLModel, table=True):
    isbn_13: str = Field(default=None, primary_key=True)
    cover_exists: bool = Field(default=False)


engine = create_engine("sqlite:///bwb-cover-bot.sqlite", echo=False)
SQLModel.metadata.create_all(engine)
db_session = Session(engine)


def update_cover_for_edition(
    edition_olid: str,
    file_name: str,
    cover_data: bytes,
    mime_type: str,
    ol: OpenLibrary,
) -> bool:
    form_data_body = {
        "file": (file_name, cover_data, mime_type),
        "url": (None, "https://"),
        "upload": (None, "Submit"),
    }
    resp = ol.session.post(
        f"https://openlibrary.org/books/{edition_olid}/-/add-cover",
        files=form_data_body,
    )
    is_update_success: bool = resp.ok and "Saved!" in resp.text
    return is_update_success


def is_cover_already_stored(isbn_13: str) -> bool:
    statement = select(EditionCoverData).where(EditionCoverData.isbn_13 == isbn_13)
    edition_cover_data = db_session.execute(statement).first()
    return (
        len(edition_cover_data or []) == 1
        and edition_cover_data[0].cover_exists is True
    )


def verify_and_update_cover(
    isbn_13: str, archive_contents: ZipFile, ol: OpenLibrary
) -> bool:
    if is_cover_already_stored(isbn_13):
        logging.info(f"cover exists in dump for {isbn_13}")
        return False

    ol_edition = ol.Edition.get(isbn=isbn_13)
    if not ol_edition:
        return False

    edition_olid = ol_edition.olid
    cover_exists = getattr(ol_edition, "covers", None)
    if cover_exists:
        db_session.bulk_save_objects(
            [EditionCoverData(isbn_13=isbn_13, cover_exists=True)]
        )
        db_session.commit()
        logging.info(f"cover exists in OL for {isbn_13}")
        return False

    is_success = update_cover_for_edition(
        edition_olid=edition_olid,
        cover_data=archive_contents.read(f"{isbn_13}.jpg"),
        file_name=f"{isbn_13}.jpg",
        mime_type="image/jpeg",
        ol=ol,
    )

    db_session.bulk_save_objects(
        [EditionCoverData(isbn_13=isbn_13, cover_exists=is_success)]
    )
    db_session.commit()
    logging.info(f"cover update status {is_success} for {isbn_13}")

    return is_success


def parser_for_zip_with_isbns(cover_zip_path: str, ol: OpenLibrary) -> int:
    logging.info(f"start time: {datetime.now().timestamp()} for {cover_zip_path}")
    archive_contents = ZipFile(cover_zip_path, "r")
    file_list: list[ZipInfo] = archive_contents.filelist

    verified_and_updated_count = 0
    processed_file_list = []
    for file in file_list:
        logging.info(
            f"processing {file.filename}, processed {len(processed_file_list)} files"
        )
        try:
            isbn_of_file: str = file.filename.split(".")[0]
            is_success = verify_and_update_cover(isbn_of_file, archive_contents, ol)
            if is_success:
                verified_and_updated_count += 1
            processed_file_list.append(processed_file_list)
        except Exception as e:
            logging.error(
                f"file: {file.filename}, zip path: {cover_zip_path}. Error: {e}"
            )

    logging.info(f"end time: {datetime.now().timestamp()} for {cover_zip_path}")
    return verified_and_updated_count


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        raise Exception("python main.py <zip path>")

    ol = get_ol()

    user_provided_path = args[1]
    zip_paths = (
        [
            os.path.join(user_provided_path, f)
            for f in os.listdir(user_provided_path)
            if f.endswith(".zip")
        ]
        if os.path.isdir(user_provided_path)
        else [user_provided_path]
    )
    for zip_path in zip_paths:
        logging.info(f"Processing: {zip_path}")
        verified_and_updated_count = parser_for_zip_with_isbns(zip_path, ol)
        logging.info(f"Verified and updated {verified_and_updated_count} ISBNs")
