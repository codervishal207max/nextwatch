import { Navigate } from "react-router-dom";

// Login and register pages are only for people who are not signed in yet.
export default function PublicRoute({ children }) {
  return localStorage.getItem("nw_token") ? <Navigate to="/" replace /> : children;
}