import { useCallback, useEffect, useState } from 'react';
import type { DashboardResponse } from '../types/api';
import { getDashboard } from '../services/api';

export function useDashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await getDashboard();
      setData(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load dashboard data.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- starts API synchronization.
    void load();
  }, [load]);

  return { data, isLoading, error, retry: load };
}
