"""Remove films from the catalog, and never import them again.

Run from backend/ (the .venv must be active):
    python -m scripts.remove_movies 12 15 33            preview of removing films with these ids
    python -m scripts.remove_movies 12 15 33 --yes      do it
    python -m scripts.remove_movies --flagged           preview: every film the word check flags
    python -m scripts.remove_movies --flagged --yes     do it
Find the ids with:  python -m scripts.review_catalog

A removed film also loses its ratings, likes, feedback, watch history and My List entries.
Its YouTube id is written to backend/blocked_videos.txt so the import scripts never add it back.
"""
import sys

from app.database.connection import SessionLocal
from app.models import Feedback, Impression, Movie, Rating, Reaction, Watchlist, WatchSession
from scripts.yt import add_to_blocklist, looks_unsuitable

ids = {int(a) for a in sys.argv[1:] if a.isdigit()}
by_flag = "--flagged" in sys.argv
if not ids and not by_flag:
    raise SystemExit(__doc__)

db = SessionLocal()
targets = [m for m in db.query(Movie).order_by(Movie.id).all()
           if m.id in ids or (by_flag and looks_unsuitable(m.title, m.overview))]
missing = ids - {m.id for m in targets}
if missing:
    print(f"No film with id: {sorted(missing)}")
if not targets:
    raise SystemExit("Nothing to remove.")

print(f"{len(targets)} films selected:")
for m in targets:
    print(f"  {m.id:>4}  {m.title[:80]}")
if "--yes" not in sys.argv:
    raise SystemExit("\nPreview only. Run again with --yes to remove them.")

target_ids = [m.id for m in targets]
for model in (Feedback, Reaction, Rating, Watchlist, WatchSession, Impression):
    db.query(model).filter(model.movie_id.in_(target_ids)).delete(synchronize_session=False)
db.query(Movie).filter(Movie.id.in_(target_ids)).delete(synchronize_session=False)
db.commit()
add_to_blocklist(m.video_url[8:] for m in targets if (m.video_url or "").startswith("youtube:"))
print(f"\nRemoved {len(target_ids)} films. {db.query(Movie).count()} films are left.")