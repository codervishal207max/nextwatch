from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.movie import MovieOut


class SessionStart(BaseModel):
    movie_id: int
    impression_id: Optional[int] = None
    device: Optional[str] = Field(default=None, max_length=20)


class SessionUpdate(BaseModel):
    watched_seconds: int = Field(ge=0)
    furthest_second: int = Field(ge=0)
    pause_count: int = Field(default=0, ge=0)
    seek_count: int = Field(default=0, ge=0)
    ended: bool = False


class SessionOut(BaseModel):
    id: int
    completion_ratio: float
    completed: bool
    model_config = {"from_attributes": True}


class RatingIn(BaseModel):
    rating: int = Field(ge=1, le=10)


class ReactionIn(BaseModel):
    value: int = Field(description="1 = like, -1 = dislike")


class FeedbackIn(BaseModel):
    session_id: Optional[int] = None
    tags: List[str] = []
    comment: Optional[str] = Field(default=None, max_length=1000)


class RecommendedMovie(BaseModel):
    movie: MovieOut
    score: Optional[float] = None
    impression_id: int


class NextResponse(BaseModel):
    strategy: str
    items: List[RecommendedMovie]
