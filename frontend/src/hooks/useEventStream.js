import { useEffect, useRef, useState, useCallback } from 'react';
import { getToken } from '../utils';

const WS_RECONNECT_BASE_MS = 2000;
const WS_RECONNECT_MAX_MS = 30000;

export function useEventStream(onEvent) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const retriesRef = useRef(0);
  const callbackRef = useRef(onEvent);
  callbackRef.current = onEvent;

  const connect = useCallback(() => {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const t = getToken();
    const qs = t ? `?token=${encodeURIComponent(t)}` : '';
    const url = `${proto}://${window.location.host}/ws/events${qs}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retriesRef.current = 0;
      };

      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data);
          callbackRef.current?.(event);
        } catch {}
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        const delay = Math.min(
          WS_RECONNECT_BASE_MS * Math.pow(2, retriesRef.current),
          WS_RECONNECT_MAX_MS,
        );
        retriesRef.current += 1;
        setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      const delay = Math.min(
        WS_RECONNECT_BASE_MS * Math.pow(2, retriesRef.current),
        WS_RECONNECT_MAX_MS,
      );
      retriesRef.current += 1;
      setTimeout(connect, delay);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { connected };
}
