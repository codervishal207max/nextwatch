const GENRES = [
  { label: "All", icon: "🎬" },
  { label: "Action", icon: "💥" },
  { label: "Sci-Fi", icon: "🚀" },
  { label: "Drama", icon: "🎭" },
  { label: "Thriller", icon: "🔪" },
  { label: "Comedy", icon: "😂" },
  { label: "Horror", icon: "👻" },
  { label: "Romance", icon: "❤️" },
  { label: "Animation", icon: "🎨" },
  { label: "Documentary", icon: "📽️" },
];

function GenreList({ active = "All", onSelect }) {
  return (
    <div className="max-w-7xl mx-auto px-6 py-6">
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide pb-1">
        {GENRES.map((genre) => (
          <button
            key={genre.label}
            onClick={() => onSelect?.(genre.label)}
            className={`shrink-0 flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 border
              ${active === genre.label
                ? "bg-cyan-400 text-slate-950 border-cyan-400 shadow-lg shadow-cyan-400/20"
                : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-600 hover:text-white"
              }`}
          >
            <span className="text-base leading-none">{genre.icon}</span>
            <span>{genre.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default GenreList;
