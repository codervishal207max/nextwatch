import { Navigate } from "react-router-dom";

function ProtectedRoute({ children }) {
  if (!localStorage.getItem("nw_token")) return <Navigate to="/login" replace />;
  return children;
}

export default ProtectedRoute;
