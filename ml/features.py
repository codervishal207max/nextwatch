"""Labels and features for the 'will this user like this film?' model.

Every feature is computed ONLY from interactions that happened before the row's
timestamp (as-of features). Using later data would leak the future and inflate scores.
"""
from collections import defaultdict

import numpy as np
import pandas as pd

from simulate_data import GENRES

REFERENCE_YEAR = 2026


def make_label(row):
    """1 = liked/finished, 0 = disliked/abandoned, None = ambiguous (excluded from training)."""
    r, rx, c = row["rating"], row["reaction"], row["completion_ratio"]
    if rx == -1 or (not np.isnan(r) and r <= 4):
        return 0
    if rx == 1 or (not np.isnan(r) and r >= 7):
        return 1
    if c >= 0.8:
        return 1
    if c < 0.3:
        return 0
    return None


def smooth(total, n, prior, weight):
    """Shrink small-sample averages toward a prior so 1 sample doesn't mean 100%."""
    return (total + prior * weight) / (n + weight)


def build_features(interactions: pd.DataFrame, movies: pd.DataFrame) -> pd.DataFrame:
    inter = interactions.sort_values("ts").reset_index(drop=True)
    inter["label"] = inter.apply(make_label, axis=1)
    mv = movies.set_index("movie_id")

    u = defaultdict(lambda: {"n": 0, "comp": 0.0, "pos": 0, "lab": 0, "rat": 0.0, "rat_n": 0,
                             "like": 0, "react_n": 0, "rt_sum": 0.0, "rt_n": 0})
    ug = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # user -> genre -> [positives, labelled]
    m = defaultdict(lambda: {"n": 0, "comp": 0.0, "pos": 0, "lab": 0})

    cand = inter["is_candidate"].tolist() if "is_candidate" in inter else [False] * len(inter)
    rows = []
    for i, r in enumerate(inter.itertuples(index=False)):
        movie = mv.loc[r.movie_id]
        genres = movie["genres"].split(",")
        us, ms = u[r.user_id], m[r.movie_id]

        pref_rt = us["rt_sum"] / us["rt_n"] if us["rt_n"] else 45.0
        aff = [smooth(ug[r.user_id][g][0], ug[r.user_id][g][1], 0.5, 2) for g in genres]

        feat = {
            "user_id": r.user_id, "movie_id": r.movie_id, "ts": r.ts, "label": r.label,
            # user history
            "user_n_prev": us["n"],
            "user_avg_completion": smooth(us["comp"], us["n"], 0.5, 3),
            "user_pos_rate": smooth(us["pos"], us["lab"], 0.5, 3),
            "user_avg_rating": smooth(us["rat"], us["rat_n"], 6.0, 2),
            "user_like_rate": smooth(us["like"], us["react_n"], 0.5, 2),
            "user_pref_runtime": pref_rt,
            # movie
            "runtime_minutes": movie["runtime_minutes"],
            "movie_age": REFERENCE_YEAR - movie["year"],
            "tmdb_rating": movie["tmdb_rating"],
            "popularity": movie["popularity"],
            "movie_n_prev": ms["n"],
            "movie_avg_completion": smooth(ms["comp"], ms["n"], 0.5, 5),
            "movie_pos_rate": smooth(ms["pos"], ms["lab"], 0.5, 5),
            # user x movie
            "runtime_gap": abs(movie["runtime_minutes"] - pref_rt),
            "genre_affinity_mean": float(np.mean(aff)),
            "genre_affinity_max": float(np.max(aff)),
            # context
            "hour": r.hour, "dow": r.dow,
        }
        for g in GENRES:
            feat[f"g_{g}"] = int(g in genres)
        rows.append(feat)
        if cand[i]:  # rows we only want to score must not change anyone's history
            continue

        # update history AFTER the row's features are fixed
        us["n"] += 1
        us["comp"] += r.completion_ratio
        if r.completion_ratio >= 0.8:
            us["rt_sum"] += movie["runtime_minutes"]
            us["rt_n"] += 1
        if not np.isnan(r.rating):
            us["rat"] += r.rating
            us["rat_n"] += 1
        if r.reaction != 0:
            us["react_n"] += 1
            us["like"] += int(r.reaction == 1)
        ms["n"] += 1
        ms["comp"] += r.completion_ratio
        if r.label is not None and not pd.isna(r.label):
            lab = int(r.label)
            us["lab"] += 1
            us["pos"] += lab
            ms["lab"] += 1
            ms["pos"] += lab
            for g in genres:
                ug[r.user_id][g][0] += lab
                ug[r.user_id][g][1] += 1

    return pd.DataFrame(rows)


FEATURES = (
    ["user_n_prev", "user_avg_completion", "user_pos_rate", "user_avg_rating", "user_like_rate",
     "user_pref_runtime", "runtime_minutes", "movie_age", "tmdb_rating", "popularity",
     "movie_n_prev", "movie_avg_completion", "movie_pos_rate", "runtime_gap",
     "genre_affinity_mean", "genre_affinity_max", "hour", "dow"]
    + [f"g_{g}" for g in GENRES]
)
