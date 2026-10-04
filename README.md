# NextWatch

A recommender for **30 to 60 minute films**. Instead of "search a movie, get similar movies", NextWatch learns from how you actually watch: how much of a film you finish, what you rate it, whether you like it, and what you tell us afterwards. That decides the next film it picks for you.


## Features
- **Watch tracking:** the player records watch time, pauses, skips and drop-off point per session.
- **Post-watch feedback:** rating (1-10), like/dislike, quick tags (too slow, great ending, ...) and an optional comment.
- **Personal recommendations:** every unwatched 30-60 min film is scored for the user; the top picks appear on Home. New users get a popularity fallback.
- **Auth:** email + password (JWT) and Google sign-in.
- **Admin dashboard:** platform stats, per-user behaviour, and a comparison of recommendation strategies (does the model beat popularity?).
- **TMDB import:** pulls 30-60 minute films with posters and metadata.

## How the recommendation works
```
watch session + rating + like + feedback
        -> label per (user, film): liked / not liked
        -> as-of features (no future data leaks in)
        -> Logistic Regression  -- good enough? --yes--> serve it
                                    |no
                                    v
                               Random Forest (kept only if clearly better)
        -> score unwatched 30-60 min films -> top-k -> Home
```
- **Label:** 1 if rating >= 7, liked, or >= 80% watched; 0 if rating <= 4, disliked, or < 30% watched. Ambiguous cases are skipped.
- **Features:** user history (completion rate, average rating, preferred runtime, per-genre affinity), film stats (runtime, TMDB rating, popularity, platform completion rate), user x film (genre affinity, runtime gap) and context (hour, weekday).
- **Evaluation:** time-based train/validation/test split, compared against a popularity baseline using ROC-AUC, PR-AUC and Precision@3 (accuracy alone misleads on imbalanced labels).
- **Impressions are logged**, so training can learn from films that were shown but ignored, and the admin page can compare strategies.

## Tech stack
| Layer | Tools |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, React Router |
| Backend | FastAPI, SQLAlchemy 2, PostgreSQL (SQLite for local dev), JWT, Google OAuth |
| ML | scikit-learn, pandas, NumPy, joblib |

## Project structure
```
backend/    FastAPI app: auth, catalog, tracking, recommendations, admin
frontend/   React app: login, home, details, watch + feedback, admin
ml/         features.py, train.py, simulate_data.py, db_loader.py
```

## Getting started

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # fill in the values below
python seed.py                                        # demo films, or: python scripts/import_tmdb.py
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Open http://localhost:5173.

**Environment variables**

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | e.g. `postgresql+psycopg2://user:password@localhost:5432/nextwatch` |
| `SECRET_KEY` | backend | JWT signing key (use a long random string) |
| `GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID` | backend / frontend | Google sign-in (same Web client ID; origin `http://localhost:5173`) |
| `TMDB_API_KEY` | backend | only for `scripts/import_tmdb.py` |
| `ADMIN_EMAILS` | backend | comma-separated emails allowed to open `/admin` |
| `VITE_API_URL` | frontend | backend URL, default `http://localhost:8000` |

**Train the model**
```bash
cd ml
python train.py               # simulated data: checks the pipeline end to end
python train.py --source db   # real sessions collected by the platform
```
The backend picks up `ml/artifacts/model.joblib` automatically after retraining.

## API at a glance
Interactive docs at http://localhost:8000/docs.

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `/login`, `/google` |
| Catalog | `GET /api/movies`, `/trending`, `/top-rated`, `/search`, `/{id}` |
| Tracking | `POST /api/sessions`, `PATCH /api/sessions/{id}`, `PUT /api/movies/{id}/rating`, `/reaction`, `POST /api/movies/{id}/feedback` |
| Recommendations | `GET /api/recommendations/next` |
| Admin | `GET /api/admin/overview`, `/users`, `/users/{id}`, `/recommendations` |

## Status and limitations
- The model has so far been trained on **simulated data**. Those scores show the pipeline works, not how good recommendations are for real people. Real evaluation will be added after a beta with actual users.
- TMDB provides metadata and posters, not video. Attach a playable file in `movies.video_url` to watch a film.
- Not built yet: My List and Profile pages wired to the API, Alembic migrations, Docker, CI.

## Roadmap
- [ ] Beta with real users, retrain with `--source db`, publish honest metrics
- [ ] Alembic migrations and Docker setup
- [ ] Cache features instead of recomputing per request
- [ ] Stronger models (gradient boosting, matrix factorization) if data supports it
- [ ] Wire My List, Profile and Search pages to the API

## Attribution
This product uses the TMDB API but is not endorsed or certified by TMDB.

## Author
Vishal Fulbandhe · [LinkedIn](https://www.linkedin.com/in/your-handle) · [GitHub](https://github.com/your-handle)
