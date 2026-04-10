from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os


def get_engine(database_url: str | None = None):
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./cawncade.db")
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    engine = create_engine(url, connect_args=connect_args, echo=False)
    return engine


def init_db(engine=None):
    """Create all tables. Call once at startup."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


def get_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Default engine and session for convenience
_engine = None
_SessionLocal = None


def get_db():
    """FastAPI dependency: yields a database session."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = get_engine()
        _SessionLocal = get_session_factory(_engine)
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
