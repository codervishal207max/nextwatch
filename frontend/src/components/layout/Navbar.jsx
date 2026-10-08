import { useState, useRef, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  FaSearch,
  FaHeart,
  FaBell,
  FaUser,
  FaTimes,
  FaClock,
  FaFire,
} from "react-icons/fa";

const ALL_MOVIES = [
  {
    title: "Inception",
    year: "2010",
    rating: "8.8",
    genres: ["Sci-Fi", "Thriller"],
  },
  {
    title: "Interstellar",
    year: "2014",
    rating: "8.7",
    genres: ["Sci-Fi", "Drama"],
  },
  {
    title: "The Dark Knight",
    year: "2008",
    rating: "9.0",
    genres: ["Action", "Crime"],
  },
  {
    title: "Parasite",
    year: "2019",
    rating: "8.6",
    genres: ["Drama", "Thriller"],
  },
  {
    title: "Oppenheimer",
    year: "2023",
    rating: "8.5",
    genres: ["Drama", "History"],
  },
  {
    title: "Dune",
    year: "2021",
    rating: "8.0",
    genres: ["Sci-Fi", "Adventure"],
  },
  {
    title: "The Matrix",
    year: "1999",
    rating: "8.7",
    genres: ["Sci-Fi", "Action"],
  },
  {
    title: "John Wick",
    year: "2014",
    rating: "7.4",
    genres: ["Action", "Thriller"],
  },
  {
    title: "The Hangover",
    year: "2009",
    rating: "7.7",
    genres: ["Comedy"],
  },
  {
    title: "Spirited Away",
    year: "2001",
    rating: "8.6",
    genres: ["Animation"],
  },
  {
    title: "Get Out",
    year: "2017",
    rating: "7.7",
    genres: ["Horror", "Thriller"],
  },
  {
    title: "La La Land",
    year: "2016",
    rating: "8.0",
    genres: ["Romance", "Drama"],
  },
];

const TRENDING_SEARCHES = [
  "Interstellar",
  "Inception",
  "Dune",
  "Parasite",
];

const NOTIFICATIONS = [
  {
    icon: "🎬",
    text: "Inception is trending today!",
    time: "2m ago",
  },
  {
    icon: "⭐",
    text: "New top rated: Oppenheimer",
    time: "1h ago",
  },
  {
    icon: "🤖",
    text: "New recommendation ready for you",
    time: "3h ago",
  },
  {
    icon: "🔥",
    text: "Dune: Part Two added to catalog",
    time: "1d ago",
  },
];

function Navbar() {
  const { pathname } = useLocation();

  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const [showNotif, setShowNotif] = useState(false);

  const searchRef = useRef(null);

  const results =
    query.trim().length > 0
      ? ALL_MOVIES.filter(
          (movie) =>
            movie.title
              .toLowerCase()
              .includes(query.toLowerCase()) ||
            movie.genres.some((genre) =>
              genre.toLowerCase().includes(query.toLowerCase())
            )
        ).slice(0, 6)
      : [];

  useEffect(() => {
    const handleClick = (event) => {
      if (
        searchRef.current &&
        !searchRef.current.contains(event.target)
      ) {
        setFocused(false);
      }
    };

    document.addEventListener("mousedown", handleClick);

    return () => {
      document.removeEventListener("mousedown", handleClick);
    };
  }, []);

  return (
    <nav className="sticky top-0 z-40 h-16 border-b border-slate-800 bg-[#0b0f17]/95 backdrop-blur-xl">
      <div className="h-full px-6 flex items-center justify-between gap-6">

        {/* Search */}
        <div
          ref={searchRef}
          className="relative w-full max-w-xl"
        >
          <div
            className={`flex items-center rounded-xl border px-4 py-2.5 transition-all ${
              focused
                ? "border-cyan-500/60 bg-slate-900 ring-1 ring-cyan-500/20"
                : "border-slate-800 bg-slate-900/80 hover:border-slate-700"
            }`}
          >
            <FaSearch
              size={14}
              className={`mr-3 ${
                focused ? "text-cyan-400" : "text-slate-500"
              }`}
            />

            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              placeholder="Search movies..."
              className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
            />

            {query && (
              <button
                onClick={() => setQuery("")}
                className="text-slate-500 hover:text-white"
              >
                <FaTimes size={12} />
              </button>
            )}
          </div>

          {/* Search Dropdown */}
          {focused && (
            <div className="absolute left-0 right-0 top-14 z-50 overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">

              {results.length > 0 ? (
                <>
                  <div className="px-4 pt-3 pb-2 text-xs font-semibold uppercase text-slate-500">
                    Results
                  </div>

                  {results.map((movie) => (
                    <div
                      key={movie.title}
                      onClick={() => {
                        setQuery(movie.title);
                        setFocused(false);
                      }}
                      className="flex cursor-pointer items-center gap-3 px-4 py-3 hover:bg-slate-800"
                    >
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-800">
                        🎬
                      </div>

                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-white">
                          {movie.title}
                        </p>

                        <p className="text-xs text-slate-500">
                          {movie.year} · {movie.genres[0]}
                        </p>
                      </div>

                      <span className="text-xs font-semibold text-yellow-400">
                        ★ {movie.rating}
                      </span>
                    </div>
                  ))}
                </>
              ) : query.trim() ? (
                <div className="px-4 py-8 text-center">
                  <p className="text-sm text-slate-400">
                    No results for{" "}
                    <span className="text-white">
                      "{query}"
                    </span>
                  </p>

                  <p className="mt-1 text-xs text-slate-600">
                    Try a different keyword
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-2 px-4 pt-3 pb-2 text-xs font-semibold uppercase text-slate-500">
                    <FaFire
                      size={11}
                      className="text-orange-400"
                    />
                    Trending Searches
                  </div>

                  {TRENDING_SEARCHES.map((item) => (
                    <div
                      key={item}
                      onClick={() => setQuery(item)}
                      className="flex cursor-pointer items-center gap-3 px-4 py-3 hover:bg-slate-800"
                    >
                      <FaClock
                        size={12}
                        className="text-slate-600"
                      />

                      <span className="text-sm text-slate-300">
                        {item}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>

        {/* Right Side */}
        <div className="flex shrink-0 items-center gap-2">

          {/* My List */}
          <Link
            to="/watchlist"
            title="My List"
            className={`flex items-center gap-2 rounded-lg px-3 py-2 transition ${
              pathname === "/watchlist"
                ? "bg-cyan-400/15 text-cyan-400"
                : "text-slate-400 hover:bg-slate-800 hover:text-cyan-400"
            }`}
          >
            <FaHeart size={17} />

            <span className="hidden lg:inline text-sm">
              My List
            </span>
          </Link>

          {/* Notification */}
          <div className="relative">
            <button
              title="Notifications"
              onClick={() => setShowNotif((prev) => !prev)}
              className={`relative rounded-lg px-3 py-2 transition ${
                showNotif
                  ? "bg-cyan-400/15 text-cyan-400"
                  : "text-slate-400 hover:bg-slate-800 hover:text-cyan-400"
              }`}
            >
              <FaBell size={17} />

              <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
            </button>

            {showNotif && (
              <div className="absolute right-0 top-12 z-50 w-80 overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">

                <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                  <span className="text-sm font-bold text-white">
                    Notifications
                  </span>

                  <button
                    onClick={() => setShowNotif(false)}
                    className="text-slate-500 hover:text-white"
                  >
                    <FaTimes size={13} />
                  </button>
                </div>

                <div className="divide-y divide-slate-800">
                  {NOTIFICATIONS.map((notification, index) => (
                    <div
                      key={index}
                      className="flex cursor-pointer items-start gap-3 px-4 py-3 hover:bg-slate-800/60"
                    >
                      <span className="text-xl">
                        {notification.icon}
                      </span>

                      <div>
                        <p className="text-sm text-slate-300">
                          {notification.text}
                        </p>

                        <span className="text-xs text-slate-600">
                          {notification.time}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t border-slate-800 px-4 py-3 text-center">
                  <button className="text-xs text-cyan-400 hover:text-cyan-300">
                    Mark all as read
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Profile */}
          <Link
            to="/profile"
            title="Profile"
            className={`rounded-lg p-1.5 transition ${
              pathname === "/profile"
                ? "ring-2 ring-cyan-400"
                : "hover:ring-2 hover:ring-slate-600"
            }`}
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 text-white">
              <FaUser size={13} />
            </div>
          </Link>

        </div>
      </div>
    </nav>
  );
}

export default Navbar;