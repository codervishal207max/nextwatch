from typing import List

from pydantic import BaseModel

from app.schemas.movie import MovieOut


class RecommendationResponse(BaseModel):
    movies: List[MovieOut]
    strategy: str
