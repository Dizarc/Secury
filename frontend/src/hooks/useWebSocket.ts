// Custom react hook that encapsulates WebSocket connection management.
// It provides:
// - Connection lifecycle management
// - Automatic reconnection
// - exponential backoff
// - Message handling and parsing
// - Send functionality
// - Cleanup and unmount
// - Manual reconnection attempts

import { useEffect, useRef, useState, useCallback } from "react";
import { z } from "zod";
import type { WebSocketMessage } from "../types";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
const MAX_RECONNECT_ATTEMPTS = 10;
const INITIAL_RECONNECT_DELAY = 1000; // 1 second
const MAX_RECONNECT_DELAY = 30000; // 30 seconds

const DeviceStatusSchema = z.enum(["open", "closed", "offline"]);
const EventTypeSchema = z.enum([
  "status_change",
  "device_offline",
  "battery_low",
]);

const DeviceSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  location: z.string(),
  battery: z.number(),
  status: DeviceStatusSchema,
  last_updated: z.string(),
  last_seen: z.string(),
});

const EventSchema = z.object({
  id: z.string(),
  device_id: z.string(),
  type: EventTypeSchema,
  details: z.string(),
  timestamp: z.string(),
});

const WebSocketMessageSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("initial_state"),
    devices: z.array(DeviceSchema),
    events: z.array(EventSchema),
    timestamp: z.string(),
  }),

  z.object({
    type: z.literal("device_update"),
    device: DeviceSchema,
    event: EventSchema,
    timestamp: z.string(),
  }),

  z.object({
    type: z.literal("device_added"),
    device: DeviceSchema,
    timestamp: z.string(),
  }),

  z.object({
    type: z.literal("device_updated"),
    device: DeviceSchema,
    timestamp: z.string(),
  }),

  z.object({
    type: z.literal("device_deleted"),
    device_id: z.string(),
    timestamp: z.string(),
  }),

  z.object({
    type: z.literal("device_offline"),
    device: DeviceSchema,
    event: EventSchema,
    timestamp: z.string(),
  }),
]);

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export const ConnectionStatus = {
  CONNECTING: "connecting" as ConnectionStatus,
  CONNECTED: "connected" as ConnectionStatus,
  DISCONNECTED: "disconnected" as ConnectionStatus,
  ERROR: "error" as ConnectionStatus,
};

interface UseWebSocketReturn {
  status: ConnectionStatus;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: unknown) => void;
  reconnect: () => void;
}

export const useWebSocket = (
  onMessage: (message: WebSocketMessage) => void,
  enabled: boolean = true
): UseWebSocketReturn => {
  const [status, setStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const ws = useRef<WebSocket | null>(null); // store WebSocket instance
  const reconnectAttempts = useRef(0); // Track how many attempts have occured for reconnection
  const reconnectTimeout = useRef<number | null>(null); // store timeout ID for reconnection
  const shouldConnect = useRef(enabled); // control whether automatic reconnect should occur

  const messageQueue = useRef<string[]>([]);
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    if (!shouldConnect.current) {
      return;
    }
    if (
      ws.current &&
      (
        ws.current.readyState === WebSocket.OPEN ||
        ws.current.readyState === WebSocket.CONNECTING
      )
    ) {
      return;
    }

    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    try {
      setStatus(ConnectionStatus.CONNECTING);
      
      // TODO: Add authentication token to WebSocket connection
      // Option 1: Query parameter: `${WS_URL}?token=${token}`
      // Option 2: Send token in first message after connection
      const websocket = new WebSocket(WS_URL);

      websocket.onopen = () => {
        console.log("[WebSocket] Connected");

        setStatus(ConnectionStatus.CONNECTED);

        reconnectAttempts.current = 0; // Reset reconnect counter on successful connection

        while (messageQueue.current.length > 0) {
          const queued = messageQueue.current.shift();

          if (queued) {
            websocket.send(queued);
          }
        }
      };

      websocket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);

          const result = WebSocketMessageSchema.safeParse(parsed);
          if (!result.success) {
            console.warn("[WebSocket] Received invalid message:", result.error);
            return;
          };
          const message = result.data;

          setLastMessage(message);

          onMessageRef.current(message);
        } catch (error) {
          console.error("[WebSocket] Failed to parse message:", error);
        }
      };

      websocket.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };

      websocket.onclose = (event) => {
        console.log("[WebSocket] Closed:", event.code, event.reason);
        setStatus(ConnectionStatus.DISCONNECTED);
        ws.current = null;

        // Attempt to reconnect if not manually closed
        if (shouldConnect.current && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          scheduleReconnect();
        }
      };

      ws.current = websocket;
    } catch (error) {
      console.error("[WebSocket] Connection error:", error);
      setStatus(ConnectionStatus.ERROR);
      
      if (shouldConnect.current && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        scheduleReconnect();
      }
    }
  }, [onMessage]);

  const scheduleReconnect = useCallback(() => {
    // Clear any existing reconnect timeout
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }

    // Exponential backoff: delay = min(initialDelay * 2^attempts, maxDelay)
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current),
      MAX_RECONNECT_DELAY
    );

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${MAX_RECONNECT_ATTEMPTS})`
    );

    reconnectTimeout.current = window.setTimeout(() => {
      reconnectTimeout.current = null;

      reconnectAttempts.current++;

      connect();
    }, delay);
  }, [connect]);

  const disconnect = useCallback(() => {
    shouldConnect.current = false;
    
    // Clear reconnect timeout
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    // Close WebSocket connection
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    
    setStatus(ConnectionStatus.DISCONNECTED);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    shouldConnect.current = true;
    connect();
  }, [connect, disconnect]);

  const sendMessage = useCallback((message: unknown) => {
    const serialized = JSON.stringify(message);
    
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(serialized);
      return;
    }
    console.warn("[WebSocket] Cannot send message, not connected, queuing message");

    messageQueue.current.push(serialized);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    shouldConnect.current = enabled;
    
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    status,
    lastMessage,
    sendMessage,
    reconnect,
  };
};
