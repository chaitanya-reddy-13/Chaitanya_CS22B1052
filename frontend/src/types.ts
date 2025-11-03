export interface OHLCBar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface HistoryResponse {
  symbol: string;
  timeframe: string;
  bars: OHLCBar[];
}

export interface HedgeRatioResponse {
  beta: number;
  intercept: number | null;
  rvalue: number | null;
  pvalue: number | null;
  stderr: number | null;
}

export interface ADFPayload {
  statistic: number;
  pvalue: number;
  lags: number;
  nobs: number;
  critical_values: Record<string, number>;
}

export interface AnalyticsResponse {
  hedge_ratio: HedgeRatioResponse;
  latest_spread: number | null;
  latest_zscore: number | null;
  rolling_correlation: number | null;
  adf: ADFPayload | null;
}

export interface AnalyticsRequest {
  symbol_a: string;
  symbol_b: string;
  window: number;
  timeframe: string;
  include_intercept: boolean;
}

export interface Alert {
  id: string;
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  symbols: string[];
  window?: number | null;
  active: boolean;
  created_at: string;
  last_triggered: string | null;
}

export interface AlertEvent {
  alert_id: string;
  metric: string;
  threshold: number;
  metric_value: number;
  operator: string;
  triggered_at: string;
  name: string;
}

export interface LiveMetricPayload {
  timestamp: string;
  symbol: string;
  price: number;
  analytics: AnalyticsResponse;
  alerts: AlertEvent[];
}

