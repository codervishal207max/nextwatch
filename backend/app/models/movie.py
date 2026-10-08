from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    overview: Mapped[Optional[str]] = mapped_column(Text)
    genres: Mapped[Optional[str]] = mapped_column(String(500))
    keywords: Mapped[Optional[str]] = mapped_column(Text)
    runtime_minutes: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    language: Mapped[Optional[str]] = mapped_column(String(20))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    poster_path: Mapped[Optional[str]] = mapped_column(String(500))
    backdrop_path: Mapped[Optional[str]] = mapped_column(String(500))
    rating: Mapped[Optional[float]] = mapped_column(Float)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    popularity: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    watchlist_items: Mapped[List["Watchlist"]] = relationship(back_populates="movie", cascade="all, delete-orphan")
    ratings: Mapped[List["Rating"]] = relationship(back_populates="movie", cascade="all, delete-orphan")
