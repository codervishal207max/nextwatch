"""Endpoints that collect the signals the recommender learns from."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models import Feedback, Movie, Rating, Reaction, User, WatchSession
from app.schemas.engagement import FeedbackIn, RatingIn, ReactionIn, SessionOut, SessionStart, SessionUpdate

router = APIRouter(prefix="/api", tags=["Tracking"])


def _movie_or_404(db: Session, movie_id: int) -> Movie:
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found.")
    return movie


@router.post("/sessions", response_model=SessionOut, status_code=201, summary="Start watching a film")
def start_session(data: SessionStart, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    movie = _movie_or_404(db, data.movie_id)
    if not movie.runtime_minutes:
        raise HTTPException(422, "This film has no runtime set.")
    session = WatchSession(user_id=user.id, movie_id=movie.id, impression_id=data.impression_id,
                           device=data.device, runtime_seconds=movie.runtime_minutes * 60)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/sessions/{session_id}", response_model=SessionOut, summary="Heartbeat / end of a watch session")
def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.get(WatchSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "Session not found.")
    session.watched_seconds = max(session.watched_seconds, min(data.watched_seconds, session.runtime_seconds))
    session.furthest_second = max(session.furthest_second, min(data.furthest_second, session.runtime_seconds))
    session.pause_count = max(session.pause_count, data.pause_count)
    session.seek_count = max(session.seek_count, data.seek_count)
    session.completion_ratio = min(session.watched_seconds / session.runtime_seconds, 1.0)
    session.completed = session.completion_ratio >= 0.9
    if data.ended:
        session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


@router.put("/movies/{movie_id}/rating", summary="Rate a film 1-10 (replaces any earlier rating)")
def rate_movie(movie_id: int, data: RatingIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _movie_or_404(db, movie_id)
    row = db.query(Rating).filter_by(user_id=user.id, movie_id=movie_id).first()
    if row:
        row.rating = data.rating
    else:
        db.add(Rating(user_id=user.id, movie_id=movie_id, rating=data.rating))
    db.commit()
    return {"rating": data.rating}


@router.put("/movies/{movie_id}/reaction", summary="Like (1) or dislike (-1)")
def react(movie_id: int, data: ReactionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.value not in (-1, 1):
        raise HTTPException(422, "value must be 1 or -1.")
    _movie_or_404(db, movie_id)
    row = db.query(Reaction).filter_by(user_id=user.id, movie_id=movie_id).first()
    if row:
        row.value = data.value
    else:
        db.add(Reaction(user_id=user.id, movie_id=movie_id, value=data.value))
    db.commit()
    return {"value": data.value}


@router.post("/movies/{movie_id}/feedback", status_code=201, summary="Post-watch feedback tags and comment")
def send_feedback(movie_id: int, data: FeedbackIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _movie_or_404(db, movie_id)
    db.add(Feedback(user_id=user.id, movie_id=movie_id, session_id=data.session_id,
                    tags=",".join(t.strip() for t in data.tags if t.strip())[:200] or None, comment=data.comment))
    db.commit()
    return {"message": "Thanks for the feedback."}
