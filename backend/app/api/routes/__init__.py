"""HTTP route modules grouped by resource."""

from app.api.routes import auth, movies, recommendations, search, tracking, users, watchlist

__all__ = ["auth", "movies", "recommendations", "search", "tracking", "users", "watchlist"]
