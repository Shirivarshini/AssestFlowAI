import { useCallback, useEffect, useState } from 'react';
import { getDefaultAssetId, getEvents, triggerEvent } from '../services/api';
import type { AssetEvent, EventType } from '../types/api';

export function useEvents() {
  const [data, setData] = useState<AssetEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastTriggered, setLastTriggered] = useState<AssetEvent | null>(null);
  const [assetId, setAssetId] = useState('AST-1001');

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [result, defaultAssetId] = await Promise.all([getEvents(), getDefaultAssetId()]);
      setData(result);
      setAssetId(defaultAssetId);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load event history.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- starts API synchronization.
    void load();
  }, [load]);

  const fireEvent = useCallback(async (assetId: string, eventType: EventType) => {
    setIsLoading(true);
    try {
      const result = await triggerEvent(assetId, eventType);
      setLastTriggered(result.event);
      setData((previous) => [result.event, ...previous].slice(0, 8));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to trigger the event.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { data, assetId, isLoading, error, lastTriggered, fireEvent, retry: load };
}
