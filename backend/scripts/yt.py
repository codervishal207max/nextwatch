"""Shared helpers for turning a YouTube video into a NextWatch film."""
import math
import re

from app.models import Movie

DURATION = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
SKIP_CATEGORIES = {"10", "20"}  # music, gaming
BAD_TITLE = re.compile(r"\b(scenes?|clips?|compilation|highlights|trailer|teaser|jukebox|promo|back to back|best of)\b", re.I)
PROMO = re.compile(
    r"(subscribe|follow (us|me)|patreon|instagram|facebook|twitter|whatsapp|telegram|earn|sponsor|giveaway|merch|"
    r"join (us|our|the)|click|link in|playlist|watch more|fancy another|bell icon|like and share|business|copyright|©|all rights)",
    re.I,
)
URL = re.compile(r"https?://\S+|www\.\S+")
STAMP = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")


def seconds(iso: str) -> int:
    h, m, s = (int(x or 0) for x in DURATION.fullmatch(iso).groups())
    return h * 3600 + m * 60 + s


def best_thumb(thumbs: dict) -> str:
    for key in ("maxres", "standard", "high", "medium", "default"):
        if key in thumbs:
            return thumbs[key]["url"]
    return ""


def clean_description(text: str, limit: int = 260) -> str:
    """Keep the first real sentences; drop links, timestamps, separators and promo lines."""
    text = STAMP.sub(" ", URL.sub(" ", text or ""))
    text = re.sub(r"[-=_*~#•–—]{3,}", " ", text)
    kept, total = [], 0
    for part in (p.strip(" -|:") for p in re.split(r"(?<=[.!?])\s+|\n+", text)):
        if len(part) < 20 or PROMO.search(part):
            continue
        if kept and total + len(part) > limit:
            break
        kept.append(part)
        total += len(part) + 1
        if total >= limit:
            break
    out = " ".join(kept)
    return out[: limit - 1].rsplit(" ", 1)[0] + "…" if len(out) > limit else out


def movie_from_video(v: dict, genre: str, allow_standard: bool = False):
    """Return (Movie, "") if the video qualifies, otherwise (None, reason)."""
    secs = seconds(v["contentDetails"]["duration"])
    sn, st, stat = v["snippet"], v["status"], v.get("statistics", {})
    cc = st.get("license") == "creativeCommon"
    if not 1800 <= secs <= 3600:
        return None, f"runtime is {round(secs / 60)} min (needs 30-60)"
    if not st.get("embeddable"):
        return None, "the owner does not allow embedding"
    if st.get("privacyStatus") != "public":
        return None, "the video is not public"
    if not cc and not allow_standard:
        return None, "not CC BY licensed (use --allow-standard only for the rights holder's own upload)"
    if sn.get("categoryId") in SKIP_CATEGORIES:
        return None, "music or gaming video"
    if BAD_TITLE.search(sn["title"]):
        return None, "looks like clips or a trailer, not a film"

    views, likes = int(stat.get("viewCount", 0)), int(stat.get("likeCount", 0))
    thumb = best_thumb(sn.get("thumbnails", {}))
    credit = "(CC BY)" if cc else "(embedded with the uploader's permission)"
    movie = Movie(
        title=sn["title"][:250],
        overview=f"{clean_description(sn.get('description', ''))}\n\nBy {sn['channelTitle']} on YouTube {credit}.".strip(),
        genres=genre, runtime_minutes=round(secs / 60), year=int(sn["publishedAt"][:4]),
        language=sn.get("defaultAudioLanguage") or sn.get("defaultLanguage"),
        poster_path=thumb, backdrop_path=thumb, video_url=f"youtube:{v['id']}", vote_count=likes,
        popularity=round(min(100.0, math.log10(views + 1) * 14), 1),
        # simple engagement score (likes per view), not a critic rating
        rating=round(5 + 5 * min(1.0, (likes / views) * 20), 1) if views else 6.5,
    )
    return movie, ""