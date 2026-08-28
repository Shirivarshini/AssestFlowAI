import { useCallback, useEffect, useState } from 'react';
import type { ReconciliationResult } from '../types/api';
import { getReconciliation } from '../services/api';

export function useReconciliation(assetId: string) {
  const [data, setData] = useState<ReconciliationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await getReconciliation(assetId);
      setData(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load reconciliation data.');
    } finally {
      setIsLoading(false);
    }
  }, [assetId]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- starts API synchronization.
    void load();
  }, [load]);

  return { data, isLoading, error, retry: load };
}
