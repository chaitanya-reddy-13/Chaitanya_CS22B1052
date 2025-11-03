import { useMemo } from "react";
import Plot from "react-plotly.js";

import type { Config, Data, Layout } from "plotly.js";

type SpreadPoint = {
  ts: string;
  spread: number;
  zscore: number;
};

type SpreadChartProps = {
  points: SpreadPoint[];
};

const SpreadChart = ({ points }: SpreadChartProps) => {
  const figure = useMemo(() => {
    if (!points.length) {
      return null;
    }

    // Sort points by timestamp to ensure proper line rendering
    const sortedPoints = [...points].sort((a, b) => 
      new Date(a.ts).getTime() - new Date(b.ts).getTime()
    );

    const data: Data[] = [
      {
        x: sortedPoints.map((point) => new Date(point.ts)),
        y: sortedPoints.map((point) => point.spread),
        type: "scatter",
        mode: "lines",
        name: "Spread",
        line: { color: "#34d399", width: 2, simplify: true },
        connectgaps: false,
      },
      {
        x: sortedPoints.map((point) => new Date(point.ts)),
        y: sortedPoints.map((point) => point.zscore),
        type: "scatter",
        mode: "lines",
        name: "Z-Score",
        line: { color: "#facc15", dash: "dot", width: 2, simplify: true },
        connectgaps: false,
        yaxis: "y2",
      },
    ];

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
        title: "Spread",
        zeroline: true,
        zerolinecolor: "rgba(148,163,184,0.4)",
        gridcolor: "rgba(148,163,184,0.2)",
        type: "linear",
      },
      yaxis2: {
        title: "Z-Score",
        overlaying: "y",
        side: "right",
        zeroline: true,
        zerolinecolor: "rgba(252,211,77,0.6)",
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

    return { data, layout, config };
  }, [points]);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-300">
        Spread &amp; Z-Score
      </h3>
      {figure ? (
        <Plot data={figure.data} layout={figure.layout} config={figure.config} style={{ width: "100%", height: "320px" }} />
      ) : (
        <p className="text-sm text-slate-400">Not enough data to compute spread.</p>
      )}
    </div>
  );
};

export type { SpreadPoint };
export default SpreadChart;

