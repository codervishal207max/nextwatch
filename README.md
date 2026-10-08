# NextWatch

A recommender for 30 to 60 minute films. Users open a film; how long they watch, their rating, like and feedback decide the next film we pick.

```
backend/   FastAPI + SQLAlchemy (auth, catalog, tracking, recommendations)
frontend/  React 19 + Vite + Tailwind v4 (login, home, details, watch + feedback)
ml/        Feature engineering, training (Logistic Regression, Random Forest fallback)
```

## Run it
```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY
python seed.py                # 60 demo films (30-60 min); or: python scripts/import_tmdb.py
uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend && cp .env.example .env && npm install && npm run dev
```
Google sign-in (optional): create a Web OAuth Client ID, set `GOOGLE_CLIENT_ID` in `backend/.env` and `VITE_GOOGLE_CLIENT_ID` in `frontend/.env`, and add `http://localhost:5173` as an authorized JavaScript origin.

Open http://localhost:5173, create an account, watch a film. Attach a playable file in `movies.video_url` first (TMDB gives posters and metadata, not videos).

## How the recommendation works
1. `GET /api/recommendations/next` scores every unwatched 30-60 min film for the user and logs what it showed (`impressions`).
2. The player sends heartbeats (`PATCH /api/sessions/{id}`); the end screen sends rating, like and feedback.
3. Label per (user, film): 1 = rating >= 7, like, or >= 80% watched; 0 = rating <= 4, dislike, or < 30% watched. Ambiguous rows are skipped.
4. Features are computed only from data before each event (no future leakage): user history, film stats, genre affinity, runtime gap, time of day.
5. `ml/train.py` trains Logistic Regression first; if validation AUC is below 0.80 it also trains a Random Forest and keeps it only if it is clearly better. Compared with a popularity baseline on a time-based test split.
6. New users, or no trained model: popularity among 30-60 min films.

```bash
cd ml
python train.py               # simulated data: checks the pipeline end to end
python train.py --source db   # real sessions from the platform (use this once users exist)
```

## Status (read before showing this to anyone)
- The model has only been trained on **simulated** data. Its scores prove the pipeline runs, not that recommendations are good. Retrain with `--source db` after real usage and report those numbers.
- Not built yet: My List / Profile / Search pages wired to the API, Alembic migrations, Docker.
- After pulling new columns into an old dev database, delete `nextwatch.db` and re-seed, or add a migration.
