import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Heart, Play } from "lucide-react";
import { movieAPI } from "../../services/api";

function MovieDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchMovie = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await movieAPI.getById(id);
        setMovie(response.data);
      } catch (err) {
        console.error("Movie details error:", err);
        setError("Unable to load movie details.");
      } finally {
        setLoading(false);
      }
    };

    fetchMovie();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center text-white">
        <p className="text-lg">Loading movie...</p>
      </div>
    );
  }

  if (error || !movie) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center text-white gap-4">
        <p className="text-lg">{error || "Movie not found."}</p>

        <button
          onClick={() => navigate("/")}
          className="px-5 py-2 rounded-lg bg-white text-black"
        >
          Back to Home
        </button>
      </div>
    );
  }

  const poster = movie.poster_path
    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
    : null;

  const backdrop = movie.backdrop_path
    ? `https://image.tmdb.org/t/p/original${movie.backdrop_path}`
    : null;

  return (
    <div className="relative min-h-screen text-white">
      {/* Backdrop */}
      {backdrop && (
        <div
          className="absolute inset-0 h-[520px] bg-cover bg-center opacity-30"
          style={{ backgroundImage: `url(${backdrop})` }}
        />
      )}

      <div className="absolute inset-0 h-[520px] bg-gradient-to-b from-transparent via-[#0b0f17]/80 to-[#0b0f17]" />

      <div className="relative z-10 px-5 md:px-10 py-8">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 mb-10 text-gray-300 hover:text-white transition"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        {/* Movie content */}
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-8 items-start">
          
          {/* Poster */}
          <div className="w-[240px] md:w-[280px] shrink-0">
            {poster ? (
              <img
                src={poster}
                alt={movie.title}
                className="w-full rounded-2xl shadow-2xl"
              />
            ) : (
              <div className="aspect-[2/3] rounded-2xl bg-gray-800 flex items-center justify-center">
                No Poster
              </div>
            )}
          </div>

          {/* Information */}
          <div className="max-w-3xl pt-2">
            <p className="text-pink-400 font-semibold mb-3">
              {movie.genres || "Movie"}
            </p>

            <h1 className="text-4xl md:text-6xl font-bold mb-5">
              {movie.title}
            </h1>

            <div className="flex flex-wrap items-center gap-4 text-gray-300 mb-6">
              {movie.runtime_minutes && <span>{movie.runtime_minutes} min</span>}
              {movie.year && <span>{movie.year}</span>}

              {movie.rating != null && (
                <span className="text-yellow-400 font-semibold">
                  ★ {Number(movie.rating).toFixed(1)}
                </span>
              )}

              {movie.vote_count != null && (
                <span>{movie.vote_count.toLocaleString()} votes</span>
              )}
            </div>

            <p className="text-gray-300 leading-7 text-base md:text-lg mb-8">
              {movie.overview || "No description available for this movie."}
            </p>

            {/* Buttons */}
            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => navigate(`/watch/${movie.id}`)}
                className="flex items-center gap-2 px-6 py-3 rounded-full bg-white text-black font-semibold hover:bg-gray-200 transition"
              >
                <Play size={18} fill="currentColor" />
                Watch now
              </button>

              <button
                className="flex items-center gap-2 px-6 py-3 rounded-full border border-white/30 bg-white/10 hover:bg-white/20 transition"
              >
                <Heart size={18} />
                Add to My List
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MovieDetails;