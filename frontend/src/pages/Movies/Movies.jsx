import { useEffect, useState } from "react";
import PosterGrid from "../../components/common/PosterGrid";
import { movieAPI } from "../../services/api";
import { toCard } from "../../utils/media";

const PAGE = 24;

export default function Movies() {
  const [genres, setGenres] = useState([]);
  const [genre, setGenre] = useState("");
  const [movies, setMovies] = useState([]);
  const [more, setMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { movieAPI.getGenres().then((r) => setGenres(r.data)).catch(() => {}); }, []);

  const load = async (reset) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await movieAPI.list({ skip: reset ? 0 : movies.length, limit: PAGE, genre: genre || undefined });
      const cards = data.map((m) => toCard(m));
      setMovies(reset ? cards : [...movies, ...cards]);
      setMore(data.length === PAGE);
    } catch {
      setError("Could not load films.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(true); }, [genre]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8 text-white">
      <h1 className="mb-1 text-3xl font-bold">Movies</h1>
      <p className="mb-6 text-sm text-slate-400">Every film here runs 30 to 60 minutes.</p>

      <div className="mb-6 flex flex-wrap gap-2" role="group" aria-label="Filter by genre">
        {["", ...genres].map((g) => (
          <button key={g || "all"} aria-pressed={genre === g} onClick={() => setGenre(g)}
            className={`rounded-full border px-4 py-1.5 text-sm transition-colors ${genre === g ? "border-cyan-400 bg-cyan-400/15 text-cyan-300" : "border-slate-700 text-slate-300 hover:border-slate-500"}`}>
            {g || "All"}
          </button>
        ))}
      </div>

      {error && <p className="text-red-400">{error}</p>}
      {!loading && !error && !movies.length && <p className="text-slate-400">No films in this genre yet.</p>}
      <PosterGrid movies={movies} />
      {loading && <p className="mt-6 text-slate-400">Loading...</p>}
      {more && !loading && (
        <button onClick={() => load(false)} className="mt-8 rounded-lg border border-slate-700 px-5 py-2 text-sm hover:border-cyan-400">
          Load more
        </button>
      )}
    </div>
  );
}