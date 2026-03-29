import { useEffect, useRef, useCallback, useState } from 'react';

interface UsePollingOptions {
    /** Interval in milliseconds when active */
    intervalMs: number;
    /** Whether polling is enabled */
    enabled?: boolean;
    /** Callback for errors */
    onError?: (error: Error) => void;
}

/**
 * Custom hook for polling async functions with cleanup
 */
export function usePolling<T>(
    asyncFn: () => Promise<T>,
    options: UsePollingOptions
) {
    const { intervalMs, enabled = true, onError } = options;
    const [data, setData] = useState<T | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const mountedRef = useRef(true);

    const poll = useCallback(async () => {
        if (!mountedRef.current) return;

        setIsLoading(true);
        try {
            const result = await asyncFn();
            if (mountedRef.current) {
                setData(result);
                setError(null);
            }
        } catch (err) {
            if (mountedRef.current) {
                const error = err instanceof Error ? err : new Error(String(err));
                setError(error);
                onError?.(error);
            }
        } finally {
            if (mountedRef.current) {
                setIsLoading(false);
            }
        }
    }, [asyncFn, onError]);

    const refetch = useCallback(() => {
        poll();
    }, [poll]);

    useEffect(() => {
        mountedRef.current = true;

        if (enabled) {
            // Initial fetch
            poll();

            // Set up interval
            intervalRef.current = setInterval(poll, intervalMs);
        }

        return () => {
            mountedRef.current = false;
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [enabled, intervalMs, poll]);

    return { data, isLoading, error, refetch };
}

/**
 * Polling hook with dynamic interval based on a condition
 */
export function useDynamicPolling<T>(
    asyncFn: () => Promise<T>,
    options: {
        activeIntervalMs: number;
        idleIntervalMs: number;
        isActive: boolean;
        enabled?: boolean;
        onError?: (error: Error) => void;
    }
) {
    const { activeIntervalMs, idleIntervalMs, isActive, enabled = true, onError } = options;
    const intervalMs = isActive ? activeIntervalMs : idleIntervalMs;

    return usePolling(asyncFn, { intervalMs, enabled, onError });
}
