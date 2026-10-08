"""Pick the next 30-60 minute films for a user: trained model if available, popularity otherwise."""
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.database.connection import engine
from app.models import Movie, User, WatchSession

ML_DIR = Path(__file__).resolve().parents[3] / "ml"
MODEL_PATH = ML_DIR / "artifacts" / "model.joblib"
MIN_RUNTIME, MAX_RUNTIME = 30, 60
_cache = {"mtime": None, "bundle": None}


def _bundle():
    if not MODEL_PATH.exists():
        return None
    mtime = MODEL_PATH.stat().st_mtime
    if _cache["mtime"] != mtime:  # reload automatically after retraining
        _cache.update(mtime=mtime, bundle=joblib.load(MODEL_PATH))
    return _cache["bundle"]


def _model_scores(bundle, user_id: int, cands: List[Movie]) -> Optional[dict]:
    if str(ML_DIR) not in sys.path:
        sys.path.insert(0, str(ML_DIR))
    from db_loader import load_interactions
    from features import build_features

    inter, movies = load_interactions(engine)
    if inter.empty or user_id not in set(inter["user_id"]):
        return None  # cold start: this user has no history yet
    now = pd.Timestamp.now("UTC").tz_localize(None)
    rows = pd.DataFrame({"user_id": user_id, "movie_id": [m.id for m in cands], "ts": now, "completion_ratio": 0.0,
                         "rating": float("nan"), "reaction": 0, "hour": now.hour, "dow": now.dayofweek, "is_candidate": True})
    inter["is_candidate"] = False
    feats = build_features(pd.concat([inter, rows], ignore_index=True), movies)
    feats = feats[(feats["user_id"] == user_id) & (feats["ts"] == now)]
    proba = bundle["model"].predict_proba(feats[bundle["features"]])[:, 1]
    return dict(zip(feats["movie_id"], proba))


def recommend(db: Session, user: User, k: int = 5) -> Tuple[str, List[Tuple[Movie, Optional[float]]]]:
    seen = [r[0] for r in db.query(WatchSession.movie_id).filter(WatchSession.user_id == user.id)]
    cands = db.query(Movie).filter(Movie.runtime_minutes.between(MIN_RUNTIME, MAX_RUNTIME), Movie.id.notin_(seen)).all()
    if not cands:
        return "none", []
    bundle = _bundle()
    scores = _model_scores(bundle, user.id, cands) if bundle else None
    if scores:
        ranked = sorted(cands, key=lambda m: -scores[m.id])[:k]
        return f"model:{bundle['name']}", [(m, float(scores[m.id])) for m in ranked]
    ranked = sorted(cands, key=lambda m: -(m.popularity or 0))[:k]
    return "popularity", [(m, None) for m in ranked]
