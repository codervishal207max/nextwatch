"""Read-only admin API: see how every user behaves. Only emails listed in ADMIN_EMAILS may call it."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database.connection import get_db
from app.models import Feedback, Impression, LoginEvent, Movie, Rating, Reaction, User, WatchSession

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


def _num(x, digits=2):
    return round(float(x), digits) if x is not None else None


def _iso(d):
    return d.isoformat() if hasattr(d, "isoformat") else (str(d) if d else None)


@router.get("/overview", summary="Platform-wide numbers")
def overview(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    week = now - timedelta(days=7)
    users = db.scalar(select(func.count(User.id)))
    new_7d = db.scalar(select(func.count(User.id)).where(User.created_at >= week))
    active_7d = db.scalar(select(func.count(func.distinct(WatchSession.user_id))).where(WatchSession.started_at >= week))
    sessions, watched, avg_completion, completed = db.execute(select(
        func.count(WatchSession.id), func.coalesce(func.sum(WatchSession.watched_seconds), 0),
        func.avg(WatchSession.completion_ratio), func.coalesce(func.sum(case((WatchSession.completed, 1), else_=0)), 0),
    )).one()
    likes, dislikes = db.execute(select(
        func.coalesce(func.sum(case((Reaction.value == 1, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Reaction.value == -1, 1), else_=0)), 0),
    )).one()

    day = func.date(WatchSession.started_at)
    per_day = {str(d)[:10]: n for d, n in db.execute(
        select(day, func.count(WatchSession.id)).where(WatchSession.started_at >= now - timedelta(days=13)).group_by(day))}
    daily = [{"day": (d := (now - timedelta(days=i)).date().isoformat()), "sessions": per_day.get(d, 0)} for i in range(13, -1, -1)]

    return {
        "users": users, "new_users_7d": new_7d, "active_users_7d": active_7d,
        "sessions": sessions, "watch_hours": round(watched / 3600, 1),
        "avg_completion_pct": round((_num(avg_completion) or 0) * 100), "completed_sessions": int(completed),
        "likes": int(likes), "dislikes": int(dislikes),
        "avg_rating": _num(db.scalar(select(func.avg(Rating.rating))), 1), "ratings": db.scalar(select(func.count(Rating.id))),
        "feedback_count": db.scalar(select(func.count(Feedback.id))), "daily_sessions": daily,
    }


@router.get("/users", summary="All users with their behaviour summary")
def list_users(search: Optional[str] = None, sort: str = "last_active", limit: int = Query(50, ge=1, le=200),
               offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    s = select(WatchSession.user_id, func.count(WatchSession.id).label("sessions"),
               func.coalesce(func.sum(WatchSession.watched_seconds), 0).label("watched"),
               func.avg(WatchSession.completion_ratio).label("avg_completion"),
               func.max(WatchSession.started_at).label("last_active")).group_by(WatchSession.user_id).subquery()
    rt = select(Rating.user_id, func.count(Rating.id).label("ratings"),
                func.avg(Rating.rating).label("avg_rating")).group_by(Rating.user_id).subquery()
    rx = select(Reaction.user_id, func.sum(case((Reaction.value == 1, 1), else_=0)).label("likes"),
                func.sum(case((Reaction.value == -1, 1), else_=0)).label("dislikes")).group_by(Reaction.user_id).subquery()

    q = (select(User, s.c.sessions, s.c.watched, s.c.avg_completion, s.c.last_active, rt.c.ratings, rt.c.avg_rating, rx.c.likes, rx.c.dislikes)
         .outerjoin(s, s.c.user_id == User.id).outerjoin(rt, rt.c.user_id == User.id).outerjoin(rx, rx.c.user_id == User.id))
    count_q = select(func.count(User.id))
    if search and search.strip():
        like = f"%{search.strip()}%"
        cond = or_(User.name.ilike(like), User.email.ilike(like))
        q, count_q = q.where(cond), count_q.where(cond)

    order = {"sessions": s.c.sessions.desc().nulls_last(), "watch_time": s.c.watched.desc().nulls_last(),
             "joined": User.created_at.desc()}.get(sort, s.c.last_active.desc().nulls_last())
    rows = db.execute(q.order_by(order, User.id).limit(limit).offset(offset)).all()

    return {"total": db.scalar(count_q), "users": [{
        "id": r.User.id, "name": r.User.name, "email": r.User.email, "is_active": r.User.is_active,
        "joined": _iso(r.User.created_at), "sessions": r.sessions or 0, "watch_minutes": round((r.watched or 0) / 60),
        "avg_completion_pct": round((_num(r.avg_completion) or 0) * 100) if r.sessions else None,
        "ratings": r.ratings or 0, "avg_rating": _num(r.avg_rating, 1), "likes": int(r.likes or 0),
        "dislikes": int(r.dislikes or 0), "last_active": _iso(r.last_active),
    } for r in rows]}


@router.get("/users/{user_id}", summary="One user's full activity")
def user_detail(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found.")

    sessions = db.execute(select(WatchSession, Movie.title).join(Movie, Movie.id == WatchSession.movie_id)
                          .where(WatchSession.user_id == user_id).order_by(WatchSession.started_at.desc()).limit(20)).all()
    ratings = db.execute(select(Rating.rating, Movie.title, Rating.created_at).join(Movie, Movie.id == Rating.movie_id)
                         .where(Rating.user_id == user_id).order_by(Rating.created_at.desc()).limit(20)).all()
    reactions = db.execute(select(Reaction.value, Movie.title).join(Movie, Movie.id == Reaction.movie_id)
                           .where(Reaction.user_id == user_id).order_by(Reaction.created_at.desc()).limit(20)).all()
    feedback = db.execute(select(Feedback.tags, Feedback.comment, Feedback.created_at, Movie.title)
                          .join(Movie, Movie.id == Feedback.movie_id).where(Feedback.user_id == user_id)
                          .order_by(Feedback.created_at.desc()).limit(20)).all()

    minutes = Counter()
    for genres, secs in db.execute(select(Movie.genres, WatchSession.watched_seconds)
                                   .join(Movie, Movie.id == WatchSession.movie_id).where(WatchSession.user_id == user_id)):
        for g in (genres or "").split(","):
            if g.strip():
                minutes[g.strip()] += secs or 0

    shown = db.scalar(select(func.count(Impression.id)).where(Impression.user_id == user_id))
    started = db.scalar(select(func.count(func.distinct(WatchSession.impression_id)))
                        .where(WatchSession.user_id == user_id, WatchSession.impression_id.is_not(None)))

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email, "is_active": user.is_active, "joined": _iso(user.created_at)},
        "top_genres": [{"genre": g, "minutes": round(m / 60)} for g, m in minutes.most_common(5)],
        "recommendations": {"shown": shown, "watched": started},
        "sessions": [{"movie": t, "started_at": _iso(x.started_at), "watched_minutes": round(x.watched_seconds / 60),
                      "runtime_minutes": round(x.runtime_seconds / 60), "completion_pct": round(x.completion_ratio * 100),
                      "completed": x.completed, "pauses": x.pause_count, "seeks": x.seek_count} for x, t in sessions],
        "ratings": [{"movie": t, "rating": r, "at": _iso(a)} for r, t, a in ratings],
        "reactions": [{"movie": t, "value": v} for v, t in reactions],
        "feedback": [{"movie": t, "tags": [g for g in (tags or "").split(",") if g], "comment": c, "at": _iso(a)} for tags, c, a, t in feedback],
    }


@router.get("/recommendations", summary="How each recommendation strategy performs")
def recommendation_health(db: Session = Depends(get_db)):
    rows = db.execute(select(Impression.model_version, func.count(func.distinct(Impression.id)),
                             func.count(func.distinct(WatchSession.id)), func.avg(WatchSession.completion_ratio))
                      .select_from(Impression).outerjoin(WatchSession, WatchSession.impression_id == Impression.id)
                      .group_by(Impression.model_version)).all()
    return [{"strategy": v or "unknown", "shown": shown, "started": started,
             "start_rate_pct": round(100 * started / shown) if shown else 0,
             "avg_completion_pct": round((_num(c) or 0) * 100) if started else None} for v, shown, started, c in rows]


@router.get("/daily", summary="Logins and watching per day, last 14 days (UTC days)")
def daily(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=13)
    login_day = func.date(LoginEvent.created_at)
    logins = {str(d)[:10]: (n, u) for d, n, u in db.execute(
        select(login_day, func.count(LoginEvent.id), func.count(func.distinct(LoginEvent.user_id)))
        .where(LoginEvent.created_at >= since).group_by(login_day))}
    watch_day = func.date(WatchSession.started_at)
    watching = {str(d)[:10]: (n, u) for d, n, u in db.execute(
        select(watch_day, func.count(WatchSession.id), func.count(func.distinct(WatchSession.user_id)))
        .where(WatchSession.started_at >= since).group_by(watch_day))}
    out = []
    for i in range(13, -1, -1):
        day = (now - timedelta(days=i)).date().isoformat()
        lg, wt = logins.get(day, (0, 0)), watching.get(day, (0, 0))
        out.append({"day": day, "logins": lg[0], "users_logged_in": lg[1], "films_started": wt[0], "users_watching": wt[1]})
    return out


@router.get("/activity", summary="Latest films watched, across all users")
def activity(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.execute(
        select(WatchSession, User.name, User.email, Movie.title)
        .join(User, User.id == WatchSession.user_id).join(Movie, Movie.id == WatchSession.movie_id)
        .order_by(WatchSession.started_at.desc()).limit(limit)).all()
    return [{"user": name, "email": email, "movie": title, "started_at": _iso(s.started_at),
             "watched_minutes": round(s.watched_seconds / 60), "runtime_minutes": round(s.runtime_seconds / 60),
             "completion_pct": round(s.completion_ratio * 100)} for s, name, email, title in rows]