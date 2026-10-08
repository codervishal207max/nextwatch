from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.movie import MovieOut
from app.services.movie_service import (
    get_genres,
    get_movie,
    get_top_rated_movies,
    get_trending_movies,
    list_movies,
)

router = APIRouter(prefix="/api/movies", tags=["Movies"])


@router.get("/", response_model=List[MovieOut], summary="List movies with optional genre filtering")
def get_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    genre: Optional[str] = Query(None, max_length=80),
    db: Session = Depends(get_db),
) -> List[MovieOut]:
    movies, _ = list_movies(db, skip=skip, limit=limit, genre=genre)
    return movies


@router.get("/trending", response_model=List[MovieOut], summary="Get the most popular movies")
def get_trending(limit: int = Query(12, ge=1, le=50), db: Session = Depends(get_db)) -> List[MovieOut]:
    return get_trending_movies(db, limit)


@router.get("/top-rated", response_model=List[MovieOut], summary="Get the highest rated movies")
def get_top_rated(limit: int = Query(12, ge=1, le=50), db: Session = Depends(get_db)) -> List[MovieOut]:
    return get_top_rated_movies(db, limit)


@router.get("/genres", response_model=List[str], summary="List available movie genres")
def list_genres(db: Session = Depends(get_db)) -> List[str]:
    return get_genres(db)


@router.get("/{movie_id}", response_model=MovieOut, summary="Get movie details")
def get_movie_details(movie_id: int, db: Session = Depends(get_db)) -> MovieOut:
    movie = get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return movie
