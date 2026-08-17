import { Link, Outlet, useLocation } from "react-router-dom";
import { FileText, Home, Leaf, Activity, Shield } from "lucide-react";
import { useFarmer } from "../context/FarmerContext";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: Home },
  { path: "/documents", label: "文件管理", icon: FileText },
  { path: "/experience", label: "經驗值", icon: Leaf },
  { path: "/indicators", label: "四大指標", icon: Activity },
  { path: "/data-health", label: "Data Health", icon: Shield },
];

export default function Layout() {
  const location = useLocation();
  const { currentFarmer, setFarmer, farmers } = useFarmer();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <Link to="/" className="flex items-center gap-2">
            <Leaf className="w-6 h-6 text-greenfin-600" />
            <span className="text-lg font-bold text-greenfin-800">GreenFin</span>
            <span className="text-xs text-gray-400 ml-2">DEMO</span>
          </Link>
          <div className="flex items-center gap-3">
            <select
              value={currentFarmer.id}
              onChange={(e) => {
                const f = farmers.find((x) => x.id === e.target.value);
                if (f) setFarmer(f);
              }}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white"
            >
              {farmers.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name} — {f.case_type}
                </option>
              ))}
            </select>
            <div className="text-sm text-gray-500 hidden md:block">
              {currentFarmer.farm}
            </div>
          </div>
        </div>
      </header>

      <div className="flex max-w-7xl mx-auto">
        {/* Sidebar */}
        <nav className="w-56 min-h-[calc(100vh-57px)] bg-white border-r border-gray-200 p-4">
          <ul className="space-y-1">
            {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
              const active = location.pathname === path;
              return (
                <li key={path}>
                  <Link
                    to={path}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      active
                        ? "bg-greenfin-50 text-greenfin-700 font-medium"
                        : "text-gray-600 hover:bg-gray-100"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Main content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
