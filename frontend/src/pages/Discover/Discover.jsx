import { useEffect, useState } from "react";
import PosterGrid from "../../components/common/PosterGrid";
import { recommendAPI } from "../../services/api";
import { toCard } from "../../utils/media";

export default function Discover() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    recommendAPI.getNext(20).then((r) => setData(r.data)).catch(() => setError("Could not load recommendations."));
  }, []);

  const personal = data?.strategy?.startsWith("model");

  return (
    <div className="mx-auto max-w-7xl px-6 py-8 text-white">
      <h1 className="mb-1 text-3xl font-bold">Discover</h1>
      <p className="mb-6 text-sm text-slate-400">
        {personal
          ? "Picked for you from how long you watch, what you rate and what you like."
          : "Popular right now. Watch and rate a few films and these picks become personal."}
      </p>
      {error && <p className="text-red-400">{error}</p>}
      {!error && !data && <p className="text-slate-400">Loading...</p>}
      {data && !data.items.length && <p className="text-slate-400">You have watched everything we have. New films are added regularly.</p>}
      {data && data.items.length > 0 && <PosterGrid movies={data.items.map((i) => toCard(i.movie, i.score))} />}
    </div>
  );
}