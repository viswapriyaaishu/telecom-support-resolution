from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    settings = get_settings()

    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )

    connection = engine.connect()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        connection.close()
        engine.dispose()