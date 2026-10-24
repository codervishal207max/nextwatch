import MovieCard from "../Home/MovieCard";

// Responsive grid of film cards (the Home rows scroll sideways; list pages use this).
export default function PosterGrid({ movies }) {
  return (
    <>
      <style>{`.poster-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:1.25rem}
.poster-grid .movie-card{width:100%!important;min-width:0!important;flex:none!important}`}</style>
      <div className="poster-grid">
        {movies.map((m) => <MovieCard key={m.id} movie={m} />)}
      </div>
    </>
  );
}