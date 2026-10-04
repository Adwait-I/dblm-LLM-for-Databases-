"""
database/connection.py
----------------------
SQLAlchemy engine creation and session management.
Two engines are maintained:
  - `engine`          — read/write (used for schema introspection)
  - `readonly_engine` — read-only user (used to execute user queries)
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# Engine creation
# ------------------------------------------------------------------ #

def _make_engine(url: str, pool_size: int = 5, label: str = "default"):
    """Create a SQLAlchemy engine with sensible defaults."""
    engine = create_engine(
        url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # recycle connections every 30 minutes
        pool_pre_ping=True,  # verify connection is alive before using it
        echo=False,
    )
    logger.info("Database engine created", extra={"engine": label})
    return engine


# Primary engine (admin / schema introspection)
engine = _make_engine(settings.database_url, pool_size=5, label="primary")

# Read-only engine (user query execution)
readonly_engine = _make_engine(
    settings.database_readonly_url, pool_size=10, label="readonly"
)

# Session factories
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
ReadOnlySessionLocal = sessionmaker(
    bind=readonly_engine, autoflush=False, autocommit=False
)


# ------------------------------------------------------------------ #
# Context managers
# ------------------------------------------------------------------ #

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Yield a primary DB session; always roll back on error and close."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_readonly_session() -> Generator[Session, None, None]:
    """Yield a read-only DB session; roll back and close on any error."""
    session: Session = ReadOnlySessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ------------------------------------------------------------------ #
# Health check
# ------------------------------------------------------------------ #

def check_database_connectivity() -> dict:
    """
    Attempt a lightweight query against both engines.
    Returns a dict with status and version info.
    """
    result = {
        "primary": {"status": "unknown", "version": None},
        "readonly": {"status": "unknown", "version": None},
    }

    for label, eng in [("primary", engine), ("readonly", readonly_engine)]:
        try:
            with eng.connect() as conn:
                row = conn.execute(text("SELECT version()")).fetchone()
                result[label]["status"] = "connected"
                result[label]["version"] = row[0] if row else None
        except Exception as exc:
            result[label]["status"] = "error"
            result[label]["error"] = str(exc)
            logger.error(
                "Database connectivity check failed",
                extra={"engine": label, "error": str(exc)},
            )

    return result
