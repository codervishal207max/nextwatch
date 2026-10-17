<div align="center">

# NextWatch

**A recommender for 30 to 60 minute films that learns from how you actually watch.**

Watch time, ratings, likes and feedback decide what you see next.

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)

[Live demo](#) · [Report a bug](../../issues)

</div>

<!-- Add 3-4 screenshots in a docs/ folder, then uncomment:
<p align="center">
  <img src="docs/login.png" width="48%" /> <img src="docs/home.png" width="48%" />
  <img src="docs/watch.png" width="48%" /> <img src="docs/admin.png" width="48%" />
</p>
-->

## Overview
Most movie apps work like this: search a title, get "similar" titles. NextWatch works differently. Every film runs **30 to 60 minutes**, so people actually finish them, and every session produces a signal: how much was watched, where the viewer dropped off, what they rated, whether they liked it and what they said afterwards. A model turns those signals into the next pick.

## Features
| | |
|---|---|
| **Watch tracking** | Records watch time, pauses, skips and drop-off point for every session |
| **Feedback loop** | Rating (1-10), like/dislike, quick tags (too slow, great ending, ...) and an optional comment after each film |
| **Personal picks** | Every unwatched 30-60 min film is scored for the user; new users get a popularity fallback |
| **Browse** | Movies with genre filter, Discover, and a My List that stays in sync across every page |
| **Auth** | Email + password (JWT), Google sign-in, complete logout that clears the session |
| **Profile** | Real per-user counts: watched, watchlist, ratings |
| **Admin dashboard** | Platform stats, per-user behaviour, and a comparison of recommendation strategies |
| **Catalog import** | Pulls 30-60 minute, embeddable, CC BY videos from YouTube, with clean descriptions and creator credit |

## How it works

### System architecture
```mermaid
flowchart LR
    subgraph Client["Browser"]
        UI["React 19 + Vite + Tailwind"]
        YT["Embedded YouTube player"]
    end
    subgraph Server["FastAPI backend"]
        AUTH["Auth: JWT and Google"]
        API["Catalog, tracking and watchlist APIs"]
        REC["Recommender service"]
        ADM["Admin API"]
    end
    DB[("PostgreSQL")]
    MODEL[["ml/artifacts/model.joblib"]]
    TRAIN["ml/train.py"]
    IMPORT["scripts/import_youtube.py"]
    YTAPI["YouTube Data API v3"]
    GOOGLE["Google Identity"]

    UI -->|"REST + JWT"| AUTH
    UI --> API
    UI --> ADM
    UI --- YT
    UI -->|"ID token"| GOOGLE
    AUTH --> DB
    API --> DB
    ADM --> DB
    REC --> DB
    REC --> MODEL
    TRAIN -->|"reads sessions"| DB
    TRAIN -->|"writes"| MODEL
    IMPORT --> YTAPI
    IMPORT -->|"30-60 min CC BY films"| DB
```

### The recommendation loop
```mermaid
flowchart TD
    A([User signs in]) --> B["Home: Your next film"]
    B --> C["Open a 30-60 min film"]
    C --> D["Watch in the embedded player"]
    D --> E["Every 15 s: watch time, pauses, skips, drop-off"]
    D --> F["After the film: rating, like or dislike, tags, comment"]
    E --> G[("watch_sessions")]
    F --> H[("ratings, reactions, feedback")]
    B -.-> I[("impressions: what was shown")]
    G --> J["Label: liked = 1, not liked = 0"]
    H --> J
    I --> J
    J --> K["As-of features: user history, film stats, genre affinity, runtime gap, context"]
    K --> L["Train: Logistic Regression, Random Forest if needed"]
    L --> M["Score unwatched 30-60 min films"]
    M --> N["Top-k picks"]
    N --> B
```

### One watch session
```mermaid
sequenceDiagram
    actor U as User
    participant W as React app
    participant A as FastAPI
    participant D as PostgreSQL
    U->>W: Open Home
    W->>A: GET /api/recommendations/next
    A->>D: Score candidates, log impressions
    A-->>W: Top picks with impression ids
    U->>W: Press Watch now
    W->>A: POST /api/sessions
    loop every 15 seconds while playing
        W->>A: PATCH /api/sessions/id (watched, furthest, pauses, skips)
    end
    U->>W: Rate, like, add tags
    W->>A: PUT rating and reaction, POST feedback
    A->>D: Store signals for the next training run
```

### Model selection
```mermaid
flowchart TD
    S([Time-based train, validation and test split]) --> LR["Logistic Regression"]
    LR --> V{"Validation ROC-AUC at least 0.80?"}
    V -->|Yes| KEEP["Keep Logistic Regression"]
    V -->|No| RF["Train Random Forest"]
    RF --> C{"Random Forest better by at least 0.01 AUC?"}
    C -->|Yes| USE["Use Random Forest"]
    C -->|No| KEEP
    KEEP --> T["Report on the test period against a popularity baseline"]
    USE --> T
```

**Labels:** 1 if rating ≥ 7, liked, or ≥ 80% watched. 0 if rating ≤ 4, disliked, or < 30% watched. Ambiguous cases are skipped.

**Features** (each computed only from events *before* the one being predicted, so no future data leaks in): user history (completion rate, average rating, preferred runtime, per-genre affinity), film stats (runtime, popularity, engagement, platform completion rate), user × film (genre affinity, runtime gap) and context (hour, weekday).

**Evaluation:** ROC-AUC, PR-AUC and Precision@3 against a popularity baseline. Accuracy alone misleads on imbalanced labels. Impressions are logged, so training also learns from films that were shown but ignored, and the admin page can compare the model against the popularity fallback.

## Tech stack
| Layer | Tools |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, React Router, axios |
| Backend | FastAPI, SQLAlchemy 2, PostgreSQL (SQLite for a quick local run), JWT, Google OAuth |
| ML | scikit-learn, pandas, NumPy, joblib |

## Project structure
```
NextWatch/
├── backend/
│   ├── app/
│   │   ├── api/routes/     auth, movies, search, tracking, recommendations, users, watchlist, admin
│   │   ├── core/           config, security (bcrypt, JWT)
│   │   ├── database/       engine and session
│   │   ├── models/         users, movies, ratings, watchlist, sessions, impressions, reactions, feedback
│   │   ├── schemas/        request and response models
│   │   └── services/       auth logic, recommender
│   ├── scripts/            import_youtube, add_youtube, yt (shared helpers)
│   ├── seed.py             demo catalog
│   └── tests/
├── frontend/src/
│   ├── pages/              Login, Home, Movies, MyList, Discover, MovieDetails, Watch, Profile, Settings, Admin
│   └── components/  hooks/  layout/  services/  utils/
└── ml/
    ├── simulate_data.py    simulated users and sessions
    ├── features.py         labels and as-of features
    ├── db_loader.py        builds training data from the database
    └── train.py            Logistic Regression, Random Forest fallback
```

## Getting started

**Requirements:** Python 3.11-3.13, Node.js 20+, PostgreSQL (optional, SQLite works for a first run).

### 1. Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
```
Edit `backend/.env` (see the table below), then:
```powershell
python seed.py                    # 60 demo films, or import the real catalog:
python -m scripts.import_youtube 3
python -m uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs

### 2. Frontend
```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```
Open http://localhost:5173, create an account and start watching.

### 3. Environment variables
| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | `sqlite:///./nextwatch.db` or `postgresql+psycopg2://user:password@localhost:5432/nextwatch` |
| `SECRET_KEY` | backend | JWT signing key. Use a long random string |
| `CORS_ORIGINS` | backend | Frontend URL, e.g. `http://localhost:5173` |
| `ADMIN_EMAILS` | backend | Comma-separated emails allowed to open `/admin` |
| `GOOGLE_CLIENT_ID` | backend | Google OAuth Web client ID (optional) |
| `YOUTUBE_API_KEY` | backend | Only for the catalog import scripts |
| `VITE_API_URL` | frontend | Backend URL, default `http://localhost:8000` |
| `VITE_GOOGLE_CLIENT_ID` | frontend | Same Google client ID |

> A password containing `@` must be written as `%40` inside `DATABASE_URL`. Never commit `.env`.

### 4. Optional setup
- **Google sign-in:** create a *Web application* OAuth client in Google Cloud Console, add your frontend URL under *Authorized JavaScript origins* (leave redirect URIs empty), add your Gmail as a test user, and put the client ID in both `.env` files.
- **YouTube catalog:** enable *YouTube Data API v3*, create an API key, restrict it to that API, set `YOUTUBE_API_KEY`.
- **Add one specific film:** `python -m scripts.add_youtube "https://youtu.be/XXXXXXXXXXX" Documentary` (must be 30-60 min, public, embeddable and CC BY).

## Training the model
```powershell
cd ml
python train.py               # simulated data: checks the whole pipeline
python train.py --source db   # real sessions collected by the platform
```
The backend loads `ml/artifacts/model.joblib` automatically and reloads it after retraining. Use `/admin` to see whether the model beats the popularity fallback on start rate and completion.

## API at a glance
Full interactive docs at `/docs`.

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `/login`, `/google` |
| Users | `GET /api/users/me`, `/api/users/me/stats` |
| Catalog | `GET /api/movies`, `/genres`, `/trending`, `/top-rated`, `/search`, `/{id}` |
| Watchlist | `GET /api/watchlist`, `POST` and `DELETE /api/watchlist/{movie_id}` |
| Tracking | `POST /api/sessions`, `PATCH /api/sessions/{id}`, `PUT /api/movies/{id}/rating`, `/reaction`, `POST /api/movies/{id}/feedback` |
| Recommendations | `GET /api/recommendations/next` |
| Admin | `GET /api/admin/overview`, `/users`, `/users/{id}`, `/recommendations` |

## Deployment
Suggested free-tier setup: PostgreSQL on Neon or Supabase, the backend on Render or Railway (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`), the frontend on Vercel or Netlify (`npm run build`, output `dist`, with a rewrite of all paths to `index.html` for React Router). Set the environment variables above, add the production frontend URL to `CORS_ORIGINS` and to Google's authorized origins, then import the catalog against the production database.

## Troubleshooting
| Symptom | Cause and fix |
|---|---|
| `Failed to build wheel for pydantic-core` or `psycopg2-binary` | Old pinned versions have no wheels for your Python. Use the current `requirements.txt`, recreate `.venv` with Python 3.11-3.13 |
| `No module named uvicorn` | The install failed. Fix it first, then run `python -m uvicorn app.main:app --reload` from `backend/` |
| Browser shows "blocked by CORS" on logged-in requests | Usually a hidden server error (500), not CORS. Check the backend terminal or DevTools → Network |
| `column ... does not exist` (PostgreSQL) | Tables were created by an older version. `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`, then seed again |
| `Connection refused` on port 5432 | PostgreSQL service is stopped. Start it from `services.msc` |
| Blank page after clicking something | A frontend runtime error. Open the console (F12), or wrap the routes in the included `ErrorBoundary` |
| `Failed to resolve import ...` | Wrong file name or folder (check spelling and capital letters), or run `npm install` |
| Google `origin_mismatch` | Add the exact frontend URL as an authorized JavaScript origin and wait a few minutes |
| `/admin` says no access | Add your login email to `ADMIN_EMAILS` and restart the backend |

## Status and limitations
- The model has so far been trained on **simulated data**. Those scores show the pipeline works, not how good recommendations are for real people. Real evaluation will be published after a beta with actual users.
- The catalog consists of CC BY videos on YouTube (short films and documentaries), not commercial releases. Videos can disappear if their owners delete them.
- Not built yet: Alembic migrations, Docker, CI, automatic retraining.

## Roadmap
- [ ] Beta with real users, retrain with `--source db`, publish honest metrics
- [ ] Alembic migrations, Docker, CI
- [ ] Cache features instead of recomputing them per request
- [ ] Gradient boosting or matrix factorization once there is enough data
- [ ] Scheduled retraining and model versioning

## Content and attribution
Videos are embedded from YouTube through its official player and used under their creators' Creative Commons (CC BY) licenses, or with the uploader's embedding permission. The creator's name is shown on each film page. NextWatch does not host or download any video.

## Author
**Vishal Fulbandhe** · [LinkedIn](https://www.linkedin.com/in/vishal-fulbandhe-16662832b/) · [GitHub](https://github.com/codervishal207max)
