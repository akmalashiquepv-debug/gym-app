# app/database.py
from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./database.db")

# SQLite specific connect args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def init_db() -> None:
    """
    Import models and create tables if missing.
    Safe to call multiple times.
    """
    import app.models  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """
    Yields a SQLModel Session for FastAPI dependencies.
    Usage: session: Session = Depends(get_session)
    """
    with Session(engine) as session:
        yield session
