"""Add ONE specific YouTube video as a film.

Run from backend/:
  python -m scripts.add_youtube "https://youtu.be/XXXXXXXXXXX" Documentary
  python -m scripts.add_youtube XXXXXXXXXXX Drama --allow-standard

By default only CC BY videos are accepted. --allow-standard also accepts normal-license videos;
use it only for uploads by the rights holder (an official channel), never for pirated "full movie" uploads.
The video must be 30-60 minutes long, public and embeddable.
"""
import re
import sys

import httpx

from app.core.config import settings
from app.database.connection import Base, SessionLocal, engine
from app.models import Movie
from scripts.yt import movie_from_video

args = [a for a in sys.argv[1:] if not a.startswith("--")]
allow = "--allow-standard" in sys.argv
if not args:
    raise SystemExit(__doc__)
if not settings.youtube_api_key:
    raise SystemExit("Set YOUTUBE_API_KEY in backend/.env first.")

match = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", args[0]) or re.fullmatch(r"([A-Za-z0-9_-]{11})", args[0])
if not match:
    raise SystemExit("Could not find a YouTube video id in that link.")
video_id, genre = match.group(1), (args[1] if len(args) > 1 else "Drama")

res = httpx.get("https://www.googleapis.com/youtube/v3/videos", timeout=30, params={
    "key": settings.youtube_api_key, "id": video_id, "part": "snippet,contentDetails,statistics,status"})
res.raise_for_status()
items = res.json().get("items", [])
if not items:
    raise SystemExit("Video not found (private, deleted, or wrong id).")

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(Movie).filter_by(video_url=f"youtube:{video_id}").first():
    raise SystemExit("That video is already in the catalog.")
movie, reason = movie_from_video(items[0], genre, allow_standard=allow)
if not movie:
    raise SystemExit(f"Not added: {reason}.")
db.add(movie)
db.commit()
print(f"Added: {movie.title} ({movie.runtime_minutes} min, {genre})")