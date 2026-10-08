from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.watchlist import Watchlist
from app.models.movie import Movie
from app.schemas.movie import MovieOut
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])

@router.get("/", response_model=List[MovieOut])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    watchlist = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    movie_ids = [w.movie_id for w in watchlist]
    return db.query(Movie).filter(Movie.id.in_(movie_ids)).all()

@router.post("/{movie_id}", status_code=201)
def add_to_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.movie_id == movie_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Movie already in watchlist.")
    db.add(Watchlist(user_id=current_user.id, movie_id=movie_id))
    db.commit()
    return {"message": "Added to watchlist."}

@router.delete("/{movie_id}")
def remove_from_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.movie_id == movie_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Movie not in watchlist.")
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist."}
