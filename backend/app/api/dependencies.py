"""Shared FastAPI dependencies.

The existing ``deps`` module remains available for backward compatibility.
"""

from app.api.deps import get_current_user, oauth2_scheme
from app.database.connection import get_db

__all__ = ["get_current_user", "get_db", "oauth2_scheme"]
