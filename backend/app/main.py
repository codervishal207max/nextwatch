from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, movies, recommendations, search, tracking, users, watchlist
from app.core.config import settings
from app.database.connection import Base, engine
import app.models  # noqa: F401  (registers every table)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NextWatch API",
    description="Movie recommendation system backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(movies.router)
app.include_router(recommendations.router)
app.include_router(watchlist.router)
app.include_router(tracking.router)
app.include_router(admin.router)


@app.get("/", tags=["System"])
def root() -> Dict[str, str]:
    return {"message": "NextWatch API is running"}


@app.api_route("/health", methods=["GET", "HEAD"], tags=["System"])
def health() -> Dict[str, str]:
    return {"status": "ok"}