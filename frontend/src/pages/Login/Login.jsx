// frontend/src/pages/Login/Login.jsx
//
// Routes (App.jsx / AppRoutes.jsx):
//   <Route path="/login"    element={<AuthPage initialMode="login" />} />
//   <Route path="/register" element={<AuthPage initialMode="register" />} />
//
// Optional display font — add to frontend/index.html <head>:
//   <link rel="preconnect" href="https://fonts.googleapis.com" />
//   <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700;800&display=swap" rel="stylesheet" />

import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { Eye, EyeOff, Lock, Mail, Play, User } from "lucide-react";
import API from "../../services/api";

// Plain axios on purpose: the shared `API` instance redirects to /login on any
// 401, which would reload this page and wipe the "wrong password" message.
const BASE_URL = API.defaults.baseURL;

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function loadGoogleScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) return resolve();
    const src = "https://accounts.google.com/gsi/client";
    let script = document.querySelector(`script[src="${src}"]`);
    if (!script) {
      script = Object.assign(document.createElement("script"), { src, async: true });
      document.head.appendChild(script);
    }
    script.addEventListener("load", resolve);
    script.addEventListener("error", reject);
  });
}

const display = "font-['Bricolage_Grotesque',system-ui,sans-serif]";
const emailOk = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

function passwordScore(pw) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

function readError(err) {
  if (!err.response) {
    return "Can't reach the server. Check that the backend is running on port 8000.";
  }
  const detail = err.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(" ");
  return "Something went wrong. Please try again.";
}

/* Left panel: shows the loop the product runs on, using a sample film. */
function ProductPanel() {
  return (
    <aside className="relative hidden flex-col justify-between overflow-hidden border-r border-slate-800/80 bg-slate-950 p-12 lg:flex">
      <div className="pointer-events-none absolute -left-24 top-24 h-80 w-80 rounded-full bg-cyan-500/10 blur-3xl" />

      <Link to="/" className="relative flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-cyan-600 shadow-lg shadow-cyan-500/30">
          <Play size={18} fill="white" className="ml-0.5 text-white" />
        </span>
        <span className={`${display} text-2xl font-extrabold tracking-tight text-white`}>NextWatch</span>
      </Link>

      <div className="relative max-w-md">
        <h2 className={`${display} text-5xl font-extrabold leading-[1.05] text-white`}>
          Finish a film tonight.
        </h2>
        <p className="mt-5 text-lg leading-relaxed text-slate-400">
          Every title runs 30 to 60 minutes. How long you watch, what you rate and what you like decides the next one we pick.
        </p>

        <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-xs text-slate-500">How your next film is picked</p>
          <div className="mt-3 flex items-baseline justify-between">
            <span className={`${display} text-lg font-bold text-white`}>Monsoon Shift</span>
            <span className="text-sm text-slate-400">52 min</span>
          </div>

          {/* runtime ruler: 30 to 60 minute window with a watch marker */}
          <div className="relative mt-4 h-2 rounded-full bg-slate-800" role="img" aria-label="Watched 42 of 52 minutes">
            <div className="h-2 rounded-full bg-cyan-400" style={{ width: "81%" }} />
          </div>
          <div className="mt-2 flex justify-between text-xs text-slate-500">
            <span>0</span>
            <span>42 min watched</span>
            <span>52</span>
          </div>

          <ul className="mt-4 flex flex-wrap gap-2 text-xs">
            <li className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">Watched 81%</li>
            <li className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">Rated 8 of 10</li>
            <li className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">Liked</li>
          </ul>

          <div className="mt-4 border-t border-slate-800 pt-4">
            <p className="text-xs text-slate-500">Up next for you</p>
            <p className="mt-1 flex items-baseline justify-between text-sm text-white">
              The Last Ferry <span className="text-slate-400">47 min</span>
            </p>
          </div>
        </div>
      </div>

      <p className="relative text-sm text-slate-600">Sample shown. Your picks start after your first film.</p>
    </aside>
  );
}

export default function AuthPage({ initialMode = "login" }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState(initialMode);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";
  const score = passwordScore(form.password);
  const googleBtn = useRef(null);

  // Google renders its own official button; we receive an ID token and trade it for our JWT.
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return undefined;
    let cancelled = false;
    loadGoogleScript()
      .then(() => {
        if (cancelled || !googleBtn.current) return;
        window.google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: handleGoogle });
        googleBtn.current.innerHTML = "";
        window.google.accounts.id.renderButton(googleBtn.current, {
          theme: "filled_black", size: "large", text: "continue_with", shape: "rectangular", width: 384,
        });
      })
      .catch(() => setFormError("Could not load Google sign-in. Check your connection."));
    return () => { cancelled = true; };
  }, []);

  function switchMode(next) {
    setMode(next);
    setErrors({});
    setFormError("");
  }

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: "" }));
  }

  function validate() {
    const errs = {};
    if (isRegister && form.name.trim().length < 2) errs.name = "Enter your name (at least 2 characters).";
    if (!emailOk(form.email.trim())) errs.email = "Enter a valid email address.";
    if (!form.password) errs.password = "Enter your password.";
    else if (isRegister && form.password.length < 8) errs.password = "Use at least 8 characters.";
    return errs;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length) return;

    setLoading(true);
    try {
      const email = form.email.trim();
      if (isRegister) {
        await axios.post(`${BASE_URL}/api/auth/register`, {
          name: form.name.trim(),
          email,
          password: form.password,
        });
      }
      const res = await axios.post(`${BASE_URL}/api/auth/login`, { email, password: form.password });
      localStorage.setItem("nw_token", res.data.access_token);
      localStorage.setItem("nw_auth", "true");
      navigate("/");
    } catch (err) {
      setFormError(readError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogle(response) {
    setFormError("");
    try {
      const res = await axios.post(`${BASE_URL}/api/auth/google`, { credential: response.credential });
      localStorage.setItem("nw_token", res.data.access_token);
      localStorage.setItem("nw_auth", "true");
      navigate("/");
    } catch (err) {
      setFormError(readError(err));
    }
  }

  const inputClass = (name) =>
    `w-full rounded-lg border bg-slate-900 py-3 pl-10 pr-3 text-sm text-white placeholder:text-slate-500 outline-none transition-colors focus-visible:border-cyan-400 focus-visible:ring-2 focus-visible:ring-cyan-400/30 ${
      errors[name] ? "border-red-500/70" : "border-slate-800"
    }`;

  return (
    <div className="grid min-h-screen bg-[#0b0f17] text-white lg:grid-cols-[1.05fr_1fr]">
      <ProductPanel />

      <main className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <Link to="/" className="mb-10 flex items-center gap-2 lg:hidden">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-cyan-600">
              <Play size={14} fill="white" className="ml-0.5 text-white" />
            </span>
            <span className={`${display} text-xl font-extrabold`}>NextWatch</span>
          </Link>

          <h1 className={`${display} text-3xl font-extrabold`}>
            {isRegister ? "Create your account" : "Welcome back"}
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            {isRegister ? "Start with one film. We learn from how you watch it." : "Log in to pick up your next film."}
          </p>

          <div role="tablist" aria-label="Account" className="mt-8 grid grid-cols-2 rounded-lg bg-slate-900 p-1">
            {[
              ["login", "Log in"],
              ["register", "Create account"],
            ].map(([key, label]) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={mode === key}
                onClick={() => switchMode(key)}
                className={`rounded-md py-2 text-sm font-semibold outline-none transition-colors focus-visible:ring-2 focus-visible:ring-cyan-400/50 ${
                  mode === key ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {GOOGLE_CLIENT_ID ? (
            <div ref={googleBtn} className="mt-6 flex justify-center" />
          ) : (
            <p className="mt-6 rounded-lg border border-slate-800 px-3 py-2.5 text-center text-sm text-slate-500">
              Google sign-in is not set up yet. Add VITE_GOOGLE_CLIENT_ID to frontend/.env.
            </p>
          )}

          <div className="my-6 flex items-center gap-3 text-xs text-slate-500">
            <span className="h-px flex-1 bg-slate-800" />
            or use your email
            <span className="h-px flex-1 bg-slate-800" />
          </div>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {isRegister && (
              <div>
                <label htmlFor="name" className="mb-1.5 block text-sm text-slate-300">Name</label>
                <div className="relative">
                  <User size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input id="name" name="name" autoComplete="name" value={form.name} onChange={handleChange}
                    placeholder="Your name" className={inputClass("name")} aria-invalid={!!errors.name} />
                </div>
                {errors.name && <p className="mt-1.5 text-xs text-red-400">{errors.name}</p>}
              </div>
            )}

            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm text-slate-300">Email</label>
              <div className="relative">
                <Mail size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input id="email" name="email" type="email" autoComplete="email" value={form.email} onChange={handleChange}
                  placeholder="you@example.com" className={inputClass("email")} aria-invalid={!!errors.email} />
              </div>
              {errors.email && <p className="mt-1.5 text-xs text-red-400">{errors.email}</p>}
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm text-slate-300">Password</label>
              <div className="relative">
                <Lock size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input id="password" name="password" type={showPass ? "text" : "password"}
                  autoComplete={isRegister ? "new-password" : "current-password"} value={form.password} onChange={handleChange}
                  placeholder={isRegister ? "At least 8 characters" : "Your password"}
                  className={`${inputClass("password")} pr-11`} aria-invalid={!!errors.password} />
                <button type="button" onClick={() => setShowPass((s) => !s)}
                  aria-label={showPass ? "Hide password" : "Show password"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-slate-500 outline-none hover:text-white focus-visible:ring-2 focus-visible:ring-cyan-400/50">
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="mt-1.5 text-xs text-red-400">{errors.password}</p>}

              {isRegister && form.password && (
                <div className="mt-2 flex items-center gap-3">
                  <div className="grid flex-1 grid-cols-3 gap-1.5" aria-hidden="true">
                    {[1, 2, 3].map((i) => (
                      <span key={i} className={`h-1 rounded-full ${i <= score ? "bg-cyan-400" : "bg-slate-800"}`} />
                    ))}
                  </div>
                  <span className="w-14 text-right text-xs text-slate-400">
                    {["Too short", "Okay", "Good", "Strong"][score]}
                  </span>
                </div>
              )}
            </div>

            {formError && (
              <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-sm text-red-300">
                {formError}
              </p>
            )}

            <button type="submit" disabled={loading}
              className="w-full rounded-lg bg-cyan-400 py-3 text-sm font-bold text-slate-950 outline-none transition-colors hover:bg-cyan-300 focus-visible:ring-2 focus-visible:ring-cyan-200 disabled:cursor-not-allowed disabled:opacity-60">
              {loading ? (isRegister ? "Creating account..." : "Logging in...") : isRegister ? "Create account" : "Log in"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-400">
            {isRegister ? "Already have an account?" : "New to NextWatch?"}{" "}
            <button type="button" onClick={() => switchMode(isRegister ? "login" : "register")}
              className="font-semibold text-cyan-400 outline-none hover:text-cyan-300 focus-visible:underline">
              {isRegister ? "Log in" : "Create an account"}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}
