"""Import 30-60 minute films (with posters) from TMDB.

Needs TMDB_API_KEY in backend/.env. Run from backend/:  python scripts/import_tmdb.py [pages]
TMDB does not supply full videos, so video_url stays empty until you attach one.
"""
import sys

import httpx

from app.core.config import settings
from app.database.connection import Base, SessionLocal, engine
from app.models import Movie

API = "https://api.themoviedb.org/3"
pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3

if not settings.tmdb_api_key:
    raise SystemExit("Set TMDB_API_KEY in backend/.env first.")

Base.metadata.create_all(bind=engine)
db, added = SessionLocal(), 0
with httpx.Client(params={"api_key": settings.tmdb_api_key}, timeout=20) as http:
    for page in range(1, pages + 1):
        found = http.get(f"{API}/discover/movie", params={"with_runtime.gte": 30, "with_runtime.lte": 60,
                         "sort_by": "popularity.desc", "vote_count.gte": 5, "page": page}).json().get("results", [])
        for item in found:
            if db.query(Movie).filter_by(tmdb_id=item["id"]).first():
                continue
            d = http.get(f"{API}/movie/{item['id']}").json()
            if not d.get("runtime") or not 30 <= d["runtime"] <= 60:
                continue
            db.add(Movie(tmdb_id=d["id"], title=d["title"], overview=d.get("overview"),
                         genres=",".join(g["name"] for g in d.get("genres", [])), runtime_minutes=d["runtime"],
                         language=d.get("original_language"), poster_path=d.get("poster_path"),
                         backdrop_path=d.get("backdrop_path"), rating=d.get("vote_average"),
                         vote_count=d.get("vote_count", 0), popularity=d.get("popularity", 0),
                         year=int(d["release_date"][:4]) if d.get("release_date") else None))
            added += 1
        db.commit()
print(f"Imported {added} films.")
