"""Benchmark and train the hybrid recommender (TF-IDF + item-KNN + ALS).

Run:  python train_hybrid.py              simulated data: prints the benchmark table only
      python train_hybrid.py --source db  real platform data: benchmark, then save artifacts/hybrid.joblib
Simulated films share ids with real ones, so a simulated model is NEVER saved for the website.
"""
import argparse
import os
from pathlib import Path

import joblib
import pandas as pd

from recsys import HybridRecommender, platform_strength, run_auc_experiment, run_experiment
from simulate_data import simulate

ARTIFACTS = Path(__file__).parent / "artifacts"


def load(source):
    if source == "db":
        from sqlalchemy import create_engine
        from db_loader import load_interactions
        url = os.getenv("DATABASE_URL", f"sqlite:///{Path(__file__).parent.parent / 'backend' / 'nextwatch.db'}")
        engine = create_engine(url)
        inter, _ = load_interactions(engine)
        movies = pd.read_sql("SELECT id AS movie_id, title, overview, genres FROM movies", engine)
        return inter, movies
    inter, movies = simulate()
    return inter, movies


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sim", "db"], default="sim")
    ap.add_argument("--force", action="store_true", help="save an untuned model even if there is too little data to evaluate")
    args = ap.parse_args()

    inter, movies = load(args.source)
    if inter.empty:
        raise SystemExit("No watch sessions found yet.")
    inter = platform_strength(inter)
    print(f"{len(inter)} usable interactions from {inter.user_id.nunique()} users "
          f"({(inter.strength > 0).mean():.0%} liked)")

    weights = None
    try:
        # Test 1: among films people actually watched, can the blend tell liked from disliked?
        _, weights = run_auc_experiment(inter, movies, label=f"{args.source} data")
        # Test 2: harder, rank the one held-out liked film among EVERY film the user has not seen
        run_experiment(inter, movies, label=f"{args.source} data (full-catalogue ranking)")
    except SystemExit as err:
        print(err)
        if not args.force:
            raise SystemExit("Not enough data yet. Use --force to save an untuned model anyway.")

    if args.source != "db":
        print("\nSimulated data: nothing saved (these results only prove the pipeline works).")
        return
    model = HybridRecommender().fit(inter, movies)
    if weights:
        model.weights = weights
    ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump(model, ARTIFACTS / "hybrid.joblib")
    print(f"\nsaved -> {ARTIFACTS / 'hybrid.joblib'}  weights: {model.weights}")


if __name__ == "__main__":
    main()