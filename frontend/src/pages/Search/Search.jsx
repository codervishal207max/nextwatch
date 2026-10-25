import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import PosterGrid from "../../components/common/PosterGrid";
import API from "../../services/api";
import { toCard } from "../../utils/media";

export default function Search() {
  const [params] = useSearchParams();
  const q = (params.get("q") || "").trim();
  const [results, setResults] = useState(null); // null while loading
  const [error, setError] = useState("");

  useEffect(() => {
    if (!q) { setResults([]); return undefined; }
    let cancelled = false;
    setResults(null);
    setError("");
    API.get("/api/movies/search", { params: { q } })
      .then((r) => { if (!cancelled) setResults(r.data.map((m) => toCard(m))); })
      .catch(() => { if (!cancelled) setError("Could not search right now. Please try again."); });
    return () => { cancelled = true; };
  }, [q]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8 text-white">
      {!q && <p className="text-slate-400">Type a movie name in the search bar.</p>}

      {q && (
        <h1 className="mb-6 text-2xl font-bold">
          Results for “{q}”{results ? <span className="ml-2 text-base font-normal text-slate-400">({results.length})</span> : null}
        </h1>
      )}

      {q && results === null && !error && <p className="text-slate-400">Searching...</p>}
      {error && <p className="text-red-400">{error}</p>}

      {q && results && results.length === 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center" role="status">
          <p className="text-xl font-semibold">Sorry your movie is not available on nextwatch!</p>
          <p className="mt-2 text-sm text-slate-400">
            Nothing matches “{q}”. Check the spelling, or <Link to="/movies" className="text-cyan-400 hover:underline">browse all movies</Link>.
          </p>
        </div>
      )}

      {results && results.length > 0 && <PosterGrid movies={results} />}
    </div>
  );
}