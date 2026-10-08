import { NavLink } from "react-router-dom";
import {
  Home,
  Film,
  Tv,
  Heart,
  Sparkles,
  Settings,
  WandSparkles,
} from "lucide-react";

const navItems = [
  {
    label: "Home",
    icon: Home,
    path: "/",
  },
  {
    label: "Movies",
    icon: Film,
    path: "/movies",
  },
  {
    label: "TV Shows",
    icon: Tv,
    path: "/tv-shows",
  },
  {
    label: "My List",
    icon: Heart,
    path: "/watchlist",
  },
  {
    label: "Recommended",
    icon: WandSparkles,
    path: "/recommended",
  },
  {
    label: "New Releases",
    icon: Sparkles,
    path: "/new-releases",
  },
];

function Sidebar() {
  return (
    <aside
      className="
        fixed left-0 top-0 z-50
        h-screen w-[92px]
        flex flex-col items-center
        border-r border-slate-800/70
        bg-slate-950/95
        backdrop-blur-xl
        py-5
      "
    >
      {/* Logo */}
      <NavLink
        to="/"
        className="
          mb-8
          flex h-10 w-10
          items-center justify-center
          rounded-xl
          bg-gradient-to-br from-cyan-400 to-cyan-600
          text-lg font-black
          text-slate-950
          shadow-lg shadow-cyan-500/20
          transition-all duration-200
          hover:scale-105
        "
      >
        N
      </NavLink>

      {/* Navigation */}
      <nav className="flex w-full flex-1 flex-col items-center gap-1">
        {navItems.map(({ label, icon: Icon, path }) => (
          <NavLink
            key={label}
            to={path}
            title={label}
            className={({ isActive }) =>
              `
              group relative
              flex w-full
              flex-col items-center justify-center
              gap-1.5
              py-3
              transition-all duration-200
              ${
                isActive
                  ? "text-cyan-400"
                  : "text-slate-500 hover:text-white"
              }
              `
            }
          >
            {({ isActive }) => (
              <>
                {/* Active left indicator */}
                {isActive && (
                  <span
                    className="
                      absolute left-0 top-1/2
                      h-9 w-[3px]
                      -translate-y-1/2
                      rounded-r-full
                      bg-cyan-400
                      shadow-lg shadow-cyan-400/50
                    "
                  />
                )}

                {/* Active background */}
                {isActive && (
                  <span
                    className="
                      absolute inset-x-2 inset-y-1
                      -z-10
                      rounded-xl
                      bg-cyan-400/10
                    "
                  />
                )}

                <Icon
                  size={21}
                  strokeWidth={isActive ? 2.5 : 1.8}
                  className="
                    transition-transform duration-200
                    group-hover:scale-110
                  "
                />

                <span className="text-[10px] font-medium">
                  {label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Settings */}
      <NavLink
        to="/settings"
        title="Settings"
        className={({ isActive }) =>
          `
          group relative
          flex w-full
          flex-col items-center
          gap-1.5
          py-3
          text-[10px]
          transition-all duration-200
          ${
            isActive
              ? "text-cyan-400"
              : "text-slate-500 hover:text-white"
          }
          `
        }
      >
        {({ isActive }) => (
          <>
            {isActive && (
              <span
                className="
                  absolute left-0 top-1/2
                  h-9 w-[3px]
                  -translate-y-1/2
                  rounded-r-full
                  bg-cyan-400
                  shadow-lg shadow-cyan-400/50
                "
              />
            )}

            {isActive && (
              <span
                className="
                  absolute inset-x-2 inset-y-1
                  -z-10
                  rounded-xl
                  bg-cyan-400/10
                "
              />
            )}

            <Settings
              size={21}
              strokeWidth={isActive ? 2.5 : 1.8}
              className="transition-transform duration-200 group-hover:rotate-45"
            />

            <span className="text-[10px] font-medium">
              Settings
            </span>
          </>
        )}
      </NavLink>
    </aside>
  );
}

export default Sidebar;