"""Simulated NextWatch data (30-60 min films).

THIS IS NOT REAL USER DATA. It exists so the pipeline can be built and tested
before the platform has users. Hidden "taste" variables generate the behaviour,
so model scores here only show the pipeline works, not how it will do in production.
Replace with an export of watch_sessions / ratings / reactions once real data exists.
"""
import numpy as np
import pandas as pd

GENRES = ["Drama", "Comedy", "Thriller", "Sci-Fi", "Romance", "Crime", "Documentary", "Animation"]


def make_movies(rng, n=300):
    rows = []
    for i in range(n):
        genres = rng.choice(GENRES, size=rng.integers(1, 4), replace=False)
        quality = rng.normal(0, 1)
        rows.append({
            "movie_id": i + 1,
            "runtime_minutes": int(rng.integers(30, 61)),
            "year": int(rng.integers(1995, 2026)),
            "genres": ",".join(genres),
            "tmdb_rating": float(np.clip(6.5 + 0.7 * quality + rng.normal(0, 0.4), 3, 9.5)),
            "popularity": float(np.clip(40 + 8 * quality + rng.normal(0, 20), 1, 100)),
            "_quality": quality,  # hidden, dropped before saving
        })
    return pd.DataFrame(rows)


def simulate(n_users=400, n_movies=300, days=120, seed=7):
    rng = np.random.default_rng(seed)
    movies = make_movies(rng, n_movies)
    genre_sets = [set(g.split(",")) for g in movies["genres"]]
    pop_w = movies["popularity"].to_numpy() / movies["popularity"].sum()
    start = pd.Timestamp("2026-01-01")
    rows = []

    for uid in range(1, n_users + 1):
        taste = dict(zip(GENRES, rng.dirichlet(np.ones(len(GENRES)) * 0.4)))
        pref_runtime = float(np.clip(rng.normal(46, 7), 32, 58))
        rating_bias = rng.normal(0, 0.6)
        n_watch = int(rng.integers(25, 60))
        seen = set()
        times = np.sort(rng.uniform(0, days * 24 * 60, n_watch))  # minutes since start

        for t in times:
            # exposure is skewed to popular films, like a real homepage
            idx = int(rng.choice(len(movies), p=pop_w))
            if idx in seen:
                continue
            seen.add(idx)
            m = movies.iloc[idx]
            aff = np.mean([taste[g] for g in genre_sets[idx]])
            logit = (
                6.0 * (aff - 1 / len(GENRES)) * 3
                + 0.6 * m["_quality"]
                - 0.08 * abs(m["runtime_minutes"] - pref_runtime)
                + rng.normal(0, 0.8)
            )
            p = 1 / (1 + np.exp(-logit))
            engaged = rng.random() < p
            completion = rng.beta(8, 1.5) if engaged else rng.beta(1.2, 5)
            if rng.random() < 0.08:  # real behaviour is noisy: finished but didn't love it, etc.
                completion = rng.beta(8, 1.5) if not engaged else rng.beta(1.2, 5)

            rating = np.nan
            if rng.random() < 0.5:
                rating = int(np.clip(round(2 + 8 * p + rating_bias + rng.normal(0, 1.2)), 1, 10))
            reaction = 0
            if rng.random() < 0.35:
                noisy = p + rng.normal(0, 0.12)
                reaction = 1 if noisy > 0.6 else (-1 if noisy < 0.3 else 0)

            ts = start + pd.Timedelta(minutes=float(t))
            rows.append({
                "user_id": uid, "movie_id": int(m["movie_id"]), "ts": ts,
                "completion_ratio": float(np.clip(completion, 0, 1)),
                "rating": rating, "reaction": reaction,
                "hour": ts.hour, "dow": ts.dayofweek,
            })

    interactions = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    return interactions, movies.drop(columns=["_quality"])


if __name__ == "__main__":
    inter, mov = simulate()
    print(len(inter), "interactions,", inter.user_id.nunique(), "users,", len(mov), "movies")
