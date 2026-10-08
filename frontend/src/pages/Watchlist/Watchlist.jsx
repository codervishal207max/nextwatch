import Navbar from "../../components/layout/Navbar";
import { FaHeart, FaTrash } from "react-icons/fa";

const DEMO_WATCHLIST = [
  { title: "Inception", year: "2010", rating: "8.8", genres: ["Sci-Fi", "Thriller"] },
  { title: "Dune", year: "2021", rating: "8.0", genres: ["Sci-Fi", "Adventure"] },
  { title: "Parasite", year: "2019", rating: "8.6", genres: ["Drama", "Thriller"] },
];

function Watchlist() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <div className="max-w-7xl mx-auto px-6 py-12">

        {/* Header */}
        <div className="flex items-center gap-3 mb-10">
          <FaHeart className="text-cyan-400 text-2xl" />
          <h1 className="text-3xl font-black text-white">My Watchlist</h1>
          <span className="ml-2 bg-cyan-400/15 text-cyan-400 text-sm font-semibold px-3 py-1 rounded-full">
            {DEMO_WATCHLIST.length} movies
          </span>
        </div>

        {DEMO_WATCHLIST.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <FaHeart className="text-slate-700 text-6xl mb-4" />
            <h2 className="text-xl font-bold text-slate-400">Your watchlist is empty</h2>
            <p className="text-slate-600 mt-2 text-sm">Add movies from the home page to see them here.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {DEMO_WATCHLIST.map((movie, i) => (
              <div key={i} className="group bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-cyan-400/40 transition-all duration-300">

                {/* Thumbnail */}
                <div className="h-48 bg-gradient-to-br from-indigo-900 to-purple-900 flex items-center justify-center text-5xl relative">
                  🎬
                  <button className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 w-8 h-8 bg-red-500/90 rounded-full flex items-center justify-center text-white hover:bg-red-400">
                    <FaTrash size={11} />
                  </button>
                </div>

                {/* Info */}
                <div className="p-4">
                  <h3 className="text-white font-bold text-base truncate">{movie.title}</h3>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-slate-500 text-xs">{movie.year}</span>
                    <span className="text-yellow-400 text-xs font-semibold">★ {movie.rating}</span>
                  </div>
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {movie.genres.map((g) => (
                      <span key={g} className="bg-slate-800 text-slate-400 text-xs px-2 py-0.5 rounded-full">{g}</span>
                    ))}
                  </div>
                </div>

              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}

export default Watchlist;
