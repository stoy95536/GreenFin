import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { FarmerProvider } from "./context/FarmerContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import BankLayout from "./components/BankLayout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Experience from "./pages/Experience";
import Indicators from "./pages/Indicators";
import DataHealth from "./pages/DataHealth";
import GreenActions from "./pages/GreenActions";
import BankCases from "./pages/bank/BankCases";
import BankCaseDetail from "./pages/bank/BankCaseDetail";
import BankEvidence from "./pages/bank/BankEvidence";

/** Redirect to /login if not authenticated. */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuth();
  if (!isLoggedIn) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Farmer & Admin workflow */}
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/experience" element={<Experience />} />
        <Route path="/indicators" element={<Indicators />} />
        <Route path="/data-health" element={<DataHealth />} />
        <Route path="/green-actions" element={<GreenActions />} />
        {/* Admin sees the same pages + admin routes if needed */}
      </Route>

      {/* Bank workflow */}
      <Route
        element={
          <RequireAuth>
            <BankLayout />
          </RequireAuth>
        }
      >
        <Route path="/bank" element={<BankCases />} />
        <Route path="/bank/case/:farmerId" element={<BankCaseDetail />} />
        <Route path="/bank/case/:farmerId/evidence" element={<BankEvidence />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <FarmerProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </FarmerProvider>
    </AuthProvider>
  );
}

export default App;
