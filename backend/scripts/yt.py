"""Shared helpers for turning a YouTube video into a NextWatch film."""
import math
import re
from pathlib import Path

from app.models import Movie

DURATION = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
SKIP_CATEGORIES = {"10", "20"}  # music, gaming
BAD_TITLE = re.compile(r"\b(scenes?|clips?|compilation|highlights|trailer|teaser|jukebox|promo|back to back|best of)\b", re.I)
PROMO = re.compile(
    r"(subscribe|follow (us|me)|patreon|instagram|facebook|twitter|whatsapp|telegram|earn|sponsor|giveaway|merch|"
    r"join (us|our|the)|click|link in|playlist|watch more|fancy another|bell icon|like and share|business|copyright|©|all rights)",
    re.I,
)
ADULT = re.compile(
    r"(18\s*\+|adults?\s+only|\bsexy\b|\bsex\b|erotic|hot\s+scenes?|\buncut\b|\bnud(e|ity)\b|bed\s*scene|bikini|seduc\w*|\bxxx\b|\bnsfw\b|b[- ]?grade|bold\s+scenes?)",
    re.I,
)
BLOCKLIST_FILE = Path(__file__).resolve().parents[1] / "blocked_videos.txt"
_blocked = None
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


def movie_from_video(v: dict, genre: str, allow_standard: bool = False, explicit: bool = False, any_length: bool = False):
    """Return (Movie, "") if the video qualifies, otherwise (None, reason).

    explicit=True is for videos you picked by hand: the clips/trailer and music/gaming checks are skipped.
    any_length=True skips the 30-60 minute rule."""
    secs = seconds(v["contentDetails"]["duration"])
    sn, st, stat = v["snippet"], v["status"], v.get("statistics", {})
    cc = st.get("license") == "creativeCommon"
    if v["contentDetails"].get("contentRating", {}).get("ytRating") == "ytAgeRestricted":
        return None, "age-restricted on YouTube"
    if not explicit and v["id"] in load_blocklist():
        return None, "you removed this film earlier (blocked_videos.txt)"
    if not explicit and ADULT.search(f"{sn['title']} {sn.get('description', '')[:300]}"):
        return None, "title or description looks adult"
    if not any_length and not 1800 <= secs <= 3600:
        return None, f"runtime is {round(secs / 60)} min (needs 30-60)"
    if not st.get("embeddable"):
        return None, "the owner does not allow embedding"
    if st.get("privacyStatus") != "public":
        return None, "the video is not public"
    if not cc and not allow_standard:
        return None, "not CC BY licensed (use --allow-standard only for the rights holder's own upload)"
    if not explicit and sn.get("categoryId") in SKIP_CATEGORIES:
        return None, "music or gaming video"
    if not explicit and BAD_TITLE.search(sn["title"]):
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


VIDEO_ID = re.compile(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})")


def parse_list(text: str, default_genre: str = "Drama"):
    """Read lines like   https://youtu.be/XXXXXXXXXXX | Documentary | My own title   (genre and title are optional).
    Lines starting with # are comments. Returns (entries, lines_that_could_not_be_read)."""
    entries, bad, seen = [], [], set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        found = VIDEO_ID.search(parts[0]) or re.fullmatch(r"([A-Za-z0-9_-]{11})", parts[0])
        if not found:
            bad.append(raw)
            continue
        vid = found.group(1)
        if vid in seen:
            continue
        seen.add(vid)
        entries.append({"id": vid, "genre": (parts[1] if len(parts) > 1 and parts[1] else default_genre),
                        "title": (parts[2] if len(parts) > 2 and parts[2] else None)})
    return entries, bad


def looks_unsuitable(title: str, overview: str = "") -> bool:
    """True if the title or description looks adult, or like clips/trailers. A guess from words, not a guarantee."""
    return bool(ADULT.search(f"{title or ''} {(overview or '')[:300]}")) or bool(BAD_TITLE.search(title or ""))


def load_blocklist() -> set:
    """Video ids you removed on purpose. Imports never bring them back."""
    global _blocked
    if _blocked is None:
        _blocked = set()
        if BLOCKLIST_FILE.exists():
            for line in BLOCKLIST_FILE.read_text().splitlines():
                line = line.split("#", 1)[0].strip()
                if line:
                    _blocked.add(line)
    return _blocked


def add_to_blocklist(video_ids) -> None:
    new = sorted(set(video_ids) - load_blocklist())
    if new:
        with open(BLOCKLIST_FILE, "a") as f:
            f.write("\n".join(new) + "\n")
        _blocked.update(new)