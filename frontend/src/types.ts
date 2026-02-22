// TypeScript type definitions matching backend models

// Device Status
export type DeviceStatus = "open" | "closed" | "offline";

export const DeviceStatus = {
  OPEN: "open" as DeviceStatus,
  CLOSED: "closed" as DeviceStatus,
  OFFLINE: "offline" as DeviceStatus,
};

// Event Type
export type EventType = "status_change" | "device_offline" | "battery_low";

export const EventType = {
  STATUS_CHANGE: "status_change" as EventType,
  DEVICE_OFFLINE: "device_offline" as EventType,
  BATTERY_LOW: "battery_low" as EventType,
};

// Device types
export interface Device {
  id: string;
  name: string;
  type: string;
  location: string;
  battery: number;
  status: DeviceStatus;
  last_updated: string; // ISO datetime string
  last_seen: string; // ISO datetime string
}

export interface DeviceCreate {
  name: string;
  type: string;
  location: string;
  battery?: number;
  status?: DeviceStatus;
}

export interface DeviceUpdate {
  name?: string;
  type?: string;
  location?: string;
  status?: DeviceStatus;
  battery?: number;
  last_updated?: string;
}

// Event types
export interface Event {
  id: string;
  device_id: string;
  type: EventType;
  details: string;
  timestamp: string; // ISO datetime string
}

export interface EventCreate {
  device_id: string;
  type: EventType;
  details: string;
}

// User types
export interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export interface UserCreate {
  email: string;
  full_name?: string | null;
  password: string;
}

export interface UserUpdate {
  email?: string;
  full_name?: string | null;
  password?: string;
}

// Authentication types
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface TokenPayload {
  sub: string | null;
}
