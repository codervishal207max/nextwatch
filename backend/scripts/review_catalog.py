"""List every film in the catalog so you can check them, and flag ones that look adult or like clips.

Run from backend/:
    python -m scripts.review_catalog              all films
    python -m scripts.review_catalog --flagged    only the flagged ones
The FLAG is a guess from words in the title and description. Open the link of every film you are unsure about.
"""
import sys

from app.database.connection import SessionLocal
from app.models import Movie
from scripts.yt import looks_unsuitable

only_flagged = "--flagged" in sys.argv
db = SessionLocal()
films = db.query(Movie).order_by(Movie.id).all()
flagged = 0
for m in films:
    bad = looks_unsuitable(m.title, m.overview)
    flagged += bad
    if only_flagged and not bad:
        continue
    link = f"https://youtu.be/{m.video_url[8:]}" if (m.video_url or "").startswith("youtube:") else "-"
    print(f"{m.id:>4} {'FLAG' if bad else '    '} {str(m.runtime_minutes or '-'):>3} min  {(m.genres or '-'):<12} {m.title[:70]}")
    print(f"           {link}")
print(f"\n{len(films)} films, {flagged} flagged by words. The flag is only a guess, so open the links of the rest you doubt.")