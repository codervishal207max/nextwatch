import SearchBar from "../components/common/Searchbar";
import { useEffect, useState } from "react";
import { userAPI } from "../services/api";
import { logout } from "../utils/auth";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Bell, ChevronDown, Compass, Film, Heart, Home, LogOut, Menu, Search, Settings, Tv, X } from "lucide-react";

const navigation = [
  { label: "Home", path: "/", icon: Home },
  { label: "Movies", path: "/movies", icon: Film },
  { label: "TV Shows", path: "/tv-shows", icon: Tv },
  { label: "My List", path: "/watchlist", icon: Heart },
  { label: "Discover", path: "/recommended", icon: Compass },
];

function AppNavigation() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [noticeOpen, setNoticeOpen] = useState(false);
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  useEffect(() => { userAPI.getMe().then((res) => setUser(res.data)).catch(() => {}); }, []);
  const initials = (user?.name || "?").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  const submitSearch = (event) => {
    event.preventDefault();
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    setMenuOpen(false);
  };

  return <>
    <header className="dashboard-header">
      <Link className="brand" to="/" aria-label="NextWatch home"><span className="brand-mark">N</span><span>Next<span>Watch</span></span></Link>
      <button className="mobile-menu" onClick={() => setMenuOpen((open) => !open)} aria-label="Toggle navigation">{menuOpen ? <X size={21} /> : <Menu size={21} />}</button>
      <nav className={`top-navigation ${menuOpen ? "is-open" : ""}`} aria-label="Primary navigation">
        {navigation.map(({ label, path }) => <NavLink key={path} to={path} end={path === "/"} onClick={() => setMenuOpen(false)}>{label}</NavLink>)}
      </nav>
      <div className="header-actions">
        <form className="header-search" onSubmit={submitSearch}><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} SearchBar="Search" aria-label="Search movies" /></form>
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