from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models import Rating, Reaction, User, Watchlist, WatchSession
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserOut, summary="Get the authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/stats", summary="Counts shown on the profile page (only this user's data)")
def my_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid = current_user.id
    return {
        "watched": db.scalar(select(func.count(func.distinct(WatchSession.movie_id))).where(WatchSession.user_id == uid)),
        "watch_minutes": round((db.scalar(select(func.coalesce(func.sum(WatchSession.watched_seconds), 0)).where(WatchSession.user_id == uid)) or 0) / 60),
        "watchlist": db.scalar(select(func.count(Watchlist.id)).where(Watchlist.user_id == uid)),
        "ratings": db.scalar(select(func.count(Rating.id)).where(Rating.user_id == uid)),
        "likes": db.scalar(select(func.count(Reaction.id)).where(Reaction.user_id == uid, Reaction.value == 1)),
    }