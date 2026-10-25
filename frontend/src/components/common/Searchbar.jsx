import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Search as SearchIcon } from "lucide-react";

// Navbar search box: results appear as you type (after a short pause) or when you press Enter.
export default function SearchBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const onSearchPage = location.pathname === "/search";
  const [text, setText] = useState(() =>
    onSearchPage ? new URLSearchParams(location.search).get("q") || "" : ""
  );
  const timer = useRef(null);

  useEffect(() => { if (!onSearchPage) setText(""); }, [onSearchPage]);
  useEffect(() => () => clearTimeout(timer.current), []);

  const go = (value) => {
    const q = value.trim();
    if (!q) return;
    navigate(`/search?q=${encodeURIComponent(q)}`, { replace: onSearchPage });
  };

  const onChange = (e) => {
    const value = e.target.value;
    setText(value);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => go(value), 400);
  };

  return (
    <form
      role="search"
      onSubmit={(e) => { e.preventDefault(); clearTimeout(timer.current); go(text); }}
      className="relative"
    >
      <SearchIcon size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        type="search"
        value={text}
        onChange={onChange}
        placeholder="Search movies"
        aria-label="Search movies"
        className="w-40 rounded-lg border border-red-900/60 bg-red-950/20 py-2 pl-9 pr-3 text-sm text-white outline-none placeholder:text-slate-400 focus-visible:border-cyan-400 md:w-64"
      />
    </form>
  );
}