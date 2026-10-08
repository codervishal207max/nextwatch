import { FaSearch } from "react-icons/fa";

function SearchBar() {
  return (
    <div className="hidden md:flex items-center w-full max-w-md bg-slate-800/80 border border-slate-700 rounded-full px-4 py-2.5 transition-all duration-300 focus-within:border-cyan-400 focus-within:ring-2 focus-within:ring-cyan-400/20">
      
      <FaSearch className="text-slate-400 mr-3 shrink-0" />

      <input
        type="text"
        placeholder="Search movies..."
        className="bg-transparent outline-none text-white w-full placeholder:text-slate-400"
      />

    </div>
  );
}

export default SearchBar;