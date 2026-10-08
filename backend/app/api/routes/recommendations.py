from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models import Impression, User
from app.schemas.engagement import NextResponse, RecommendedMovie
from app.schemas.movie import MovieOut
from app.services.recommender import recommend

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.get("/next", response_model=NextResponse, summary="Next 30-60 minute films for the signed-in user")
def next_up(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    strategy, ranked = recommend(db, user, limit)
    items = []
    for position, (movie, score) in enumerate(ranked):
        impression = Impression(user_id=user.id, movie_id=movie.id, position=position, surface="up_next",
                                model_version=strategy, score=score)
        db.add(impression)
        db.flush()
        items.append(RecommendedMovie(movie=MovieOut.model_validate(movie), score=score, impression_id=impression.id))
    db.commit()
    return NextResponse(strategy=strategy, items=items)
