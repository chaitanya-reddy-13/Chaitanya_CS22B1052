import { useMemo } from "react";
import Plot from "react-plotly.js";

import type { Config, Data, Layout } from "plotly.js";

import type { HistoryResponse } from "@/types";

type PriceChartProps = {
  primary?: HistoryResponse;
  secondary?: HistoryResponse;
  loading?: boolean;
};

const PriceChart = ({ primary, secondary, loading }: PriceChartProps) => {
  const figure = useMemo(() => {
    const traces: Data[] = [];

    if (primary?.bars.length) {
      // Sort bars by timestamp to ensure proper line rendering
      const sortedPrimary = [...primary.bars].sort((a, b) => 
        new Date(a.ts).getTime() - new Date(b.ts).getTime()
      );
      const primaryTrace: Data = {
        x: sortedPrimary.map((bar) => new Date(bar.ts)),
        y: sortedPrimary.map((bar) => bar.close),
        type: "scatter",
        mode: "lines+markers",
        name: primary.symbol.toUpperCase(),
        line: { color: "#38bdf8", width: 2, simplify: true },
        marker: { size: 4, opacity: 0.6 },
        connectgaps: false,
      };
      traces.push(primaryTrace);
    }

    if (secondary?.bars.length) {
      // Sort bars by timestamp to ensure proper line rendering
      const sortedSecondary = [...secondary.bars].sort((a, b) => 
        new Date(a.ts).getTime() - new Date(b.ts).getTime()
      );
      const secondaryTrace: Data = {
        x: sortedSecondary.map((bar) => new Date(bar.ts)),
        y: sortedSecondary.map((bar) => bar.close),
        type: "scatter",
        mode: "lines+markers",
        name: secondary.symbol.toUpperCase(),
        line: { color: "#f97316", width: 2, simplify: true },
        marker: { size: 4, opacity: 0.6 },
        connectgaps: false,
        yaxis: "y2",
      };
      traces.push(secondaryTrace);
    }

    const layout: Partial<Layout> = {
      autosize: true,
      margin: { l: 60, r: 60, t: 30, b: 40 },
      paper_bgcolor: "rgba(15,23,42,0.4)",
      plot_bgcolor: "rgba(15,23,42,0.4)",
      font: { color: "#e2e8f0" },
      hovermode: "x unified",
      xaxis: {
        type: "date",
        gridcolor: "rgba(148,163,184,0.1)",
      },
      yaxis: {
        title: primary ? primary.symbol.toUpperCase() : "Price",
        gridcolor: "rgba(148,163,184,0.2)",
        type: "linear",
      },
      yaxis2: {
        title: secondary ? secondary.symbol.toUpperCase() : undefined,
        overlaying: "y",
        side: "right",
        gridcolor: "rgba(148,163,184,0.05)",
        type: "linear",
      },
      legend: { orientation: "h", x: 0, y: 1.1 },
    };

    const config: Partial<Config> = {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d"],
    };

    return {
      data: traces,
      layout,
      config,
    };
  }, [primary, secondary]);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Price Overlay</h3>
        {loading ? <span className="text-xs text-slate-400">Loading…</span> : null}
      </div>
      {figure.data.length ? (
        <Plot data={figure.data} layout={figure.layout} config={figure.config} style={{ width: "100%", height: "360px" }} />
      ) : (
        <p className="text-sm text-slate-400">No price data available.</p>
      )}
    </div>
  );
};

export default PriceChart;

