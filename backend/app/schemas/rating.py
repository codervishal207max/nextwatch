from datetime import datetime

from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    movie_id: int
    rating: int = Field(ge=1, le=10)


class RatingOut(RatingCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
