import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Heart, Play } from "lucide-react";
import useWatchlist from "../../hooks/useWatchlist";
import { movieAPI } from "../../services/api";
import { posterUrl } from "../../utils/media";

function MovieDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { ids, toggle } = useWatchlist();

  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    movieAPI.getById(id)
      .then((r) => { if (!cancelled) setMovie(r.data); })
      .catch(() => { if (!cancelled) setError("Unable to load movie details."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  if (loading) {
    return <div className="flex min-h-[70vh] items-center justify-center text-white"><p className="text-lg">Loading movie...</p></div>;
  }

  if (error || !movie) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center gap-4 text-white">
        <p className="text-lg">{error || "Movie not found."}</p>
        <button onClick={() => navigate("/")} className="rounded-lg bg-white px-5 py-2 text-black">Back to Home</button>
      </div>
    );
  }

  // works for TMDB paths and for full image URLs (YouTube thumbnails)
  const poster = posterUrl(movie.poster_path);
  const backdrop = posterUrl(movie.backdrop_path, "original");
  const saved = ids.has(movie.id);
  const votes = Number(movie.vote_count);

  return (
    <div className="relative min-h-screen text-white">
      {backdrop && (
        <div className="absolute inset-0 h-[520px] bg-cover bg-center opacity-30" style={{ backgroundImage: `url(${backdrop})` }} />
      )}
      <div className="absolute inset-0 h-[520px] bg-gradient-to-b from-transparent via-[#0b0f17]/80 to-[#0b0f17]" />

      <div className="relative z-10 px-5 py-8 md:px-10">
        <button onClick={() => navigate(-1)} className="mb-10 flex items-center gap-2 text-gray-300 transition hover:text-white">
          <ArrowLeft size={20} /> Back
        </button>

        <div className="mx-auto flex max-w-6xl flex-col items-start gap-8 md:flex-row">
          <div className="w-[240px] shrink-0 md:w-[280px]">
            {poster ? (
              <img src={poster} alt={movie.title} className="w-full rounded-2xl shadow-2xl" />
            ) : (
              <div className="flex aspect-[2/3] items-center justify-center rounded-2xl bg-gray-800">No Poster</div>
            )}
          </div>

          <div className="max-w-3xl pt-2">
            <p className="mb-3 font-semibold text-pink-400">{movie.genres || "Movie"}</p>
            <h1 className="mb-5 text-4xl font-bold md:text-5xl">{movie.title}</h1>

            <div className="mb-6 flex flex-wrap items-center gap-4 text-gray-300">
              {movie.runtime_minutes ? <span>{movie.runtime_minutes} min</span> : null}
              {movie.year ? <span>{movie.year}</span> : null}
              {movie.rating != null && <span className="font-semibold text-yellow-400">★ {Number(movie.rating).toFixed(1)}</span>}
              {votes > 0 && <span>{votes.toLocaleString()} likes</span>}
            </div>

            <p className="mb-8 whitespace-pre-line text-base leading-7 text-gray-300 md:text-lg">
              {movie.overview || "No description available for this movie."}
            </p>

            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => navigate(`/watch/${movie.id}`)}
                className="flex items-center gap-2 rounded-full bg-white px-6 py-3 font-semibold text-black transition hover:bg-gray-200"
              >
                <Play size={18} fill="currentColor" /> Watch now
              </button>
              <button
                onClick={() => toggle(movie.id)}
                aria-pressed={saved}
                className="flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-6 py-3 transition hover:bg-white/20"
              >
                <Heart size={18} fill={saved ? "currentColor" : "none"} /> {saved ? "In My List" : "Add to My List"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MovieDetails;