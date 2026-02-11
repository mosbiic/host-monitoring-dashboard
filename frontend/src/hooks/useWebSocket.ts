import { useEffect, useRef, useCallback } from 'react';
import { useMetricsStore } from '../stores/useMetricsStore';

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { setWsConnected, setWsError, setSystemMetrics, setProcessMetrics } = useMetricsStore();

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

        if (data.error) {
          console.error('[WebSocket] Error message:', data.error);
          return;
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

      // Auto-reconnect after 5 seconds
      reconnectTimeout.current = setTimeout(() => {
        console.log('[WebSocket] Attempting to reconnect...');
        connect();
      }, 5000);
    };
  }, [setWsConnected, setWsError, setSystemMetrics, setProcessMetrics]);

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
