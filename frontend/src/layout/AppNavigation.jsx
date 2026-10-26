import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { Bell, ChevronDown, Compass, Film, Heart, Home, LogOut, Menu, Search, Settings, X } from "lucide-react";
import { userAPI } from "../services/api";
import { logout } from "../utils/auth";

const navigation = [
  { label: "Home", path: "/", icon: Home },
  { label: "Movies", path: "/movies", icon: Film },
  { label: "My List", path: "/watchlist", icon: Heart },
  { label: "Discover", path: "/recommended", icon: Compass },
];

// Search box. On desktop (live) results appear as you type; on phones they appear when you press Enter.
function SearchBox({ className, live = false, onDone }) {
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
    if (onDone) onDone();
  };

  const onChange = (event) => {
    const value = event.target.value;
    setText(value);
    if (!live) return;
    clearTimeout(timer.current);
    timer.current = setTimeout(() => go(value), 400);
  };

  return (
    <form
      className={className}
      role="search"
      onSubmit={(event) => { event.preventDefault(); clearTimeout(timer.current); go(text); }}
    >
      <Search size={17} />
      <input
        value={text}
        onChange={onChange}
        placeholder="Search movies"
        aria-label="Search movies"
        enterKeyHint="search"
      />
    </form>
  );
}

function AppNavigation() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [noticeOpen, setNoticeOpen] = useState(false);
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => { userAPI.getMe().then((res) => setUser(res.data)).catch(() => {}); }, []);
  const initials = (user?.name || "?").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  const closeMenu = () => setMenuOpen(false);

  return <>
    <header className="dashboard-header">
      <Link className="brand" to="/" aria-label="NextWatch home"><span className="brand-mark">N</span><span>Next<span>Watch</span></span></Link>
      <button className="mobile-menu" onClick={() => setMenuOpen((open) => !open)} aria-label="Toggle navigation">{menuOpen ? <X size={21} /> : <Menu size={21} />}</button>
      <nav className={`top-navigation ${menuOpen ? "is-open" : ""}`} aria-label="Primary navigation">
        {navigation.map(({ label, path }) => <NavLink key={path} to={path} end={path === "/"} onClick={closeMenu}>{label}</NavLink>)}
        {/* these four are only visible inside the phone menu (the sidebar is hidden on phones) */}
        <SearchBox className="menu-search mobile-only" onDone={closeMenu} />
        <NavLink className="mobile-only" to="/settings" onClick={closeMenu}>Settings</NavLink>
        <NavLink className="mobile-only" to="/profile" onClick={closeMenu}>Profile</NavLink>
        <button type="button" className="mobile-only menu-logout" onClick={() => logout(navigate)}>Log out</button>
      </nav>
      <div className="header-actions">
        <SearchBox className="header-search" live />
        <div className="notification-wrap"><button className="icon-button" onClick={() => setNoticeOpen((open) => !open)} aria-label="Notifications"><Bell size={20} /><i /></button>{noticeOpen && <div className="notification-popover"><b>Notifications</b><p>New movies are waiting for you.</p></div>}</div>
        <Link to="/profile" className="profile-chip"><span className="avatar">{initials}</span><span className="profile-name">{user?.name || "Profile"}</span><ChevronDown size={15} /></Link>
        <button className="icon-button" onClick={() => logout(navigate)} aria-label="Log out" title="Log out"><LogOut size={20} /></button>
      </div>
    </header>
    <aside className="side-navigation" aria-label="Quick navigation">
      {navigation.map(({ label, path, icon: Icon }) => <NavLink key={path} to={path} end={path === "/"} title={label}><Icon size={20} /><span>{label}</span></NavLink>)}
      <div className="side-spacer" />
      <NavLink to="/settings" title="Settings"><Settings size={20} /><span>Settings</span></NavLink>
    </aside>
  </>;
}

export default AppNavigation;