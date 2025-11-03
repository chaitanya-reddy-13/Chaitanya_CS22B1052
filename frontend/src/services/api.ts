import axios from "axios";

import type {
  Alert,
  AlertEvent,
  AnalyticsRequest,
  AnalyticsResponse,
  HistoryResponse,
  LiveMetricPayload,
} from "@/types";

export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 15_000,
});

export const wsBaseUrl = (path: string) => {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}${path}`;
};

export const fetchHistory = async (
  symbol: string,
  timeframe: string,
  limit = 3000,
): Promise<HistoryResponse> => {
  const { data } = await apiClient.get<HistoryResponse>("/data/history", {
    params: { symbol, timeframe, limit },
  });
  return data;
};

export const exportHistory = async (
  symbol: string,
  timeframe: string,
  limit = 5000,
): Promise<Blob> => {
  const response = await apiClient.get("/data/export", {
    params: { symbol, timeframe, limit },
    responseType: "blob",
  });
  return response.data;
};

export const uploadCsv = async (
  file: File,
  timeframe: string,
  symbol?: string,
): Promise<HistoryResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  const params: Record<string, string> = { timeframe };
  if (symbol) params.symbol = symbol;
  const { data } = await apiClient.post<HistoryResponse>("/data/upload", formData, {
    params,
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const fetchAnalytics = async (
  payload: AnalyticsRequest,
): Promise<AnalyticsResponse> => {
  const { data } = await apiClient.post<AnalyticsResponse>("/analytics/snapshot", payload);
  return data;
};

export const fetchAlerts = async (): Promise<Alert[]> => {
  const { data } = await apiClient.get<{ alerts: Alert[] }>("/alerts/");
  return data.alerts;
};

export const createAlert = async (payload: {
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  symbols: string[];
  window?: number;
}) => {
  const { data } = await apiClient.post<Alert>("/alerts/", payload);
  return data;
};

export const toggleAlert = async (id: string, active: boolean) => {
  const { data } = await apiClient.post<Alert>(`/alerts/${id}/toggle`, null, {
    params: { active },
  });
  return data;
};

export const deleteAlert = async (id: string) => {
  await apiClient.delete(`/alerts/${id}`);
};

export const fetchAlertHistory = async (): Promise<AlertEvent[]> => {
  const { data } = await apiClient.get<{ events: AlertEvent[] }>("/alerts/history");
  return data.events;
};

export type { LiveMetricPayload };



