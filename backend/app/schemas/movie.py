from pydantic import BaseModel, ConfigDict
from typing import Optional

class MovieOut(BaseModel):
    id: int
    tmdb_id: Optional[int]
    title: str
    overview: Optional[str]
    genres: Optional[str]
    runtime_minutes: Optional[int] = None
    language: Optional[str] = None
    video_url: Optional[str] = None
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    rating: Optional[float]
    vote_count: int
    year: Optional[int]
    popularity: float

    model_config = ConfigDict(from_attributes=True)
