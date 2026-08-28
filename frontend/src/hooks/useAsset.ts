import { useCallback, useEffect, useState } from 'react';
import { getAsset } from '../services/api';
import type { AssetDetailResponse } from '../types/api';

export function useAsset(assetId: string) {
  const [data, setData] = useState<AssetDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await getAsset(assetId);
      setData(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load asset data.');
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
