import { ChevronRight } from "lucide-react";
import MovieCard from "./MovieCard";
function MovieSection({ title, movies = [] }) { return <section className="movie-section"><div className="section-heading"><h2>{title}</h2><button aria-label={`See all ${title}`}><ChevronRight size={20} /></button></div><div className="movie-row">{movies.map((movie) => <MovieCard key={movie.id} movie={movie} />)}</div></section>; }
export default MovieSection;
