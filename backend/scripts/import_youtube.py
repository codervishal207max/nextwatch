"""Import real, legally embeddable 30-60 minute videos from YouTube.

Only Creative Commons (CC BY) videos that the owner allows to be embedded are imported,
so the films are legal to show here. Attribution is stored in each film's overview.

Setup: Google Cloud Console -> enable "YouTube Data API v3" -> create an API key
       -> put YOUTUBE_API_KEY=... in backend/.env
Run (from backend/):  python -m scripts.import_youtube          (all genres)
                      python -m scripts.import_youtube 3        (pages per genre, default 2)
"""
import math
import re
import sys

import httpx

from app.core.config import settings
from app.database.connection import Base, SessionLocal, engine
from app.models import Movie

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
SKIP_CATEGORIES = {"10", "20"}  # music, gaming
DURATION = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")

if not settings.youtube_api_key:
    raise SystemExit("Set YOUTUBE_API_KEY in backend/.env first.")


def seconds(iso: str) -> int:
    h, m, s = (int(x or 0) for x in DURATION.fullmatch(iso).groups())
    return h * 3600 + m * 60 + s


def best_thumb(thumbs: dict) -> str:
    for key in ("maxres", "standard", "high", "medium", "default"):
        if key in thumbs:
            return thumbs[key]["url"]
    return ""


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
                    secs = seconds(v["contentDetails"]["duration"])
                    sn, st, stat = v["snippet"], v["status"], v.get("statistics", {})
                    if not 1800 <= secs <= 3600 or not st.get("embeddable") or st.get("privacyStatus") != "public":
                        continue
                    if sn.get("categoryId") in SKIP_CATEGORIES:
                        continue
                    url = f"youtube:{v['id']}"
                    if db.query(Movie).filter_by(video_url=url).first():
                        continue
                    views, likes = int(stat.get("viewCount", 0)), int(stat.get("likeCount", 0))
                    thumb = best_thumb(sn.get("thumbnails", {}))
                    db.add(Movie(
                        title=sn["title"][:250],
                        overview=f"{sn.get('description', '')[:600].strip()}\n\nBy {sn['channelTitle']} on YouTube (CC BY).",
                        genres=genre, runtime_minutes=round(secs / 60), year=int(sn["publishedAt"][:4]),
                        language=sn.get("defaultAudioLanguage") or sn.get("defaultLanguage"),
                        poster_path=thumb, backdrop_path=thumb, video_url=url, vote_count=likes,
                        popularity=round(min(100.0, math.log10(views + 1) * 14), 1),
                        # simple engagement score (likes per view), not a critic rating
                        rating=round(5 + 5 * min(1.0, (likes / views) * 20), 1) if views else 6.5,
                    ))
                    added += 1
                db.commit()
            if not token:
                break
        print(f"{genre}: done")
print(f"Imported {added} videos.")