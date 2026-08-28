import { useCallback, useEffect, useState } from 'react';
import { getFinancing } from '../services/api';
import type { FinancingDecision } from '../types/api';

export function useFinancing(assetId: string) {
  const [data, setData] = useState<FinancingDecision | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await getFinancing(assetId);
      setData(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load financing data.');
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
