"""Turn the platform's tables into the (interactions, movies) frames the features expect."""
import pandas as pd

COLS = ["user_id", "movie_id", "ts", "completion_ratio", "rating", "reaction", "hour", "dow"]


def load_interactions(engine):
    sessions = pd.read_sql("SELECT user_id, movie_id, started_at, completion_ratio FROM watch_sessions", engine)
    ratings = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", engine)
    reactions = pd.read_sql("SELECT user_id, movie_id, value AS reaction FROM reactions", engine)
    movies = pd.read_sql("SELECT id AS movie_id, runtime_minutes, year, genres, rating AS tmdb_rating, popularity FROM movies", engine)
    movies = movies.fillna({"runtime_minutes": 45, "year": 2000, "genres": "", "tmdb_rating": 6.5, "popularity": 0})
    if sessions.empty:
        return pd.DataFrame(columns=COLS), movies

    sessions["started_at"] = pd.to_datetime(sessions["started_at"], utc=True).dt.tz_localize(None)
    inter = sessions.groupby(["user_id", "movie_id"], as_index=False).agg(
        ts=("started_at", "min"), completion_ratio=("completion_ratio", "max"))
    inter = inter.merge(ratings, how="left", on=["user_id", "movie_id"]).merge(reactions, how="left", on=["user_id", "movie_id"])
    inter["rating"] = inter["rating"].astype(float)
    inter["reaction"] = inter["reaction"].fillna(0).astype(int)
    inter["hour"], inter["dow"] = inter["ts"].dt.hour, inter["ts"].dt.dayofweek
    return inter.sort_values("ts").reset_index(drop=True)[COLS], movies
