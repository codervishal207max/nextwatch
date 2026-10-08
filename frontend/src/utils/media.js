// TMDB image helper. Accepts a full URL, a "/abc.jpg" path, or nothing.
export function posterUrl(path, size = "w500") {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `https://image.tmdb.org/t/p/${size}${path.startsWith("/") ? path : `/${path}`}`;
}
