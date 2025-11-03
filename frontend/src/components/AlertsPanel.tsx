import { FormEvent, useState } from "react";

import type { Alert, AlertEvent } from "@/types";

type CreateAlertPayload = {
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  window?: number;
};

type AlertsPanelProps = {
  alerts: Alert[];
  history: AlertEvent[];
  loading: boolean;
  onCreate: (payload: CreateAlertPayload) => Promise<void>;
  onToggle: (id: string, active: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

const AlertsPanel = ({ alerts, history, loading, onCreate, onToggle, onDelete }: AlertsPanelProps) => {
  const [form, setForm] = useState<CreateAlertPayload>({
    name: "Z > 2",
    metric: "zscore",
    operator: ">",
    threshold: 2,
    window: 300,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onCreate(form);
    } catch (err) {
      setError((err as Error).message ?? "Failed to create alert");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Create Alert</h3>
        <form className="mt-4 space-y-3 text-sm" onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-1 text-slate-300">
              Name
              <input
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-slate-300">
              Window
              <input
                type="number"
                min={10}
                max={5000}
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={form.window}
                onChange={(event) => setForm((prev) => ({ ...prev, window: Number(event.target.value) }))}
              />
            </label>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <label className="flex flex-col gap-1 text-slate-300">
              Metric
              <select
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={form.metric}
                onChange={(event) => setForm((prev) => ({ ...prev, metric: event.target.value }))}
              >
                <option value="zscore">Z-Score</option>
                <option value="spread">Spread</option>
                <option value="correlation">Correlation</option>
                <option value="beta">Beta</option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-slate-300">
              Operator
              <select
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={form.operator}
                onChange={(event) => setForm((prev) => ({ ...prev, operator: event.target.value }))}
              >
                <option value=">">&gt;</option>
                <option value=">=">&gt;=</option>
                <option value="<">&lt;</option>
                <option value="<=">&lt;=</option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-slate-300">
              Threshold
              <input
                type="number"
                step="0.01"
                className="rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-slate-100 focus:border-sky-400 focus:outline-none"
                value={form.threshold}
                onChange={(event) => setForm((prev) => ({ ...prev, threshold: Number(event.target.value) }))}
                required
              />
            </label>
          </div>

          {error ? <p className="text-xs text-red-400">{error}</p> : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-sky-500 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700"
          >
            {submitting ? "Creating…" : "Create Alert"}
          </button>
        </form>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Active Alerts</h3>
          {loading ? <span className="text-xs text-slate-400">Refreshing…</span> : null}
        </div>
        <div className="mt-4 space-y-3 text-sm">
          {alerts.length ? (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2"
              >
                <div>
                  <p className="font-medium text-slate-200">{alert.name}</p>
                  <p className="text-xs text-slate-400">
                    {alert.metric} {alert.operator} {alert.threshold} · window {alert.window ?? "default"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onToggle(alert.id, !alert.active)}
                    className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                      alert.active
                        ? "bg-emerald-500/90 text-emerald-950 hover:bg-emerald-400"
                        : "bg-slate-700 text-slate-200 hover:bg-slate-600"
                    }`}
                  >
                    {alert.active ? "Active" : "Paused"}
                  </button>
                  <button
                    onClick={() => onDelete(alert.id)}
                    className="rounded-md bg-slate-800 px-3 py-1 text-xs text-slate-300 hover:bg-slate-700"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">No alerts configured yet.</p>
          )}
        </div>

        <div className="mt-5">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-300">Recent Triggers</h4>
          <div className="mt-2 max-h-40 space-y-2 overflow-y-auto text-xs text-slate-300">
            {history.length ? (
              history.map((event) => (
                <div key={`${event.alert_id}-${event.triggered_at}`} className="flex items-center justify-between gap-2">
                  <span>{event.name}</span>
                  <span className="text-slate-400">
                    {event.metric} {event.operator} {event.threshold} → {event.metric_value.toFixed(3)}
                  </span>
                  <span className="text-slate-500">{new Date(event.triggered_at).toLocaleTimeString()}</span>
                </div>
              ))
            ) : (
              <p className="text-slate-500">No triggers yet.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default AlertsPanel;

