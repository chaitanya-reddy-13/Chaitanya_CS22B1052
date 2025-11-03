type ControlPanelProps = {
  availableSymbols: string[];
  primarySymbol: string;
  secondarySymbol: string;
  timeframe: string;
  window: number;
  includeIntercept: boolean;
  onUpdatePrimary: (symbol: string) => void;
  onUpdateSecondary: (symbol: string) => void;
  onTimeframeChange: (timeframe: string) => void;
  onWindowChange: (window: number) => void;
  onToggleIntercept: (value: boolean) => void;
  onRunAdf: () => void;
};

const ControlPanel = ({
  availableSymbols,
  primarySymbol,
  secondarySymbol,
  timeframe,
  window,
  includeIntercept,
  onUpdatePrimary,
  onUpdateSecondary,
  onTimeframeChange,
  onWindowChange,
  onToggleIntercept,
  onRunAdf,
}: ControlPanelProps) => {
  const renderSymbolOptions = () =>
    availableSymbols.map((symbol) => (
      <option key={symbol} value={symbol}>
        {symbol.toUpperCase()}
      </option>
    ));

  return (
    <div className="grid gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-5 md:grid-cols-4">
      <label className="flex flex-col text-xs font-medium uppercase tracking-wide text-slate-400">
        Primary Symbol
        <select
          className="mt-1 rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
          value={primarySymbol}
          onChange={(event) => onUpdatePrimary(event.target.value)}
        >
          {renderSymbolOptions()}
        </select>
      </label>

      <label className="flex flex-col text-xs font-medium uppercase tracking-wide text-slate-400">
        Hedge Symbol
        <select
          className="mt-1 rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
          value={secondarySymbol}
          onChange={(event) => onUpdateSecondary(event.target.value)}
        >
          {renderSymbolOptions()}
        </select>
      </label>

      <label className="flex flex-col text-xs font-medium uppercase tracking-wide text-slate-400">
        Timeframe
        <select
          className="mt-1 rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
          value={timeframe}
          onChange={(event) => onTimeframeChange(event.target.value)}
        >
          {[
            { label: "Tick", value: "tick" },
            { label: "1 Second", value: "1s" },
            { label: "1 Minute", value: "1m" },
            { label: "5 Minutes", value: "5m" },
          ].map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-xs font-medium uppercase tracking-wide text-slate-400">
        Rolling Window
        <input
          type="number"
          min={10}
          max={5000}
          value={window}
          onChange={(event) => onWindowChange(Number(event.target.value))}
          className="mt-1 rounded-lg border border-slate-700 bg-slate-900/70 p-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
        />
      </label>

      <div className="md:col-span-2">
        <label className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-400">
          <input
            type="checkbox"
            checked={includeIntercept}
            onChange={(event) => onToggleIntercept(event.target.checked)}
            className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-sky-400 focus:ring-sky-400"
          />
          Include intercept in OLS regression
        </label>
      </div>

      <div className="flex items-end justify-end md:col-span-2">
        <button
          onClick={onRunAdf}
          className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
        >
          Run ADF Test
        </button>
      </div>
    </div>
  );
};

export default ControlPanel;

