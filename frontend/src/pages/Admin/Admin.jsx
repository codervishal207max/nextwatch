import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { adminAPI } from "../../services/api";

const when = (d) => (d ? new Date(d).toLocaleString() : "Never");
const dur = (m) => (m >= 60 ? `${(m / 60).toFixed(1)} h` : `${m} min`);
const SORTS = [["last_active", "Last active"], ["sessions", "Most sessions"], ["watch_time", "Most watch time"], ["joined", "Newest"]];

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value ?? "-"}</p>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="mb-5">
      <h3 className="mb-2 text-sm font-semibold text-slate-300">{title}</h3>
      {children}
    </section>
  );
}

function UserPanel({ id, onClose }) {
  const [d, setD] = useState(null);
  useEffect(() => { adminAPI.user(id).then((r) => setD(r.data)); }, [id]);

  return (
    <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-lg overflow-y-auto border-l border-slate-800 bg-[#0b0f17] p-6 shadow-2xl" aria-label="User details">
      <button onClick={onClose} aria-label="Close" className="absolute right-4 top-4 rounded-md p-1 text-slate-400 hover:text-white"><X size={20} /></button>
      {!d ? <p className="text-slate-400">Loading...</p> : (
        <>
          <h2 className="text-xl font-bold">{d.user.name}</h2>
          <p className="text-sm text-slate-400">{d.user.email} · joined {when(d.user.joined)}</p>
          <p className="mb-6 mt-2 text-sm text-slate-300">
            Shown {d.recommendations.shown} recommendations, watched {d.recommendations.watched} of them.
          </p>

          <Section title="Top genres by watch time">
            {d.top_genres.length ? <div className="flex flex-wrap gap-2">{d.top_genres.map((g) => (
              <span key={g.genre} className="rounded-full bg-slate-800 px-3 py-1 text-xs">{g.genre} · {dur(g.minutes)}</span>))}</div> : <p className="text-sm text-slate-500">No watching yet.</p>}
          </Section>

          <Section title="Recent sessions">
            {d.sessions.length ? d.sessions.map((s, i) => (
              <div key={i} className="mb-2 rounded-lg bg-slate-900 p-3 text-sm">
                <div className="flex justify-between"><span className="font-medium">{s.movie}</span><span className={s.completed ? "text-cyan-400" : "text-slate-400"}>{s.completion_pct}%</span></div>
                <p className="text-xs text-slate-500">{s.watched_minutes} of {s.runtime_minutes} min · {s.pauses} pauses · {s.seeks} skips · {when(s.started_at)}</p>
              </div>)) : <p className="text-sm text-slate-500">None.</p>}
          </Section>

          <Section title="Ratings and likes">
            <div className="flex flex-wrap gap-2 text-xs">
              {d.ratings.map((r, i) => <span key={`r${i}`} className="rounded-full bg-slate-800 px-3 py-1">{r.movie}: {r.rating}/10</span>)}
              {d.reactions.map((r, i) => <span key={`x${i}`} className="rounded-full bg-slate-800 px-3 py-1">{r.value === 1 ? "Liked" : "Disliked"} {r.movie}</span>)}
              {!d.ratings.length && !d.reactions.length && <p className="text-sm text-slate-500">None.</p>}
            </div>
          </Section>

          <Section title="Feedback">
            {d.feedback.length ? d.feedback.map((f, i) => (
              <div key={i} className="mb-2 rounded-lg bg-slate-900 p-3 text-sm">
                <p className="font-medium">{f.movie}</p>
                {f.tags.length > 0 && <p className="text-xs text-cyan-400">{f.tags.map((t) => t.replace(/_/g, " ")).join(", ")}</p>}
                {f.comment && <p className="mt-1 text-slate-300">{f.comment}</p>}
              </div>)) : <p className="text-sm text-slate-500">None.</p>}
          </Section>
        </>
      )}
    </aside>
  );
}

export default function Admin() {
  const [overview, setOverview] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [users, setUsers] = useState({ total: 0, users: [] });
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("last_active");
  const [selected, setSelected] = useState(null);
  const [forbidden, setForbidden] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([adminAPI.overview(), adminAPI.recommendations()])
      .then(([o, r]) => { setOverview(o.data); setStrategies(r.data); })
      .catch((e) => (e.response?.status === 403 ? setForbidden(true) : setError("Could not load admin data.")));
  }, []);

  useEffect(() => {
    if (forbidden) return undefined;
    const t = setTimeout(() => adminAPI.users({ search, sort, limit: 100 }).then((r) => setUsers(r.data)).catch(() => {}), 300);
    return () => clearTimeout(t);
  }, [search, sort, forbidden]);

  if (forbidden) return <p className="p-10 text-center text-slate-300">You don't have admin access. Add your email to ADMIN_EMAILS in backend/.env.</p>;
  if (error) return <p className="p-10 text-red-400">{error}</p>;
  const max = Math.max(1, ...(overview?.daily_sessions.map((d) => d.sessions) ?? [1]));

  return (
    <div className="mx-auto max-w-6xl px-5 py-8 text-white">
      <h1 className="mb-6 text-3xl font-bold">Admin</h1>

      {overview && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Users" value={overview.users} />
            <Stat label="New this week" value={overview.new_users_7d} />
            <Stat label="Active this week" value={overview.active_users_7d} />
            <Stat label="Watch time" value={`${overview.watch_hours} h`} />
            <Stat label="Sessions" value={overview.sessions} />
            <Stat label="Avg completion" value={`${overview.avg_completion_pct}%`} />
            <Stat label="Likes / dislikes" value={`${overview.likes} / ${overview.dislikes}`} />
            <Stat label="Avg rating" value={overview.avg_rating ? `${overview.avg_rating} / 10` : "-"} />
          </div>

          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-4">
            <p className="mb-3 text-sm text-slate-400">Sessions, last 14 days</p>
            <div className="flex h-28 items-end gap-1.5" role="img" aria-label="Sessions per day for the last 14 days">
              {overview.daily_sessions.map((d) => (
                <div key={d.day} title={`${d.day}: ${d.sessions}`} className="flex-1 rounded-t bg-cyan-400/80" style={{ height: `${Math.max(3, (d.sessions / max) * 100)}%` }} />
              ))}
            </div>
          </div>

          <div className="mt-6 overflow-x-auto rounded-xl border border-slate-800">
            <p className="border-b border-slate-800 bg-slate-900 px-4 py-3 text-sm text-slate-400">Recommendation strategies (does the model beat popularity?)</p>
            <table className="w-full text-left text-sm">
              <thead className="text-slate-400"><tr><th className="px-4 py-2">Strategy</th><th>Shown</th><th>Started</th><th>Start rate</th><th>Avg completion</th></tr></thead>
              <tbody>{strategies.length ? strategies.map((s) => (
                <tr key={s.strategy} className="border-t border-slate-800">
                  <td className="px-4 py-2">{s.strategy}</td><td>{s.shown}</td><td>{s.started}</td><td>{s.start_rate_pct}%</td><td>{s.avg_completion_pct != null ? `${s.avg_completion_pct}%` : "-"}</td>
                </tr>)) : <tr><td className="px-4 py-3 text-slate-500" colSpan="5">Nothing shown yet.</td></tr>}</tbody>
            </table>
          </div>
        </>
      )}

      <div className="mb-3 mt-8 flex flex-wrap items-center gap-3">
        <h2 className="mr-auto text-xl font-bold">Users ({users.total})</h2>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name or email"
          className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm outline-none focus-visible:border-cyan-400" />
        <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort users"
          className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm">
          {SORTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr><th className="px-4 py-3">User</th><th>Sessions</th><th>Watch time</th><th>Completion</th><th>Rating</th><th>Likes</th><th>Last active</th></tr>
          </thead>
          <tbody>
            {users.users.map((u) => (
              <tr key={u.id} tabIndex={0} onClick={() => setSelected(u.id)} onKeyDown={(e) => e.key === "Enter" && setSelected(u.id)}
                className="cursor-pointer border-t border-slate-800 hover:bg-slate-900/70 focus-visible:bg-slate-900">
                <td className="px-4 py-3"><p className="font-medium">{u.name}</p><p className="text-xs text-slate-500">{u.email}</p></td>
                <td>{u.sessions}</td><td>{dur(u.watch_minutes)}</td>
                <td>{u.avg_completion_pct != null ? `${u.avg_completion_pct}%` : "-"}</td>
                <td>{u.avg_rating ?? "-"}</td><td>{u.likes} / {u.dislikes}</td>
                <td className="text-slate-400">{when(u.last_active)}</td>
              </tr>
            ))}
            {!users.users.length && <tr><td className="px-4 py-6 text-slate-500" colSpan="7">No users found.</td></tr>}
          </tbody>
        </table>
      </div>

      {selected && <UserPanel id={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}