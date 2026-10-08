from fastapi.testclient import TestClient

from app.database.connection import Base, SessionLocal, engine
from app.main import app
from app.models import Movie


def setup_client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all([Movie(title="Short A", runtime_minutes=40, genres="Drama", popularity=90, year=2020, rating=8),
                Movie(title="Short B", runtime_minutes=50, genres="Comedy", popularity=70, year=2021, rating=7),
                Movie(title="Feature", runtime_minutes=140, genres="Drama", popularity=99, year=2019, rating=9)])
    db.commit()
    db.close()
    client = TestClient(app)
    user = {"name": "Test User", "email": "t@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user)
    token = client.post("/api/auth/login", json={"email": user["email"], "password": user["password"]}).json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}


def test_watch_rate_react_feedback_and_next():
    client, h = setup_client()

    nxt = client.get("/api/recommendations/next", headers=h).json()
    titles = [i["movie"]["title"] for i in nxt["items"]]
    assert nxt["strategy"] == "popularity" and titles == ["Short A", "Short B"]  # 140-min film excluded

    first = nxt["items"][0]
    s = client.post("/api/sessions", json={"movie_id": first["movie"]["id"], "impression_id": first["impression_id"]}, headers=h)
    assert s.status_code == 201
    done = client.patch(f"/api/sessions/{s.json()['id']}", json={"watched_seconds": 2300, "furthest_second": 2400, "ended": True}, headers=h)
    assert done.json()["completed"] is True

    movie_id = first["movie"]["id"]
    assert client.put(f"/api/movies/{movie_id}/rating", json={"rating": 9}, headers=h).status_code == 200
    assert client.put(f"/api/movies/{movie_id}/reaction", json={"value": 1}, headers=h).status_code == 200
    assert client.put(f"/api/movies/{movie_id}/reaction", json={"value": 5}, headers=h).status_code == 422
    assert client.post(f"/api/movies/{movie_id}/feedback", json={"tags": ["great_ending"]}, headers=h).status_code == 201

    after = [i["movie"]["title"] for i in client.get("/api/recommendations/next", headers=h).json()["items"]]
    assert after == ["Short B"]  # already watched films are not recommended again
