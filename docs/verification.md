# Verification record

Verification date: 11 October 2026 (Asia/Calcutta).

| Check | Observed result |
|---|---|
| Refactored backend, isolated SQLite | 26 passed |
| Refactored backend, PostgreSQL 17 | 26 passed, including independent service and layer-boundary tests |
| TypeScript and Vite production build | Passed; chart code split into a separate bundle |
| Playwright against FastAPI + PostgreSQL | 3 passed using installed Microsoft Edge (Chromium engine) |
| PostgreSQL schema script | Executed successfully in a separate empty database |
| PostgreSQL analytics scripts | Executed successfully on 384 labelled demo checks |
| npm audit, production dependencies | Zero known vulnerabilities reported |
| Screenshots | Desktop and 390px mobile screenshots captured from the working dashboard |
| Actual APScheduler startup | `start-local.ps1` started successfully; three fresh live checks were persisted without manual HTTP check requests |
| Combined production frontend/backend | Built dashboard served by FastAPI; connected in Edge without page errors; API docs link correct; `/`, `/docs`, `/api/health` returned 200 |
| Docker image and Compose runtime | Not executed: Docker engine was unavailable |
| Docker Compose configuration | `docker compose config --quiet` passed |
| GitHub Actions | Configuration supplied; remote workflow not executed |
| Render/Neon and custom domain | Not deployed; provider connections and domain configuration pending |

## Backend coverage

Creation, list/detail retrieval, update, delete, missing records, duplicate URL, invalid fields, URL rejection, empty analytics, current status independent of analytics range, success and non-2xx probes, timeouts, redirects not followed, private DNS rejection, first-failure incidents, repeated-failure deduplication, recovery, aggregate calculations, pagination, cascading deletion, scheduler due checks, paused monitors, overlapping check rejection, busy mutations, service lock cleanup, and architectural import boundaries.

The HTTPX transport tests inspect that requests target the pinned public IP while retaining the original Host header and TLS server name. Network outcomes are mocked in the backend suite. Browser workflows make a real manual request; both successful checks and correctly recorded network failures are acceptable outcomes.

## Browser coverage

The CRUD workflow creates an initially paused monitor, changes name/interval, enables it, runs a manual check, pauses it, searches, and deletes it. The analytics workflow changes time range, filters statuses, selects another endpoint, verifies chart and incident rendering, captures screenshots, and checks mobile overflow/dialog behavior. The error workflow simulates a 503 response then verifies Retry recovers against the actual backend.

## Environment findings and scope

PostgreSQL 17 was installed but absent from PATH. Tests ran in a separate local cluster at 127.0.0.1:55433, and each PostgreSQL test session used its own temporary schema. Windows refused the Psycopg binary DLL; the installed PostgreSQL client library with `PSYCOPG_IMPL=python` worked. Downloaded Playwright Chromium could not launch; installed Edge worked without changing system security settings. Existing processes occupied ports 8000 and 5173; they were left untouched and APIWatch uses 8011 and 5178.

A third-party Starlette TestClient deprecation warning appears with the installed FastAPI/Starlette versions. SQLite verification also reports Python datetime-adapter deprecation warnings. Neither fails the tests. Dependency versions are recorded in `requirements.lock.txt` and `package-lock.json`. Passing tests establish the covered scenarios, not exhaustive correctness under all network or production conditions.
