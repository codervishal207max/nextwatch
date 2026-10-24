// TMDB/YouTube image helper. Accepts a full URL, a "/abc.jpg" path, or nothing.
export function posterUrl(path, size = "w500") {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `https://image.tmdb.org/t/p/${size}${path.startsWith("/") ? path : `/${path}`}`;
}

// Shape a backend movie for MovieCard / HeroBanner. `score` (0-1) is a real model score, if any.
export const toCard = (m, score = null) => ({
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