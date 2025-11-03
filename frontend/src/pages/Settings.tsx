import { useEffect, useState } from "react";

type FrontendSettings = {
  defaultPrimarySymbol: string;
  defaultSecondarySymbol: string;
  defaultTimeframe: string;
  defaultWindow: number;
};

const DEFAULT_SETTINGS: FrontendSettings = {
  defaultPrimarySymbol: "btcusdt",
  defaultSecondarySymbol: "ethusdt",
  defaultTimeframe: "1s",
  defaultWindow: 300,
};

const SYMBOL_OPTIONS = ["btcusdt", "ethusdt", "bnbusdt", "adausdt", "solusdt", "xrpusdt"];
const TIMEFRAME_OPTIONS = [
  { value: "tick", label: "Tick" },
  { value: "1s", label: "1 Second" },
  { value: "1m", label: "1 Minute" },
  { value: "5m", label: "5 Minutes" },
];

const Settings = () => {
  const [settings, setSettings] = useState<FrontendSettings>(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("frontend_settings");
    if (stored) {
      try {
        setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(stored) });
      } catch {
        // Invalid JSON, use defaults
      }
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem("frontend_settings", JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    localStorage.removeItem("frontend_settings");
    setSaved(false);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="text-lg font-semibold text-slate-200">Settings</h2>
        <p className="mt-2 text-sm text-slate-400">
          Configure frontend preferences and view backend configuration details.
        </p>
      </div>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Frontend Preferences</h3>
          <div className="mt-4 space-y-4 text-sm">
            <label className="flex flex-col gap-1 text-slate-300">
              Default Primary Symbol
              <select
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={settings.defaultPrimarySymbol}
                onChange={(e) => setSettings({ ...settings, defaultPrimarySymbol: e.target.value })}
              >
                {SYMBOL_OPTIONS.map((sym) => (
                  <option key={sym} value={sym}>
                    {sym.toUpperCase()}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-slate-300">
              Default Secondary Symbol
              <select
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={settings.defaultSecondarySymbol}
                onChange={(e) => setSettings({ ...settings, defaultSecondarySymbol: e.target.value })}
              >
                {SYMBOL_OPTIONS.map((sym) => (
                  <option key={sym} value={sym}>
                    {sym.toUpperCase()}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-slate-300">
              Default Timeframe
              <select
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={settings.defaultTimeframe}
                onChange={(e) => setSettings({ ...settings, defaultTimeframe: e.target.value })}
              >
                {TIMEFRAME_OPTIONS.map((tf) => (
                  <option key={tf.value} value={tf.value}>
                    {tf.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-slate-300">
              Default Analytics Window
              <input
                type="number"
                min={10}
                max={5000}
                step={10}
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={settings.defaultWindow}
                onChange={(e) => setSettings({ ...settings, defaultWindow: Number(e.target.value) })}
              />
              <span className="text-xs text-slate-400">Number of periods for rolling metrics</span>
            </label>

            <div className="flex gap-3 pt-2">
              <button
                onClick={handleSave}
                className="flex-1 rounded-lg bg-sky-500 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
              >
                {saved ? "✓ Saved" : "Save Preferences"}
              </button>
              <button
                onClick={handleReset}
                className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 transition hover:bg-slate-700"
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Backend Configuration</h3>
          <div className="mt-4 space-y-3 text-sm text-slate-300">
            <div className="space-y-2">
              <p className="text-xs text-slate-400">Backend settings are configured via environment variables.</p>
              <p className="text-xs text-slate-400">
                Create a <code className="rounded bg-slate-800 px-1.5 py-0.5 text-sky-300">.env</code> file in the repo
                root based on <code className="rounded bg-slate-800 px-1.5 py-0.5 text-sky-300">env.example</code>.
              </p>
            </div>

            <div className="mt-4 space-y-2 rounded-lg border border-slate-800 bg-slate-900/70 p-3">
              <h4 className="text-xs font-semibold uppercase text-slate-400">Key Settings</h4>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Default Symbols:</span>
                  <span className="text-slate-200">btcusdt, ethusdt</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Tick Buffer:</span>
                  <span className="text-slate-200">3,600 ticks</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">DB Flush Interval:</span>
                  <span className="text-slate-200">2.0s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Analytics Window:</span>
                  <span className="text-slate-200">300 periods</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">WS Broadcast:</span>
                  <span className="text-slate-200">0.5s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Alert Eval:</span>
                  <span className="text-slate-200">1.0s</span>
                </div>
              </div>
            </div>

            <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/70 p-3">
              <h4 className="mb-2 text-xs font-semibold uppercase text-slate-400">API Endpoints</h4>
              <div className="space-y-1 text-xs text-slate-300">
                <div>
                  <code className="rounded bg-slate-800 px-1.5 py-0.5 text-sky-300">GET /api/health</code> — Health check
                </div>
                <div>
                  <code className="rounded bg-slate-800 px-1.5 py-0.5 text-sky-300">GET /api/data/history</code> —
                  Historical data
                </div>
                <div>
                  <code className="rounded bg-slate-800 px-1.5 py-0.5 text-sky-300">POST /api/analytics/snapshot</code>{" "}
                  — Analytics
                </div>
                <div>
                  <code className="rounded bg-slate-800 px-1.5 py-0.5 text-sky-300">GET /api/ws/live</code> — Live
                  stream
                </div>
                <div>
                  <code className="rounded bg-slate-800 px-1.5 py-0.5 text-sky-300">POST /api/alerts</code> — Alert
                  management
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Application Information</h3>
        <div className="mt-4 space-y-2 text-sm text-slate-300">
          <div className="flex justify-between">
            <span className="text-slate-400">Application Name:</span>
            <span className="text-slate-200">Binance Analytics</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Backend:</span>
            <span className="text-slate-200">FastAPI (Port 8000)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Frontend:</span>
            <span className="text-slate-200">React + Vite (Port 5173)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Storage:</span>
            <span className="text-slate-200">SQLite</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Data Source:</span>
            <span className="text-slate-200">Binance WebSocket</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Settings;

