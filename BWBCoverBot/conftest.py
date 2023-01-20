import pytest
from requests_mock.mocker import Mocker as RequestsMock
from sqlmodel import SQLModel, create_engine, Session
from olclient import OpenLibrary, config
from main import EditionCoverData


@pytest.fixture(scope="session")
def get_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    db_session = Session(engine)

    # Add ISBN an ISBN as already seeded into the database.
    db_session.bulk_save_objects(
        [EditionCoverData(isbn_13="123", cover_exists=True)]
    )
    db_session.commit()

    yield db_session


@pytest.fixture()
def get_ol(requests_mock: RequestsMock):
    requests_mock.post("https://openlibrary.org/account/login", cookies={"session": "/people/testbot%2C2023-01-20T02%3A26%3A33%2C4819b%246atest;Path=/"})
    yield OpenLibrary(credentials=config.Credentials(access="access_key", secret="secret_key"))
