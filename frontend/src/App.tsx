import { BrowserRouter, Routes, Route } from "react-router-dom";
import { FarmerProvider } from "./context/FarmerContext";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Experience from "./pages/Experience";
import Indicators from "./pages/Indicators";
import DataHealth from "./pages/DataHealth";

function App() {
  return (
    <FarmerProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/experience" element={<Experience />} />
            <Route path="/indicators" element={<Indicators />} />
            <Route path="/data-health" element={<DataHealth />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </FarmerProvider>
  );
}

export default App;
