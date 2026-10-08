from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.movie import Movie


def list_movies(
    db: Session, *, skip: int = 0, limit: int = 20, genre: Optional[str] = None
) -> Tuple[List[Movie], int]:
    query = db.query(Movie)
    if genre and genre.lower() != "all":
        query = query.filter(Movie.genres.ilike("%{}%".format(genre.strip())))
    return (
        query.order_by(Movie.popularity.desc(), Movie.rating.desc()).offset(skip).limit(limit).all(),
        query.count(),
    )


def get_movie(db: Session, movie_id: int) -> Optional[Movie]:
    return db.query(Movie).filter(Movie.id == movie_id).first()


def get_trending_movies(db: Session, limit: int = 12) -> List[Movie]:
    return db.query(Movie).order_by(Movie.popularity.desc(), Movie.rating.desc()).limit(limit).all()


def get_top_rated_movies(db: Session, limit: int = 12) -> List[Movie]:
    return db.query(Movie).order_by(Movie.rating.desc(), Movie.vote_count.desc()).limit(limit).all()


def search_movies(db: Session, query_text: str, limit: int = 20) -> List[Movie]:
    term = "%{}%".format(query_text.strip())
    return (
        db.query(Movie)
        .filter(or_(Movie.title.ilike(term), Movie.overview.ilike(term), Movie.genres.ilike(term)))
        .order_by(Movie.popularity.desc(), Movie.rating.desc())
        .limit(limit)
        .all()
    )


def get_genres(db: Session) -> List[str]:
    genre_values = db.query(Movie.genres).filter(Movie.genres.isnot(None)).all()
    return sorted({genre.strip() for value, in genre_values for genre in value.split(",") if genre.strip()})
