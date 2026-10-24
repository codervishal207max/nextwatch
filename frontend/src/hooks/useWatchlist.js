import { useCallback, useEffect, useState } from "react";
import { watchlistAPI } from "../services/api";

// One shared copy of "which films are saved", so every heart on every page stays in sync.
let cache = null;
const listeners = new Set();
const publish = (ids) => { cache = ids; listeners.forEach((fn) => fn(ids)); };

export function resetWatchlist() {
  cache = null;
  listeners.forEach((fn) => fn(new Set()));
}

export default function useWatchlist() {
  const [ids, setIds] = useState(cache || new Set());

  useEffect(() => {
    listeners.add(setIds);
    if (!cache) {
      watchlistAPI.get().then((r) => publish(new Set(r.data.map((m) => m.id)))).catch(() => {});
    } else {
      setIds(cache);
    }
    return () => listeners.delete(setIds);
  }, []);

  const toggle = useCallback(async (movieId) => {
    const current = cache || new Set();
    const had = current.has(movieId);
    const next = new Set(current);
    if (had) next.delete(movieId); else next.add(movieId);
    publish(next); // update the heart immediately
    try {
      if (had) await watchlistAPI.remove(movieId); else await watchlistAPI.add(movieId);
    } catch (e) {
      if (!had && e.response?.status === 400) return; // already saved on the server, fine
      const back = new Set(cache);
      if (had) back.add(movieId); else back.delete(movieId);
      publish(back);
    }
  }, []);

  return { ids, toggle };
}