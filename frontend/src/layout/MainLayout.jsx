import { Outlet } from "react-router-dom";
import AppNavigation from "./AppNavigation";

function MainLayout() {
  return (
    <div className="min-h-screen bg-[#0b0f17] text-white">
      <AppNavigation />
      <main className="app-content">
        <Outlet />
      </main>

    </div>
  );
}

export default MainLayout;
