from app.database.connection import Base
from app.models import Movie, Rating, User, Watchlist  # noqa: F401


def test_core_recommendation_tables_are_registered() -> None:
    assert {"users", "movies", "ratings", "watchlist"}.issubset(Base.metadata.tables)
