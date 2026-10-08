import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// Auto attach JWT token to every request
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("nw_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto logout on 401
API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("nw_auth");
      localStorage.removeItem("nw_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const movieAPI = {
  getAll:           () => API.get("/api/movies/"),
  getTrending:       () => API.get("/api/movies/trending"),
  getTopRated:       () => API.get("/api/movies/top-rated"),
  getByGenre:        (genre) => API.get(`/api/movies/?genre=${genre}`),
  getById:           (id) => API.get(`/api/movies/${id}`),
  search:            (q) => API.get(`/api/movies/search?q=${q}`),
};

export const recommendAPI = {
  getNext: (limit = 5) => API.get(`/api/recommendations/next?limit=${limit}`),
};

// Signals the recommender learns from: watch time, rating, like, feedback
export const trackingAPI = {
  start:    (body)       => API.post("/api/sessions", body),
  update:   (id, body)   => API.patch(`/api/sessions/${id}`, body),
  rate:     (movieId, rating) => API.put(`/api/movies/${movieId}/rating`, { rating }),
  react:    (movieId, value)  => API.put(`/api/movies/${movieId}/reaction`, { value }),
  feedback: (movieId, body)   => API.post(`/api/movies/${movieId}/feedback`, body),
};

export const watchlistAPI = {
  get:    ()        => API.get("/api/watchlist/"),
  add:    (movieId) => API.post(`/api/watchlist/${movieId}`),
  remove: (movieId) => API.delete(`/api/watchlist/${movieId}`),
};

export const userAPI = {
  getMe: () => API.get("/api/users/me"),
};

export const adminAPI = {
  overview:        () => API.get("/api/admin/overview"),
  users:           (params) => API.get("/api/admin/users", { params }),
  user:            (id) => API.get(`/api/admin/users/${id}`),
  recommendations: () => API.get("/api/admin/recommendations"),
};

export default API;
