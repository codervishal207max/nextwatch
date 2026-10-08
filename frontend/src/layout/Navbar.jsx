import { NavLink } from "react-router-dom";
import { Home, Film, Tv, List, Sparkles, Settings } from "lucide-react";
import { ROUTES } from "../routes/AppRoutes";

const navItems = [
  { label: "Home", icon: Home, path: ROUTES.HOME },
  { label: "Movies", icon: Film, path: "/movies" },
  { label: "TV Shows", icon: Tv, path: "/tv-shows" },
  { label: "My List", icon: List, path: ROUTES.WATCHLIST },
  { label: "New Releases", icon: Sparkles, path: "/new-releases" },
];

function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-20 bg-[var(--color-bg-secondary)] border-r border-white/5 flex flex-col items-center justify-between py-6 z-50">
      {/* Logo */}
      <div className="flex flex-col items-center gap-8 w-full">
        <div className="w-9 h-9 rounded-lg bg-[var(--color-accent)] flex items-center justify-center font-bold text-lg">
          N
        </div>

        {/* Nav Items */}
        <nav className="flex flex-col items-center gap-2 w-full">
          {navItems.map(({ label, icon: Icon, path }) => (
            <NavLink
              key={label}
              to={path}
              className={({ isActive }) =>
                `relative flex flex-col items-center gap-1 w-full py-3 text-xs transition-colors ${
                  isActive
                    ? "text-[var(--color-accent)]"
                    : "text-[var(--color-text-muted)] hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-[3px] bg-[var(--color-accent)] rounded-r-full" />
                  )}
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Settings pinned bottom */}
      <NavLink
        to="/settings"
        className={({ isActive }) =>
          `flex flex-col items-center gap-1 text-xs ${
            isActive ? "text-[var(--color-accent)]" : "text-[var(--color-text-muted)] hover:text-white"
          }`
        }
      >
        <Settings size={20} />
      </NavLink>
    </aside>
  );
}

export default Sidebar;