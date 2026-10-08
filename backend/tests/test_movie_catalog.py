from fastapi.testclient import TestClient

from app.database.connection import Base, SessionLocal, engine
from app.main import app
from app.models.movie import Movie


def seed_catalog() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add_all(
            [
                Movie(title="Orbit", year=2024, rating=8.9, popularity=98, genres="Sci-Fi,Drama", overview="An orbital rescue mission."),
                Movie(title="City Lights", year=2023, rating=7.8, popularity=85, genres="Drama,Romance", overview="A story set in the city."),
                Movie(title="Action Point", year=2022, rating=8.2, popularity=91, genres="Action,Sci-Fi", overview="A high-stakes mission."),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_movie_catalog_endpoints() -> None:
    seed_catalog()
    client = TestClient(app)

    trending = client.get("/api/movies/trending")
    top_rated = client.get("/api/movies/top-rated")
    genres = client.get("/api/movies/genres")
    filtered = client.get("/api/movies/?genre=Sci-Fi")
    search = client.get("/api/movies/search?q=orbit")

    assert trending.status_code == 200
    assert trending.json()[0]["title"] == "Orbit"
    assert top_rated.json()[0]["title"] == "Orbit"
    assert genres.json() == ["Action", "Drama", "Romance", "Sci-Fi"]
    assert {movie["title"] for movie in filtered.json()} == {"Orbit", "Action Point"}
    assert search.json()[0]["title"] == "Orbit"
    assert client.get("/api/movies/9999").status_code == 404
