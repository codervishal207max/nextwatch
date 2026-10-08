import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaUser, FaHeart, FaStar, FaFilm } from "react-icons/fa";
import { userAPI } from "../../services/api";
import { logout } from "../../utils/auth";

const since = (d) => (d ? new Date(d).toLocaleDateString("en-US", { month: "long", year: "numeric" }) : "");

function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([userAPI.getMe(), userAPI.getStats()])
      .then(([me, st]) => { setUser(me.data); setStats(st.data); })
      .catch(() => setError("Could not load your profile."));
  }, []);

  if (error) return <p className="p-10 text-red-400">{error}</p>;
  if (!user || !stats) return <p className="p-10 text-slate-400">Loading...</p>;

  const tiles = [
    { icon: <FaHeart className="text-cyan-400 text-2xl shrink-0" />, title: "My Watchlist", text: `${stats.watchlist} movies saved` },
    { icon: <FaStar className="text-yellow-400 text-2xl shrink-0" />, title: "My Ratings", text: `${stats.ratings} movies rated` },
    { icon: <FaFilm className="text-cyan-400 text-2xl shrink-0" />, title: "Watch History", text: `${stats.watched} movies watched` },
  ];

  return (
    <div className="min-h-full bg-slate-950 text-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-10">
          <div className="w-24 h-24 rounded-full bg-cyan-500 flex items-center justify-center text-white shrink-0 ring-4 ring-cyan-400/30">
            <FaUser size={36} />
          </div>

          <div className="text-center sm:text-left">
            <h1 className="text-2xl font-black text-white">{user.name}</h1>
            <p className="text-slate-400 text-sm mt-1">{user.email}</p>
            <p className="text-slate-600 text-xs mt-2">Member since {since(user.created_at)}</p>
            <button onClick={() => logout(navigate)}
              className="mt-4 border border-slate-700 hover:border-cyan-400 text-slate-200 font-semibold px-5 py-2 rounded-lg text-sm transition-all duration-200">
              Log out
            </button>
          </div>

          <div className="sm:ml-auto flex gap-6 text-center">
            {[["Watched", stats.watched], ["Watchlist", stats.watchlist], ["Rated", stats.ratings]].map(([label, n]) => (
              <div key={label}>
                <div className="text-2xl font-black text-cyan-400">{n}</div>
                <div className="text-slate-500 text-xs mt-1">{label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {tiles.map((t) => (
            <div key={t.title} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
              {t.icon}
              <div>
                <div className="text-white font-bold">{t.title}</div>
                <div className="text-slate-500 text-xs mt-0.5">{t.text}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Profile;