import { useEffect, useRef, useCallback } from 'react';
import { useMetricsStore } from '../stores/useMetricsStore';
import { useAuthStore } from '../stores/useAuthStore';

export function useWebSocket(onAuthError?: () => void) {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { setWsConnected, setWsError, setSystemMetrics, setProcessMetrics } = useMetricsStore();
  const { logout } = useAuthStore();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Use current window location for WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws/metrics`;

    console.log('[WebSocket] Connecting to:', wsUrl);

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('[WebSocket] Connected');
      setWsConnected(true);
      setWsError(null);
    };

    ws.current.onmessage = (event) => {
      try {
        // Handle ping/pong messages
        if (event.data === 'ping') {
          ws.current?.send('pong');
          return;
        }
        if (event.data === 'pong') {
          return;
        }

        const data = JSON.parse(event.data);

        // Check for auth errors from server
        if (data.error) {
          console.error('[WebSocket] Error message:', data.error);
          if (data.error.includes('Unauthorized') || data.error.includes('Authentication required')) {
            setWsConnected(false);
            logout();
            onAuthError?.();
            return;
          }
        }

        if (data.system) {
          setSystemMetrics(data.system);
        }
        if (data.processes) {
          setProcessMetrics({ 
            timestamp: data.timestamp, 
            processes: data.processes 
          });
        }
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error, 'Data:', event.data);
      }
    };

    ws.current.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      setWsError('Connection error');
      setWsConnected(false);
    };

    ws.current.onclose = (event) => {
      console.log('[WebSocket] Disconnected:', event.code, event.reason);
      setWsConnected(false);

      // Check if closed due to authentication (code 1008 = policy violation, 4001 = custom auth error)
      if (event.code === 1008 || event.code === 4001) {
        console.warn('[WebSocket] Closed possibly due to auth failure');
        logout();
        onAuthError?.();
        return;
      }

      // Auto-reconnect after 5 seconds (unless auth error)
      reconnectTimeout.current = setTimeout(() => {
        console.log('[WebSocket] Attempting to reconnect...');
        connect();
      }, 5000);
    };
  }, [setWsConnected, setWsError, setSystemMetrics, setProcessMetrics, logout, onAuthError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    setWsConnected(false);
  }, [setWsConnected]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { connect, disconnect };
}
