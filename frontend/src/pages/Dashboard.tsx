import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AlertsPanel from "@/components/AlertsPanel";
import ControlPanel from "@/components/ControlPanel";
import FileOperations from "@/components/FileOperations";
import PriceChart from "@/components/PriceChart";
import SpreadChart, { type SpreadPoint } from "@/components/SpreadChart";
import StatCard from "@/components/StatCard";
import { useLiveMetrics } from "@/hooks/useLiveMetrics";
import {
  createAlert,
  deleteAlert,
  exportHistory,
  fetchAlertHistory,
  fetchAlerts,
  fetchAnalytics,
  fetchHistory,
  toggleAlert,
  uploadCsv,
} from "@/services/api";
import type { Alert, AnalyticsResponse, HistoryResponse } from "@/types";

const SYMBOL_CANDIDATES = ["btcusdt", "ethusdt", "bnbusdt", "adausdt"];

const DEFAULT_PAIR = [SYMBOL_CANDIDATES[0], SYMBOL_CANDIDATES[1]] as const;

const formatNumber = (value: number | null | undefined, digits = 3) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(digits);
};

const Dashboard = () => {
  const queryClient = useQueryClient();
  const [primarySymbol, setPrimarySymbol] = useState(SYMBOL_CANDIDATES[0]);
  const [secondarySymbol, setSecondarySymbol] = useState(SYMBOL_CANDIDATES[1]);
  const [timeframe, setTimeframe] = useState("1s");
  const [window, setWindow] = useState(300);
  const [includeIntercept, setIncludeIntercept] = useState(true);
  const [uploadPreview, setUploadPreview] = useState<HistoryResponse | null>(null);

  const liveMetrics = useLiveMetrics();

  const historyPrimaryQuery = useQuery({
    queryKey: ["history", primarySymbol, timeframe],
    queryFn: () => fetchHistory(primarySymbol, timeframe),
    refetchInterval: 30_000,
  });

  const historySecondaryQuery = useQuery({
    queryKey: ["history", secondarySymbol, timeframe],
    queryFn: () => fetchHistory(secondarySymbol, timeframe),
    refetchInterval: 30_000,
  });

  const analyticsQuery = useQuery<AnalyticsResponse>({
    queryKey: ["analytics", primarySymbol, secondarySymbol, timeframe, window, includeIntercept],
    queryFn: () =>
      fetchAnalytics({
        symbol_a: primarySymbol,
        symbol_b: secondarySymbol,
        timeframe,
        window,
        include_intercept: includeIntercept,
      }),
    refetchInterval: 15_000,
  });

  const alertsQuery = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 10_000,
  });

  const alertHistoryQuery = useQuery({
    queryKey: ["alerts", "history"],
    queryFn: fetchAlertHistory,
    refetchInterval: 15_000,
  });

  const createAlertMutation = useMutation({
    mutationFn: createAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const toggleAlertMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => toggleAlert(id, active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const deleteAlertMutation = useMutation({
    mutationFn: deleteAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file }: { file: File }) => uploadCsv(file, timeframe, primarySymbol),
    onSuccess: (data: HistoryResponse) => {
      setUploadPreview(data);
    },
  });

  const useLive =
    liveMetrics &&
    primarySymbol === DEFAULT_PAIR[0] &&
    secondarySymbol === DEFAULT_PAIR[1];

  const metrics: AnalyticsResponse | undefined = (useLive ? liveMetrics.analytics : undefined) ?? analyticsQuery.data;

  const spreadPoints = useMemo<SpreadPoint[]>(() => {
    if (timeframe === "tick") return [];
    const primary = historyPrimaryQuery.data?.bars ?? [];
    const secondary = historySecondaryQuery.data?.bars ?? [];
    if (!primary.length || !secondary.length) return [];

    const beta = metrics?.hedge_ratio.beta ?? 1;
    const secondaryMap = new Map(secondary.map((bar) => [bar.ts, bar.close]));
    const spreads: number[] = [];
    const points: SpreadPoint[] = [];
    const rollingWindow = Math.min(window, 500);

    for (const bar of primary) {
      const otherPrice = secondaryMap.get(bar.ts);
      if (otherPrice === undefined || otherPrice === null) continue;
      const spread = bar.close - beta * otherPrice;
      spreads.push(spread);
      const start = Math.max(0, spreads.length - rollingWindow);
      const slice = spreads.slice(start);
      const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
      const variance =
        slice.reduce((acc, value) => acc + Math.pow(value - mean, 2), 0) / Math.max(slice.length - 1, 1);
      const std = Math.sqrt(variance);
      const zscore = std === 0 ? 0 : (spread - mean) / std;
      points.push({ ts: bar.ts, spread, zscore });
    }

    return points;
  }, [historyPrimaryQuery.data, historySecondaryQuery.data, metrics?.hedge_ratio.beta, timeframe, window]);

  const handleCreateAlert = async (payload: { name: string; metric: string; operator: string; threshold: number; window?: number }) => {
    await createAlertMutation.mutateAsync({
      ...payload,
      symbols: [primarySymbol, secondarySymbol],
    });
  };

  const handleToggleAlert = async (id: string, active: boolean) => {
    await toggleAlertMutation.mutateAsync({ id, active });
  };

  const handleDeleteAlert = async (id: string) => {
    await deleteAlertMutation.mutateAsync(id);
  };

  const handleUpload = async (file: File) => {
    await uploadMutation.mutateAsync({ file });
  };

  const handleExport = async () => {
    const blob = await exportHistory(primarySymbol, timeframe);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${primarySymbol}_${timeframe}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  const loadingHistory = historyPrimaryQuery.isFetching || historySecondaryQuery.isFetching;
  const liveTs = useLive && liveMetrics?.timestamp ? new Date(liveMetrics.timestamp).toLocaleTimeString() : "—";

  return (
    <div className="space-y-6">
      <ControlPanel
        availableSymbols={SYMBOL_CANDIDATES}
        primarySymbol={primarySymbol}
        secondarySymbol={secondarySymbol}
        timeframe={timeframe}
        window={window}
        includeIntercept={includeIntercept}
        onUpdatePrimary={setPrimarySymbol}
        onUpdateSecondary={setSecondarySymbol}
        onTimeframeChange={setTimeframe}
        onWindowChange={setWindow}
        onToggleIntercept={setIncludeIntercept}
        onRunAdf={() => analyticsQuery.refetch()}
      />

      <section className="grid gap-4 md:grid-cols-5">
        <StatCard
          label="Hedge Ratio β"
          value={formatNumber(metrics?.hedge_ratio.beta)}
          helper={`intercept ${formatNumber(metrics?.hedge_ratio.intercept)}`}
        />
        <StatCard label="Spread" value={formatNumber(metrics?.latest_spread)} helper={`Live @ ${liveTs}`} />
        <StatCard label="Z-Score" value={formatNumber(metrics?.latest_zscore)} helper="Latest z-score" />
        <StatCard label="Correlation" value={formatNumber(metrics?.rolling_correlation)} helper="Rolling correlation" />
        <StatCard
          label="ADF p-value"
          value={formatNumber(metrics?.adf?.pvalue)}
          helper={metrics?.adf ? `stat ${formatNumber(metrics.adf.statistic)}` : "Run ADF for current window"}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <PriceChart
          primary={historyPrimaryQuery.data}
          secondary={historySecondaryQuery.data}
          loading={loadingHistory}
        />
        <SpreadChart points={spreadPoints} />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <FileOperations onUpload={handleUpload} onExport={handleExport} />
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Upload Preview</h3>
          {uploadMutation.isPending ? (
            <p className="mt-3 text-xs text-slate-400">Processing upload…</p>
          ) : uploadPreview ? (
            <div className="mt-3 text-xs text-slate-300">
              <p>{uploadPreview.bars.length} bars ingested for {uploadPreview.symbol.toUpperCase()}.</p>
              <div className="mt-3 max-h-40 overflow-y-auto rounded-lg border border-slate-800">
                <table className="min-w-full text-left">
                  <thead className="bg-slate-900 text-[10px] uppercase text-slate-400">
                    <tr>
                      <th className="px-3 py-2">Timestamp</th>
                      <th className="px-3 py-2">Open</th>
                      <th className="px-3 py-2">High</th>
                      <th className="px-3 py-2">Low</th>
                      <th className="px-3 py-2">Close</th>
                    </tr>
                  </thead>
                  <tbody className="text-[11px]">
                    {uploadPreview.bars.slice(0, 12).map((bar) => (
                      <tr key={bar.ts} className="odd:bg-slate-900/40">
                        <td className="px-3 py-1 text-slate-400">{new Date(bar.ts).toLocaleString()}</td>
                        <td className="px-3 py-1">{formatNumber(bar.open)}</td>
                        <td className="px-3 py-1">{formatNumber(bar.high)}</td>
                        <td className="px-3 py-1">{formatNumber(bar.low)}</td>
                        <td className="px-3 py-1">{formatNumber(bar.close)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="mt-3 text-xs text-slate-400">Upload CSV data to preview processed bars.</p>
          )}
        </div>
      </section>

      <AlertsPanel
        alerts={(alertsQuery.data as Alert[]) ?? []}
        history={alertHistoryQuery.data ?? []}
        loading={alertsQuery.isFetching || alertHistoryQuery.isFetching}
        onCreate={handleCreateAlert}
        onToggle={handleToggleAlert}
        onDelete={handleDeleteAlert}
      />
    </div>
  );
};

export default Dashboard;



