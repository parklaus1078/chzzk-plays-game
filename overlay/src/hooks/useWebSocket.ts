import { useState, useEffect, useRef } from "react";
import type { QueueState } from "@/types/queue";

const INITIAL_STATE: QueueState = {
  current: null,
  pending: [],
  recentCompleted: null,
  recentBan: null,
};

export function useQueueWebSocket(url: string): QueueState {
  const [state, setState] = useState<QueueState>(INITIAL_STATE);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(1000);
  const reconnectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(url);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setState(data);
        reconnectDelay.current = 1000;
      };

      ws.onclose = () => {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
          connect();
        }, reconnectDelay.current);
      };

      ws.onerror = () => ws.close();

      wsRef.current = ws;
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [url]);

  return state;
}
