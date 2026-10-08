"""Backward-compatible database imports.

New code should import from :mod:`app.database.connection`.
"""

from app.database.connection import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
