"""Database session factory.

Spec: spec/product/02-architecture.md — Tech stack / SQLAlchemy 2.0 sync
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from zer0.config.settings import get_settings

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    """FastAPI / dependency-injection compatible session provider."""
    session: Session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def create_db_session():
    """Open a standalone synchronous session for non-FastAPI contexts.

    Use this in graph nodes, the CLI, and the scheduler.
    Commits on normal exit, rolls back on exception, always closes.
    """
    session: Session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
