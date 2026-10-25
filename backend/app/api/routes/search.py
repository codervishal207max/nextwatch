from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.movie import Movie
from app.schemas.movie import MovieOut

router = APIRouter(prefix="/api/movies", tags=["Search"])


def _like(word: str) -> str:
    word = word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{word}%"


@router.get("/search", response_model=List[MovieOut], summary="Find films by name (or genre)")
def search_movies(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(24, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Every word of the search must appear in the title or genre. Case does not matter."""
    words = q.strip().split()
    if not words:
        return []
    conditions = [
        or_(Movie.title.ilike(_like(w), escape="\\"), Movie.genres.ilike(_like(w), escape="\\"))
        for w in words
    ]
    rows = db.query(Movie).filter(and_(*conditions)).limit(300).all()
    phrase = q.strip().lower()

    def rank(movie):  # titles that start with the search first, then titles containing it, then genre matches
        title = (movie.title or "").lower()
        return 0 if title.startswith(phrase) else 1 if phrase in title else 2

    rows.sort(key=lambda m: (rank(m), -(m.popularity or 0)))
    return rows[:limit]