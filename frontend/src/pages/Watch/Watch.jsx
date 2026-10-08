import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ThumbsDown, ThumbsUp } from "lucide-react";
import { movieAPI, trackingAPI } from "../../services/api";

const TAGS = ["great_ending", "loved_the_acting", "too_slow", "too_long", "not_my_genre", "want_more_like_this"];
const label = (t) => t.replace(/_/g, " ");

function Watch() {
  const { id } = useParams();
  const navigate = useNavigate();
  const video = useRef(null);
  const session = useRef({ id: null, starting: false, watched: 0, furthest: 0, pauses: 0, seeks: 0, last: 0 });

  const [movie, setMovie] = useState(null);
  const [error, setError] = useState("");
  const [finished, setFinished] = useState(false);
  const [sent, setSent] = useState(false);
  const [rating, setRating] = useState(null);
  const [reaction, setReaction] = useState(0);
  const [tags, setTags] = useState([]);
  const [comment, setComment] = useState("");

  useEffect(() => {
    movieAPI.getById(id).then((r) => setMovie(r.data)).catch(() => setError("Could not load this film."));
  }, [id]);

  const send = (ended = false) => {
    const s = session.current;
    if (!s.id) return;
    trackingAPI.update(s.id, {
      watched_seconds: Math.round(s.watched), furthest_second: Math.round(s.furthest),
      pause_count: s.pauses, seek_count: s.seeks, ended,
    }).catch(() => {});
  };

  // heartbeat every 15 s while mounted, final update when the viewer leaves
  useEffect(() => {
    const timer = setInterval(() => { if (video.current && !video.current.paused) send(false); }, 15000);
    const hidden = () => document.hidden && send(false);
    document.addEventListener("visibilitychange", hidden);
    return () => { clearInterval(timer); document.removeEventListener("visibilitychange", hidden); send(true); };
  }, []);

  const onPlay = async () => {
    const s = session.current;
    if (s.id || s.starting) return;
    s.starting = true;
    try {
      const res = await trackingAPI.start({ movie_id: Number(id), device: window.innerWidth < 768 ? "mobile" : "desktop" });
      s.id = res.data.id;
    } catch { setError("Could not start tracking this session."); }
  };

  const onTimeUpdate = () => {
    const s = session.current, t = video.current.currentTime, delta = t - s.last;
    if (!video.current.paused && delta > 0 && delta < 2) s.watched += delta; // skips don't count as watching
    s.furthest = Math.max(s.furthest, t);
    s.last = t;
  };

  const submit = async () => {
    const calls = [];
    if (rating) calls.push(trackingAPI.rate(id, rating));
    if (reaction) calls.push(trackingAPI.react(id, reaction));
    if (tags.length || comment.trim()) calls.push(trackingAPI.feedback(id, { session_id: session.current.id, tags, comment: comment.trim() || null }));
    await Promise.allSettled(calls);
    setSent(true);
  };

  if (error) return <p className="p-10 text-red-400">{error}</p>;
  if (!movie) return <p className="p-10 text-gray-400">Loading...</p>;

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 text-white">
      <button onClick={() => navigate(-1)} className="mb-6 flex items-center gap-2 text-gray-300 hover:text-white">
        <ArrowLeft size={18} /> Back
      </button>
      <h1 className="mb-1 text-3xl font-bold">{movie.title}</h1>
      <p className="mb-5 text-sm text-gray-400">{movie.runtime_minutes} min</p>

      {movie.video_url ? (
        <video
          ref={video} src={movie.video_url} controls className="w-full rounded-xl bg-black"
          onPlay={onPlay} onTimeUpdate={onTimeUpdate}
          onPause={() => { if (!video.current.ended) { session.current.pauses += 1; send(false); } }}
          onSeeking={() => { session.current.seeks += 1; }}
          onSeeked={() => { session.current.last = video.current.currentTime; }}
          onEnded={() => { send(true); setFinished(true); }}
        />
      ) : (
        <div className="flex aspect-video items-center justify-center rounded-xl bg-slate-900 text-center text-slate-400">
          No video is attached to this film yet. Set movies.video_url to a playable file.
        </div>
      )}

      {!finished && (
        <button onClick={() => setFinished(true)} className="mt-4 text-sm text-slate-400 hover:text-white">
          Give feedback now
        </button>
      )}

      {finished && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6" aria-label="Feedback">
          {sent ? (
            <div>
              <p className="mb-4 text-lg font-semibold">Thanks. Your next film is ready.</p>
              <button onClick={() => navigate("/")} className="rounded-lg bg-cyan-400 px-5 py-2 font-bold text-slate-950 hover:bg-cyan-300">
                See what's next
              </button>
            </div>
          ) : (
            <>
              <h2 className="mb-4 text-xl font-bold">How was it?</h2>
              <div className="mb-5 flex gap-3">
                <button aria-pressed={reaction === 1} onClick={() => setReaction(reaction === 1 ? 0 : 1)}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2 ${reaction === 1 ? "border-cyan-400 bg-cyan-400/15" : "border-slate-700"}`}>
                  <ThumbsUp size={16} /> Like
                </button>
                <button aria-pressed={reaction === -1} onClick={() => setReaction(reaction === -1 ? 0 : -1)}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2 ${reaction === -1 ? "border-red-400 bg-red-400/15" : "border-slate-700"}`}>
                  <ThumbsDown size={16} /> Dislike
                </button>
              </div>
              <p className="mb-2 text-sm text-slate-400">Rating</p>
              <div className="mb-5 flex flex-wrap gap-2">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <button key={n} aria-pressed={rating === n} onClick={() => setRating(n)}
                    className={`h-9 w-9 rounded-lg border text-sm ${rating === n ? "border-cyan-400 bg-cyan-400 text-slate-950" : "border-slate-700"}`}>
                    {n}
                  </button>
                ))}
              </div>
              <p className="mb-2 text-sm text-slate-400">What stood out?</p>
              <div className="mb-5 flex flex-wrap gap-2">
                {TAGS.map((t) => (
                  <button key={t} aria-pressed={tags.includes(t)}
                    onClick={() => setTags((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]))}
                    className={`rounded-full border px-3 py-1 text-sm ${tags.includes(t) ? "border-cyan-400 bg-cyan-400/15" : "border-slate-700 text-slate-300"}`}>
                    {label(t)}
                  </button>
                ))}
              </div>
              <textarea value={comment} onChange={(e) => setComment(e.target.value)} maxLength={1000} rows={3}
                placeholder="Anything else? (optional)"
                className="mb-5 w-full rounded-lg border border-slate-800 bg-slate-950 p-3 text-sm outline-none focus-visible:border-cyan-400" />
              <div className="flex gap-3">
                <button onClick={submit} className="rounded-lg bg-cyan-400 px-5 py-2 font-bold text-slate-950 hover:bg-cyan-300">Send feedback</button>
                <button onClick={() => navigate("/")} className="rounded-lg px-5 py-2 text-slate-400 hover:text-white">Skip</button>
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}

export default Watch;
