from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# check_same_thread only applies to SQLite; other drivers (e.g. psycopg) reject the kwarg.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def create_db_and_tables() -> None:
	SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
	with Session(engine) as session:
		yield session
