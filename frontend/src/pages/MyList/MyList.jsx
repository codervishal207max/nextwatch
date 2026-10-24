import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PosterGrid from "../../components/common/PosterGrid";
import useWatchlist from "../../hooks/useWatchlist";
import { watchlistAPI } from "../../services/api";
import { toCard } from "../../utils/media";

export default function MyList() {
  const [movies, setMovies] = useState(null);
  const [error, setError] = useState("");
  const { ids } = useWatchlist();

  useEffect(() => {
    watchlistAPI.get().then((r) => setMovies(r.data.map((m) => toCard(m)))).catch(() => setError("Could not load your list."));
  }, []);

  // a film disappears from this page as soon as its heart is switched off
  const shown = (movies || []).filter((m) => ids.has(m.id));

  return (
    <div className="mx-auto max-w-7xl px-6 py-8 text-white">
      <h1 className="mb-6 text-3xl font-bold">My List</h1>
      {error && <p className="text-red-400">{error}</p>}
      {!error && movies === null && <p className="text-slate-400">Loading...</p>}
      {movies && !shown.length && (
        <p className="text-slate-400">
          Nothing saved yet. Tap the heart on any film, or <Link to="/movies" className="text-cyan-400 hover:underline">browse movies</Link>.
        </p>
      )}
      {shown.length > 0 && <PosterGrid movies={shown} />}
    </div>
  );
}