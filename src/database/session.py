from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from config.settings import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


engine = create_engine(
    settings.POSTGRES_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
