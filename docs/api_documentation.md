# API documentation

Local base URL: `http://127.0.0.1:8011`. Interactive OpenAPI documentation: `/docs`; JSON schema: `/openapi.json`. This MVP uses a shared workspace without authentication.

| Method | Path | Result |
|---|---|---|
| GET | `/api/health` | 200 process liveness (not a database readiness probe) |
| GET | `/api/approved-endpoints` | Approved exact URL → display name mapping |
| GET | `/api/monitors` | All monitor configurations, newest first |
| POST | `/api/monitors` | 201 created monitor |
| GET | `/api/monitors/{id}` | Monitor configuration |
| PUT | `/api/monitors/{id}` | Updated configuration |
| DELETE | `/api/monitors/{id}` | 204, cascades history deletion |
| POST | `/api/monitors/{id}/check` | One completed check; waits up to the probe timeout |
| GET | `/api/monitors/{id}/results` | Recent check rows, newest first |
| GET | `/api/monitors/{id}/analytics` | Per-monitor aggregate and current status |
| GET | `/api/monitors/{id}/incidents` | Incident history, newest first |
| GET | `/api/dashboard/summary` | Summary totals plus monitor analytics |

## Create/update body

```json
{
  "name": "GitHub Zen",
  "url": "https://api.github.com/zen",
  "check_interval": 60,
  "is_active": true
}
```

Name: 1–100 nonblank characters. URL: one exact approved HTTPS URL. Interval: integer seconds, 30–86,400; default 60. Active state defaults to true. PUT takes the complete input object; name and URL are required. Endpoint URLs cannot change after creation because previous history must remain attributable to its original endpoint. Create a new monitor for a different URL.

## Query parameters

Summary, monitor analytics and results accept `hours` from 1 to 720, default 24. Results accept `limit` (1–2,000, default 500) and `offset` (nonnegative, default 0). Incidents accept `limit` (1–1,000, default 100) and `offset`; incident history is all-time. Lists are unpaginated only for monitors, consistent with the five-endpoint allowlist.

## Check response example

```json
{
  "id": 1,
  "monitor_id": 1,
  "status_code": 200,
  "response_time_ms": 147.6,
  "is_success": true,
  "error_message": null,
  "checked_at": "2026-10-11T12:00:00+00:00"
}
```

This example is illustrative, not a measured result. HTTP 2xx is success. Other HTTP statuses and network errors are failed checks; a completed failed probe still returns HTTP 200 from the check endpoint because the monitoring operation completed successfully. A timeout has a null `status_code` and an error message. Redirects are recorded as failures without following them. Probe elapsed time includes DNS, connection and TLS establishment through response headers; no response-body timing is claimed.

## Analytics semantics

Each monitor returns total/successful/failed counts; average/minimum/maximum elapsed time; completed-check uptime; incidents started in the window; latest latency/time; and `healthy`, `unhealthy`, `not_yet_checked`, or `inactive`. With no checks, uptime and timings are null. Latest status is not restricted to the historical range. The summary includes active/inactive/healthy/unhealthy counts and a check-weighted average latency.

## Error contract

404: unknown monitor. 409: duplicate URL, overlapping check, checking a paused monitor, editing/deleting during an active check, or changing an existing URL. 422: Pydantic input/query validation failure. 503: database failure. Domain errors return `{"detail":"message"}`; validation errors contain FastAPI's structured detail list. The frontend handles both formats and displays retryable errors.

## Security policy

The allowlist is intentionally exact (including path and scheme), so alternate hosts, ports, userinfo, fragments, query strings, localhost, private endpoints and redirect endpoints are rejected. Before each check all resolved addresses must be globally routable; one validated IP is used directly, with the original Host header and TLS SNI. A 15-second total deadline includes DNS and network activity; lower connection and HTTP timeouts also apply. Environment proxy settings are ignored to preserve the connection policy. To support another endpoint, review and add a fixed URL in `security.py`, then test it. No wildcard URLs or user-supplied headers are supported.
