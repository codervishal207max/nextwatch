import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Play } from "lucide-react";

const clamp = (lines) => ({ display: "-webkit-box", WebkitLineClamp: lines, WebkitBoxOrient: "vertical", overflow: "hidden" });
const AUTO_MS = 6500;   // each slide stays this long
const SWIPE_PX = 50;    // how far a finger must move to count as a swipe

// `movies` come from the backend (top picks), already shaped by toCard()
function HeroBanner({ movies = [] }) {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false); // true while a finger is on the banner
  const touch = useRef(null);
  const navigate = useNavigate();
  const slides = movies.slice(0, 3);
  const count = slides.length;

  // Auto-advance. Using a timeout that restarts whenever the slide changes, so after a manual
  // swipe or click the new slide still gets its full time.
  useEffect(() => {
    if (count < 2 || paused) return undefined;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return undefined;
    const timer = setTimeout(() => setActive((i) => (i + 1) % count), AUTO_MS);
    return () => clearTimeout(timer);
  }, [active, paused, count]);

  const step = (d) => setActive((i) => (i + d + count) % count);

  const onTouchStart = (e) => {
    const t = e.touches[0];
    touch.current = { x: t.clientX, y: t.clientY };
    setPaused(true);
  };

  const onTouchEnd = (e) => {
    const start = touch.current;
    touch.current = null;
    setPaused(false);
    if (!start || count < 2) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - start.x;
    const dy = t.clientY - start.y;
    // a mostly sideways move counts as a swipe; mostly vertical is just the page scrolling
    if (Math.abs(dx) > SWIPE_PX && Math.abs(dx) > Math.abs(dy) * 1.5) step(dx < 0 ? 1 : -1);
  };

  const onTouchCancel = () => { touch.current = null; setPaused(false); };

  if (!count) return <section className="featured-section"><div className="featured-card" /></section>;
  const movie = slides[active % count];

  return (
    <section className="featured-section">
      <div
        className="featured-card"
        style={{ touchAction: "pan-y" }}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
        onTouchCancel={onTouchCancel}
      >
        <div className="featured-art" style={movie.backdrop ? { backgroundImage: `url(${movie.backdrop})` } : undefined} />
        <div className="featured-copy">
          {movie.poster && <img src={movie.poster} alt={`${movie.title} poster`} className="featured-poster" draggable={false} />}
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
        {count > 1 && (
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