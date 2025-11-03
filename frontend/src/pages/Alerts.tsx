import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AlertsPanel from "@/components/AlertsPanel";
import {
  createAlert,
  deleteAlert,
  fetchAlertHistory,
  fetchAlerts,
  toggleAlert,
} from "@/services/api";
import type { Alert } from "@/types";

const Alerts = () => {
  const queryClient = useQueryClient();

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

  const handleCreateAlert = async (payload: {
    name: string;
    metric: string;
    operator: string;
    threshold: number;
    window?: number;
  }) => {
    await createAlertMutation.mutateAsync({
      ...payload,
      symbols: ["btcusdt", "ethusdt"],
    });
  };

  const handleToggleAlert = async (id: string, active: boolean) => {
    await toggleAlertMutation.mutateAsync({ id, active });
  };

  const handleDeleteAlert = async (id: string) => {
    await deleteAlertMutation.mutateAsync(id);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="text-lg font-semibold text-slate-200">Alert Management</h2>
        <p className="mt-2 text-sm text-slate-400">
          Create and manage alert rules for monitoring spread, z-score, correlation, and hedge ratio metrics.
        </p>
      </div>

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

export default Alerts;

