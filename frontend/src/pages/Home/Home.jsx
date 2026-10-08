import { useEffect, useState } from "react";

import HeroBanner from "../../components/Home/HeroBanner";
import MovieSection from "../../components/Home/MovieSection";
import Footer from "../../layout/Footer";
import { movieAPI, recommendAPI } from "../../services/api";
import { posterUrl } from "../../utils/media";

const toCard = (m, score = null) => ({
  id: m.id,
  title: m.title,
  year: m.year,
  rating: m.rating,
  runtime: m.runtime_minutes,
  overview: m.overview,
  genres: m.genres ? m.genres.split(",").map((g) => g.trim()) : [],
  poster: posterUrl(m.poster_path),
  backdrop: posterUrl(m.backdrop_path, "original"),
  match: score == null ? null : Math.round(score * 100),
});

function Home() {
  const [state, setState] = useState({ loading: true, picks: [], trending: [], topRated: [], strategy: "" });

  useEffect(() => {
    (async () => {
      const [next, trending, top] = await Promise.allSettled([
        recommendAPI.getNext(8), movieAPI.getTrending(), movieAPI.getTopRated(),
      ]);
      const picks = next.status === "fulfilled" ? next.value.data.items : [];
      setState({
        loading: false,
        strategy: next.status === "fulfilled" ? next.value.data.strategy : "",
        picks: picks.map((p) => toCard(p.movie, p.score)),
        trending: trending.status === "fulfilled" ? trending.value.data.map((m) => toCard(m)) : [],
        topRated: top.status === "fulfilled" ? top.value.data.map((m) => toCard(m)) : [],
      });
    })();
  }, []);

  const { loading, picks, trending, topRated, strategy } = state;
  const heroMovies = picks.length ? picks : trending;
  const pickTitle = strategy.startsWith("model") ? "Your next film" : "Start with one of these";

  return (
    <div className="dashboard-page">
      <HeroBanner movies={heroMovies} />
      <div className="movie-shelves">
        {loading && <p className="px-5 py-10 text-gray-400">Loading films...</p>}
        {!loading && !heroMovies.length && (
          <p className="px-5 py-10 text-gray-400">No films yet. Run <code>python seed.py</code> or <code>python scripts/import_tmdb.py</code> in backend/.</p>
        )}
        {picks.length > 0 && <MovieSection title={pickTitle} movies={picks} />}
        {trending.length > 0 && <MovieSection title="Trending" movies={trending} />}
        {topRated.length > 0 && <MovieSection title="Top rated" movies={topRated} />}
      </div>
      <Footer />
    </div>
  );
}

export default Home;
