// API client for frontend-backend communication

import type {
  Device,
  DeviceCreate,
  DeviceUpdate,
  Event,
  LoginResponse,
  APIError,
} from "../types";

/**
 * IMPORTANT: Backend Prerequisites
 * 
 * Before this frontend can communicate with the backend, the following must be configured:
 * 
 * 2. WebSocket Authentication (SECURITY)
 *    File: backend/app/core/websocket.py (line 50)
 *    Implement token validation for WebSocket connections
 * 
 * 3. Device Trigger Endpoint Authentication (SECURITY)
 *    File: backend/app/api/routes/devices.py (line 156)
 *    Add device authentication to prevent spoofing
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private getAuthToken(): string | null {
    return localStorage.getItem("access_token");
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { requiresAuth = true, ...fetchOptions } = options;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Copy any existing headers
    if (fetchOptions.headers) {
      const existingHeaders = new Headers(fetchOptions.headers);
      existingHeaders.forEach((value, key) => {
        headers[key] = value;
      });
    }

    // Add authorization header if required
    if (requiresAuth) {
      const token = this.getAuthToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
      });

      // Handle 401 Unauthorized - redirect to login
      if (response.status === 401) {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
        throw new Error("Unauthorized");
      }

      // Handle other error responses
      if (!response.ok) {
        const error: APIError = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      // Handle 204 No Content or empty responses
      if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null as T;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Network error");
    }
  }

  // ==================== Authentication ====================

  async login(email: string, password: string): Promise<LoginResponse> {
    // OAuth2 requires form data, not JSON
    const formData = new URLSearchParams();
    formData.append("username", email); // OAuth2 spec uses "username" field
    formData.append("password", password);

    const response = await fetch(`${this.baseURL}/api/login/access-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      const error: APIError = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const data: LoginResponse = await response.json();
    
    // Store token in localStorage
    localStorage.setItem("access_token", data.access_token);
    
    return data;
  }

  logout(): void {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  // ==================== Devices ====================

  async getDevices(): Promise<Device[]> {
    return this.request<Device[]>("/api/devices");
  }

  async getDevice(deviceId: string): Promise<Device> {
    return this.request<Device>(`/api/devices/${deviceId}`);
  }

  async createDevice(device: DeviceCreate): Promise<Device> {
    return this.request<Device>("/api/devices", {
      method: "POST",
      body: JSON.stringify(device),
    });
  }

  async updateDevice(deviceId: string, updates: DeviceUpdate): Promise<Device> {
    return this.request<Device>(`/api/devices/${deviceId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  }

  async deleteDevice(deviceId: string): Promise<void> {
    return this.request<void>(`/api/devices/${deviceId}`, {
      method: "DELETE",
    });
  }

  async triggerDevice(deviceId: string, status: string, battery?: number): Promise<Device> {
    const params = new URLSearchParams({ status });
    if (battery !== undefined) {
      params.append("battery", battery.toString());
    }
    
    return this.request<Device>(`/api/devices/${deviceId}/trigger?${params}`, {
      requiresAuth: false, // Trigger endpoint doesn't require auth (for IoT devices)
    });
  }

  // ==================== Events ====================

  async getEvents(limit: number = 50): Promise<Event[]> {
    return this.request<Event[]>(`/api/events?limit=${limit}`);
  }
}

// Export singleton instance
export const api = new APIClient(API_BASE_URL);
