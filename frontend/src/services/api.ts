export type Monitor = {
  id: number;
  name: string;
  url: string;
  check_interval: number;
  is_active: boolean;
};
export type MonitorInput = Omit<Monitor, "id">;
export type Stats = Monitor & {
  status: "healthy" | "unhealthy" | "not_yet_checked" | "inactive";
  total_checks: number;
  successful_checks: number;
  failed_checks: number;
  uptime_percentage: number | null;
  avg_response_time: number | null;
  min_response_time: number | null;
  max_response_time: number | null;
  incident_count: number;
  latest_response_time: number | null;
  last_checked: string | null;
};
export type Summary = {
  total_monitors: number;
  active_monitors: number;
  inactive_monitors: number;
  healthy_monitors: number;
  unhealthy_monitors: number;
  average_response_time: number | null;
  successful_checks: number;
  failed_checks: number;
  monitors: Stats[];
};
export type Result = {
  id: number;
  status_code: number | null;
  response_time_ms: number;
  is_success: boolean;
  error_message: string | null;
  checked_at: string;
};
export type Incident = {
  id: number;
  monitor_id: number;
  started_at: string;
  resolved_at: string | null;
  description: string;
};

export async function request<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL || ""}/api${path}`,
    {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(20000),
    },
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = data.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item: { msg: string }) => item.msg).join("; ")
          : `Request failed (${response.status}). Check that the backend is running.`,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const ms = (value: number | null) =>
  value === null ? "—" : `${Math.round(value).toLocaleString()} ms`;
export const date = (value: string | null) =>
  value
    ? new Date(value).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Not checked yet";
