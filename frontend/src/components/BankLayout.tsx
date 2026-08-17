import { Link, Outlet } from "react-router-dom";
import { Building2, Home } from "lucide-react";

export default function BankLayout() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <Link to="/bank" className="flex items-center gap-2">
            <Building2 className="w-6 h-6 text-blue-600" />
            <span className="text-lg font-bold text-gray-800">GreenFin</span>
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full ml-2">銀行端</span>
            <span className="text-xs text-gray-400 ml-1">DEMO</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm text-gray-500 hover:text-greenfin-600 flex items-center gap-1">
              <Home className="w-3 h-3" /> 小農端
            </Link>
            <span className="text-sm text-gray-500">台新銀行審查員</span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-5xl mx-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
