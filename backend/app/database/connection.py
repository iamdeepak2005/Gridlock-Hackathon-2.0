"""
SQLAlchemy database connection and session management.
Uses synchronous engine for compatibility with ML training workflows.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Create engine - use SQLite fallback for easy hackathon setup
def get_engine():
    """Create database engine with appropriate settings."""
    db_url = settings.DATABASE_URL

    if db_url.startswith("sqlite"):
        return create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        return create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )


engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on startup."""
    Base.metadata.create_all(bind=engine)
