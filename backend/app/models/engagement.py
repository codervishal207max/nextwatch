"""Engagement tables: the raw signals the recommender learns from.

Save as backend/app/models/engagement.py and export from app/models/__init__.py.
Ratings already exist in app/models/rating.py (1-10) and are reused as-is.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, SmallInteger,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.connection import Base


class Impression(Base):
    """A film we showed a user in a recommendation slot.

    Without this table the model only ever sees films people chose to watch
    and can't learn from films that were shown and ignored.
    """

    __tablename__ = "impressions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False)
    shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # slot in the list, 0 = first
    surface: Mapped[str] = mapped_column(String(40), default="up_next", nullable=False)  # e.g. up_next, home_row
    model_version: Mapped[Optional[str]] = mapped_column(String(40))  # None = popularity fallback
    score: Mapped[Optional[float]] = mapped_column(Float)  # model's predicted probability at the time


class WatchSession(Base):
    """One playback of one film by one user."""

    __tablename__ = "watch_sessions"
    __table_args__ = (
        CheckConstraint("watched_seconds >= 0", name="ck_session_watched_nonneg"),
        CheckConstraint("completion_ratio >= 0 AND completion_ratio <= 1", name="ck_session_completion_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False)
    impression_id: Mapped[Optional[int]] = mapped_column(ForeignKey("impressions.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    runtime_seconds: Mapped[int] = mapped_column(Integer, nullable=False)  # snapshot of the film's length
    watched_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # time actually playing
    furthest_second: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # drop-off point
    completion_ratio: Mapped[float] = mapped_column(Float, default=0, nullable=False)  # min(watched / runtime, 1)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # completion_ratio >= 0.9
    pause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    seek_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # skips; many = bored
    device: Mapped[Optional[str]] = mapped_column(String(20))  # mobile, desktop, tv


class Reaction(Base):
    """Like (+1) or dislike (-1). One per user and film."""

    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_reaction_user_movie"),
        CheckConstraint("value IN (-1, 1)", name="ck_reaction_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False)
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Feedback(Base):
    """Post-watch feedback. Tags are structured so the model can use them; the comment is for humans."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("watch_sessions.id", ondelete="SET NULL"))
    tags: Mapped[Optional[str]] = mapped_column(String(200))  # e.g. "too_slow,great_ending,not_my_genre"
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
