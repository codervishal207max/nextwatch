import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Heart } from "lucide-react";

function MovieCard({ movie }) {
  const [saved, setSaved] = useState(false);
  const [broken, setBroken] = useState(false);
  const navigate = useNavigate();
  const open = () => navigate(`/movie/${movie.id}`);

  return (
    <article
      className="movie-card"
      tabIndex="0"
      role="button"
      onClick={open}
      onKeyDown={(e) => e.key === "Enter" && open()}
    >
      <div className="movie-poster">
        {movie.poster && !broken ? (
          <img src={movie.poster} alt={movie.title} loading="lazy" onError={() => setBroken(true)} />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-slate-800 p-3 text-center text-sm font-semibold text-slate-300">
            {movie.title}
          </div>
        )}
        <button
          className={saved ? "saved" : ""}
          onClick={(e) => { e.stopPropagation(); setSaved((v) => !v); }}
          aria-label={`Save ${movie.title}`}
        >
          <Heart size={15} fill={saved ? "currentColor" : "none"} />
        </button>
        {movie.match != null && (
          <div className="poster-progress"><span style={{ width: `${movie.match}%` }} /></div>
        )}
      </div>
      {/* Match % only appears when it is a real model score */}
      {movie.match != null
        ? <p className="match-score">{movie.match}% match</p>
        : <p className="match-score">{movie.runtime ? `${movie.runtime} min` : `★ ${movie.rating ?? "–"}`}</p>}
      <h3>{movie.title}</h3>
      <small>{movie.genres?.[0]}</small>
    </article>
  );
}

export default MovieCard;
