import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Play } from "lucide-react";

const clamp = (lines) => ({ display: "-webkit-box", WebkitLineClamp: lines, WebkitBoxOrient: "vertical", overflow: "hidden" });

// `movies` come from the backend (top picks), already shaped by toCard()
function HeroBanner({ movies = [] }) {
  const [active, setActive] = useState(0);
  const navigate = useNavigate();
  const slides = movies.slice(0, 3);

  useEffect(() => {
    if (slides.length < 2) return undefined;
    const timer = setInterval(() => setActive((i) => (i + 1) % slides.length), 6500);
    return () => clearInterval(timer);
  }, [slides.length]);

  if (!slides.length) return <section className="featured-section"><div className="featured-card" /></section>;
  const movie = slides[active % slides.length];
  const step = (d) => setActive((i) => (i + d + slides.length) % slides.length);

  return (
    <section className="featured-section">
      <div className="featured-card">
        <div className="featured-art" style={movie.backdrop ? { backgroundImage: `url(${movie.backdrop})` } : undefined} />
        <div className="featured-copy">
          {movie.poster && <img src={movie.poster} alt={`${movie.title} poster`} className="featured-poster" />}
          <div className="featured-description">
            <h1 style={clamp(2)}>{movie.title}</h1>
            <p style={clamp(3)}>{movie.overview}</p>
            <small>{[movie.genres?.join(" / "), movie.year, movie.runtime && `${movie.runtime} min`].filter(Boolean).join("  |  ")}</small>
            <div className="featured-buttons">
              <button className="play-button" onClick={() => navigate(`/watch/${movie.id}`)}>
                <Play size={16} fill="currentColor" /> Watch now
              </button>
            </div>
          </div>
        </div>
        {slides.length > 1 && (
          <>
            <button className="hero-arrow left" onClick={() => step(-1)} aria-label="Previous"><ChevronLeft /></button>
            <button className="hero-arrow right" onClick={() => step(1)} aria-label="Next"><ChevronRight /></button>
            <div className="hero-dots">
              {slides.map((_, i) => <button key={i} className={i === active ? "active" : ""} onClick={() => setActive(i)} aria-label={`Slide ${i + 1}`} />)}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default HeroBanner;