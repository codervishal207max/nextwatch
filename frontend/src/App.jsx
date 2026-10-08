import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import ProtectedRoute from "./components/common/ProtectedRoute";
import MainLayout from "./layout/MainLayout";
import Home from "./pages/Home/Home";
import Login from "./pages/Login/Login";
import MovieDetails from "./pages/MovieDetails/MovieDetails";
import Profile from "./pages/Profile/Profile";
import Watch from "./pages/Watch/Watch";
import Admin from "./pages/Admin/Admin";

function Soon({ title }) {
  return (
    <div className="flex min-h-[70vh] items-center justify-center text-center text-white">
      <div>
        <h1 className="mb-2 text-3xl font-bold">{title}</h1>
        <p className="text-gray-400">This section is coming next.</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login initialMode="login" />} />
        <Route path="/register" element={<Login initialMode="register" />} />

        <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
          <Route path="/" element={<Home />} />
          <Route path="/movie/:id" element={<MovieDetails />} />
          <Route path="/watch/:id" element={<Watch />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/movies" element={<Soon title="Movies" />} />
          <Route path="/tv-shows" element={<Soon title="TV Shows" />} />
          <Route path="/watchlist" element={<Soon title="My List" />} />
          <Route path="/recommended" element={<Soon title="Discover" />} />
          <Route path="/settings" element={<Soon title="Settings" />} />
          <Route path="/admin" element={<Admin />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
