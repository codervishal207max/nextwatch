"""Demo catalog so the app runs offline. Real catalog: python scripts/import_tmdb.py

Run: python seed.py   (only fills an empty movies table)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml"))
from simulate_data import make_movies  # noqa: E402

from app.database.connection import Base, SessionLocal, engine  # noqa: E402
from app.models import Movie  # noqa: E402

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(Movie).count():
    print("Movies already exist, nothing to do.")
else:
    for m in make_movies(np.random.default_rng(1), 60).itertuples():
        db.add(Movie(title=f"Demo Film {m.movie_id:02d}", overview="Placeholder film for local development.",
                     genres=m.genres, runtime_minutes=m.runtime_minutes, year=m.year, rating=round(m.tmdb_rating, 1),
                     popularity=round(m.popularity, 1), vote_count=100))
    db.commit()
    print("Seeded 60 demo films (30-60 min). Use scripts/import_tmdb.py for real titles and posters.")
db.close()
