"""Benchmark the hybrid recommender on MovieLens 100K: real ratings from real people, free and public.

1. Download https://files.grouplens.org/datasets/movielens/ml-100k.zip
2. Unzip it so that this folder exists:  ml/data/ml-100k/  (with u.data, u.item, u.genre inside)
3. Run:  cd ml && python benchmark_movielens.py            (or --path some/other/folder)

Rating 4 or 5 = liked (5 counts double), rating 1 or 2 = disliked, 3 is ignored.
"""
import argparse
from pathlib import Path

import pandas as pd

from recsys import run_auc_experiment, run_experiment


def load(path):
    path = Path(path)
    ratings = pd.read_csv(path / "u.data", sep="\t", names=["user_id", "movie_id", "rating", "ts"])
    genre_names = pd.read_csv(path / "u.genre", sep="|", names=["genre", "idx"], encoding="latin-1").dropna()["genre"].tolist()
    items = pd.read_csv(path / "u.item", sep="|", names=["movie_id", "title", "release", "video", "url"] + genre_names,
                        encoding="latin-1")
    items["genres"] = items[genre_names].apply(
        lambda row: ",".join(g for g in genre_names if row[g] == 1 and g != "unknown"), axis=1)
    movies = items[["movie_id", "title", "genres"]]

    r = ratings["rating"]
    strength = pd.Series(float("nan"), index=ratings.index)
    strength[r >= 4] = (r[r >= 4] - 3).astype(float)   # 4 -> 1, 5 -> 2
    strength[r <= 2] = -1.0
    inter = ratings.assign(strength=strength).dropna(subset=["strength"])[["user_id", "movie_id", "ts", "strength"]]
    return inter, movies


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=str(Path(__file__).parent / "data" / "ml-100k"))
    args = ap.parse_args()
    if not (Path(args.path) / "u.data").exists():
        raise SystemExit(f"MovieLens files not found in {args.path}. See the instructions at the top of this file.")
    inter, movies = load(args.path)
    print(f"{len(inter)} usable ratings, {inter.user_id.nunique()} users, {len(movies)} films")
    run_auc_experiment(inter, movies, label="MovieLens-100K")
    run_experiment(inter, movies, label="MovieLens-100K (full-catalogue ranking)")


if __name__ == "__main__":
    main()