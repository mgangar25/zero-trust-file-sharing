"""
Database setup for SQLAlchemy.

SQLAlchemy lets Python code work with database tables using classes and objects.
The actual database for this project will be Supabase PostgreSQL.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings


def build_engine_options(database_url: str) -> dict:
    """
    Build SQLAlchemy engine options for the selected database.

    The real app uses Supabase PostgreSQL. Tests use SQLite so they can run
    locally without real secrets or network services. SQLite needs
    check_same_thread=False because FastAPI's TestClient may run request handling
    in a different thread from the test itself.
    """
    if database_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "pool_pre_ping": True,
        }

    return {"pool_pre_ping": True}


# The engine manages the connection pool to PostgreSQL.
# pool_pre_ping=True checks that a connection is still alive before using it,
# which helps avoid stale database connections in deployed environments.
engine = create_engine(settings.DATABASE_URL, **build_engine_options(settings.DATABASE_URL))


# SessionLocal is a factory for database sessions.
# Each request should get its own session, use it, and then close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base is the parent class for all SQLAlchemy models.
# Every table model in models.py inherits from this Base.
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session to routes.

    The `yield` gives the session to the route. After the request finishes, the
    `finally` block closes the session so connections are not leaked.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_database_tables() -> None:
    """
    Create database tables from the SQLAlchemy models.

    This is convenient for early development because the app can create the
    starter tables automatically in Supabase PostgreSQL.
    Later, a production project should use Alembic migrations instead. Migrations
    give you versioned, reviewable database changes as the schema evolves.
    """
    # Importing models here registers every model class with Base.metadata.
    # The import is intentionally inside the function to avoid circular imports
    # while database.py is still loading.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    apply_development_schema_adjustments()


def apply_development_schema_adjustments() -> None:
    """
    Apply tiny compatibility fixes for this early development phase.

    SQLAlchemy's create_all() creates missing tables, but it does not modify
    columns on tables that already exist. The first backend checkpoint created
    encryption_nonce and encrypted_file_key as required columns. This checkpoint
    intentionally stores file metadata before encryption exists, so those two
    columns must allow NULL.

    Later, Alembic migrations should replace this kind of startup adjustment.
    For now, these PostgreSQL ALTER statements make local/Supabase development
    smoother without exposing or printing any secrets.
    """
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE files ALTER COLUMN encryption_nonce DROP NOT NULL")
        )
        connection.execute(
            text("ALTER TABLE files ALTER COLUMN encrypted_file_key DROP NOT NULL")
        )
