import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def pg_db():
    """Session on a throwaway Postgres database (`gmit_test`), never the development data."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.db.base import Base
    import app.db.models  # noqa: F401  (registers every table on Base.metadata)

    url = make_url(settings.database_url)
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            if not conn.execute(text("select 1 from pg_database where datname='gmit_test'")).first():
                conn.execute(text("create database gmit_test"))
    except Exception as exc:
        pytest.skip(f"Postgres not reachable for DB tests: {exc}")
    finally:
        admin.dispose()

    engine = create_engine(url.set(database="gmit_test"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
