import { useEffect, useState } from "react";

import { wsBaseUrl } from "@/services/api";
import type { LiveMetricPayload } from "@/types";

const RECONNECT_DELAY = 2_000;

export const useLiveMetrics = () => {
  const [metrics, setMetrics] = useState<LiveMetricPayload | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let shouldReconnect = true;

    const connect = () => {
      ws = new WebSocket(wsBaseUrl("/api/ws/live"));

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as LiveMetricPayload;
          setMetrics(payload);
        } catch (error) {
          console.warn("Failed to parse live metrics", error);
        }
      };

      ws.onclose = () => {
        if (shouldReconnect) {
          setTimeout(connect, RECONNECT_DELAY);
        }
      };
    };

    connect();

    return () => {
      shouldReconnect = false;
      if (ws) {
        ws.close(1000, "component unmounted");
      }
    };
  }, []);

  return metrics;
};

export type { LiveMetricPayload };



