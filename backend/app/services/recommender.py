"""Pick the next 30-60 minute films for a user.

Order of preference: hybrid model (TF-IDF + item-KNN + ALS, ml/artifacts/hybrid.joblib),
then the feature model (Logistic Regression / Random Forest, ml/artifacts/model.joblib),
then plain popularity. A problem in any model is logged and never breaks the Home page.
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.database.connection import engine
from app.models import Movie, User, WatchSession

log = logging.getLogger(__name__)

ML_DIR = Path(__file__).resolve().parents[3] / "ml"
MODEL_PATH = ML_DIR / "artifacts" / "model.joblib"
HYBRID_PATH = ML_DIR / "artifacts" / "hybrid.joblib"
MIN_RUNTIME, MAX_RUNTIME = 30, 60
_cache = {}


def _load(path: Path):
    """Load a trained model file, and reload it automatically after retraining."""
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    if _cache.get(path, (None, None))[0] != mtime:
        if str(ML_DIR) not in sys.path:
            sys.path.insert(0, str(ML_DIR))  # the pickled classes live in ml/
        _cache[path] = (mtime, joblib.load(path))
    return _cache[path][1]


def _hybrid_scores(model, user_id: int) -> Optional[dict]:
    from db_loader import load_interactions
    from recsys import platform_strength

    inter, _ = load_interactions(engine)
    mine = inter[inter["user_id"] == user_id]
    if mine.empty:
        return None
    mine = platform_strength(mine)
    history = {int(m): float(s) for m, s in zip(mine["movie_id"], mine["strength"])}
    if not any(s > 0 for s in history.values()):
        return None  # nothing liked yet: use the popularity fallback
    return dict(model.recommend(history, k=len(model.movie_ids)))


def _model_scores(bundle, user_id: int, cands: List[Movie]) -> Optional[dict]:
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
    return {int(mid): float(p) for mid, p in zip(feats["movie_id"], proba)}


def recommend(db: Session, user: User, k: int = 5) -> Tuple[str, List[Tuple[Movie, Optional[float]]]]:
    seen = [r[0] for r in db.query(WatchSession.movie_id).filter(WatchSession.user_id == user.id)]
    cands = db.query(Movie).filter(Movie.runtime_minutes.between(MIN_RUNTIME, MAX_RUNTIME), Movie.id.notin_(seen)).all()
    if not cands:
        return "none", []

    for name, path, scorer in (
        ("model:hybrid", HYBRID_PATH, lambda m: _hybrid_scores(m, user.id)),
        (None, MODEL_PATH, lambda b: _model_scores(b, user.id, cands)),
    ):
        try:
            bundle = _load(path)
            scores = scorer(bundle) if bundle is not None else None
        except Exception:
            log.exception("Scoring with %s failed, trying the next fallback", path.name)
            continue
        scored = [m for m in cands if scores and m.id in scores]
        if scored:
            ranked = sorted(scored, key=lambda m: -scores[m.id])[:k]
            return (name or f"model:{bundle['name']}"), [(m, scores[m.id]) for m in ranked]

    ranked = sorted(cands, key=lambda m: -(m.popularity or 0))[:k]
    return "popularity", [(m, None) for m in ranked]