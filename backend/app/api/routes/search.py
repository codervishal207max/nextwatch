from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.movie import MovieOut
from app.services.movie_service import search_movies

router = APIRouter(prefix="/api/movies", tags=["Search"])


@router.get("/search", response_model=List[MovieOut], summary="Search the local movie catalog")
def search_catalog(
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[MovieOut]:
    return search_movies(db, q, limit)
