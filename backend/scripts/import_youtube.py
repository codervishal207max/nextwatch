"""Import real, legally embeddable 30-60 minute videos from YouTube (CC BY only).

Setup: Google Cloud -> enable "YouTube Data API v3" -> create API key -> YOUTUBE_API_KEY=... in backend/.env
Run (from backend/):  python -m scripts.import_youtube        (2 pages per genre)
                      python -m scripts.import_youtube 4
"""
import sys

import httpx

from app.core.config import settings
from app.database.connection import Base, SessionLocal, engine
from app.models import Movie
from scripts.yt import movie_from_video

API = "https://www.googleapis.com/youtube/v3"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 2
# (genre label, search text, YouTube category id or None)
GENRES = [
    ("Drama", "drama short film", "1"),
    ("Thriller", "thriller short film", "1"),
    ("Sci-Fi", "science fiction short film", "1"),
    ("Comedy", "comedy short film", "23"),
    ("Horror", "horror short film", "1"),
    ("Documentary", "documentary", None),
]

if not settings.youtube_api_key:
    raise SystemExit("Set YOUTUBE_API_KEY in backend/.env first.")

Base.metadata.create_all(bind=engine)
db, added = SessionLocal(), 0
with httpx.Client(params={"key": settings.youtube_api_key}, timeout=30) as http:
    for genre, query, category in GENRES:
        token = None
        for _ in range(PAGES):
            params = {"part": "snippet", "type": "video", "q": query, "maxResults": 50, "order": "viewCount",
                      "videoDuration": "long", "videoEmbeddable": "true", "videoLicense": "creativeCommon"}
            if category:
                params["videoCategoryId"] = category
            if token:
                params["pageToken"] = token
            res = http.get(f"{API}/search", params=params)
            res.raise_for_status()
            data = res.json()
            ids = [i["id"]["videoId"] for i in data.get("items", [])]
            token = data.get("nextPageToken")
            if ids:
                details = http.get(f"{API}/videos", params={"part": "snippet,contentDetails,statistics,status",
                                                            "id": ",".join(ids)}).json().get("items", [])
                for v in details:
                    if db.query(Movie).filter_by(video_url=f"youtube:{v['id']}").first():
                        continue
                    movie, _ = movie_from_video(v, genre)
                    if movie:
                        db.add(movie)
                        added += 1
                db.commit()
            if not token:
                break
        print(f"{genre}: done")
print(f"Imported {added} videos.")