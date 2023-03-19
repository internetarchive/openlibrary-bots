from collections.abc import Iterator

import pytest

import olclient
from main import EditionCoverData
from requests_mock.mocker import Mocker as RequestsMock
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(scope="session")
def get_db() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    db_session = Session(engine)

    # Add an ISBN as already seeded into the database.
    db_session.bulk_save_objects([EditionCoverData(isbn_13="111", cover_exists=True)])
    db_session.commit()

    yield db_session


@pytest.fixture()
def get_ol(requests_mock: RequestsMock) -> Iterator[OpenLibrary]:
    requests_mock.post(
        "https://openlibrary.org/account/login",
        cookies={
            "session": "/people/testbot%2C2023-01-20T02%3A26%3A33%2C4819b%246atest;Path=/"
        },
    )
    yield olclient.OpenLibrary(
        credentials=olclient.config.Credentials(access="access_key", secret="secret_key")
    )
