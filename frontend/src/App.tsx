import { Link, Navigate, Route, Routes } from "react-router-dom";

import Alerts from "./pages/Alerts";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";

const App = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="text-lg font-semibold text-sky-300">
            Binance Analytics
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link className="hover:text-sky-300" to="/alerts">
              Alerts
            </Link>
            <Link className="hover:text-sky-300" to="/settings">
              Settings
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="border-t border-slate-800 bg-slate-900/80 py-4 text-center text-xs text-slate-500">
        © {new Date().getFullYear()} Binance Analytics Project. All rights reserved.
      </footer>
    </div>
  );
};

export default App;



