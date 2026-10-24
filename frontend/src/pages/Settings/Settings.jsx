import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { userAPI } from "../../services/api";
import { logout } from "../../utils/auth";

export default function Settings() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => { userAPI.getMe().then((r) => setUser(r.data)).catch(() => {}); }, []);

  return (
    <div className="mx-auto max-w-2xl px-6 py-8 text-white">
      <h1 className="mb-6 text-3xl font-bold">Settings</h1>

      <section className="mb-5 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-3 text-lg font-semibold">Account</h2>
        <p className="text-sm text-slate-400">Name</p>
        <p className="mb-3">{user?.name || "-"}</p>
        <p className="text-sm text-slate-400">Email</p>
        <p className="mb-5">{user?.email || "-"}</p>
        <button onClick={() => logout(navigate)}
          className="rounded-lg border border-slate-700 px-5 py-2 text-sm font-semibold hover:border-cyan-400">
          Log out
        </button>
      </section>

      <section className="mb-5 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-2 text-lg font-semibold">Your data</h2>
        <p className="text-sm leading-relaxed text-slate-400">
          NextWatch records how much of each film you watch, your ratings, likes and feedback. It uses them only to
          choose the next film for you.
        </p>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-2 text-lg font-semibold">About the films</h2>
        <p className="text-sm leading-relaxed text-slate-400">
          Videos are embedded from YouTube and are used under their creators' Creative Commons (CC BY) licenses
          or with the uploader's embedding permission. Credit to the creator is shown on each film page.
        </p>
      </section>
    </div>
  );
}