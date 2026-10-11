# APIWatch — API Monitoring & Analytics

A complete undergraduate full-stack project for registering public API endpoints, recording health checks, tracking outages, and exploring response-time history.

**Architecture:** React presentation → FastAPI API → Python services → SQLAlchemy repositories → PostgreSQL. APScheduler invokes the monitoring service independently of HTTP requests. See [architecture and data flow](docs/architecture.md).

![APIWatch dashboard with explicitly labelled simulated history](docs/screenshots/dashboard-desktop.png)

## Features

- Add, rename, pause, resume, and delete monitors; configure 30–86,400 second intervals.
- Approved public endpoint list, validated DNS, pinned public IP connections, TLS hostname verification, disabled redirects, bounded timeouts.
- Automatic checks every configured interval (scheduler scans every five seconds), plus manual checks.
- HTTP 2xx success definition; latency, failures, and timestamps stored persistently.
- One open incident per monitor; automatic recovery; cascading history deletion.
- Summary cards, searchable/filterable monitors, response-time charts, check totals, incident history, and mobile layout.
- One-hour, 24-hour, seven-day and 30-day analytics; 12-second dashboard polling.
- Real SQL aggregates, schema and query scripts, tests, documentation, and opt-in labelled demo history.

## Stack and prerequisites

Python 3.11+ (verified with 3.13), PostgreSQL 17, Node.js 22+, npm, and optionally Docker Compose. Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts. Backend: FastAPI, SQLAlchemy, Pydantic, HTTPX, APScheduler 3.x. Tests: Pytest and Playwright.

## Quick start on this Windows laptop

Open PowerShell in this project folder. Dependencies are already installed in the working copy; these commands also work after extracting the source archive:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
cd frontend
npm ci
npm run build
cd ..
.\start-local.ps1
```

`start-local.ps1` uses the existing PostgreSQL 17 binaries in `C:\Program Files\PostgreSQL\17\bin`, creates a separate `.local-pg` development cluster if needed, and starts the backend at **http://127.0.0.1:8011**. The built frontend is served at the same URL. This does not modify the system PostgreSQL service. Override the binary path with `-PostgresBin 'C:\your\postgres\bin'`.

For frontend development, open a second terminal in this folder and run `./start-frontend.ps1`, then visit **http://127.0.0.1:5178**. Vite forwards `/api` to port 8011. Ports deliberately avoid other projects already using 8000/5173.

This local cluster listens only on 127.0.0.1:55433 and uses passwordless trust authentication for local development. Do not expose that port. Stop the backend with Ctrl+C. To stop this project's database:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe' -D "$PWD\.local-pg" stop
```

## Standard PostgreSQL setup (any machine)

Create a role and database using your PostgreSQL administrator account:

```sql
CREATE ROLE apiwatch WITH LOGIN PASSWORD 'choose-a-local-password';
CREATE DATABASE apiwatch OWNER apiwatch;
```

Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL`, for example:

```dotenv
DATABASE_URL=postgresql+psycopg://apiwatch:choose-a-local-password@localhost:5432/apiwatch
SCHEDULER_ENABLED=true
CORS_ORIGINS=["http://localhost:5178","http://127.0.0.1:5178"]
```

URL-encode special characters in a database password. Start from `backend/`:

```sh
python -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --workers 1
```

Use your virtual environment's Python (`../.venv/Scripts/python.exe` on Windows, `../.venv/bin/python` on Linux/macOS). Tables are created at startup. Alternatively run `database/schema.sql` against an **empty** database before starting. The SQL script is not a migration and should not be rerun over existing tables.

On Windows, if Psycopg's binary DLL cannot load, use your installed PostgreSQL library:

```powershell
$env:PATH = 'C:\Program Files\PostgreSQL\17\bin;' + $env:PATH
$env:PSYCOPG_IMPL = 'python'
```

## Docker Compose

With Docker Desktop running:

```sh
docker compose up --build
```

Open http://127.0.0.1:8011. Compose builds React and runs one FastAPI process plus PostgreSQL with a persistent volume. For only the database, run `docker compose up -d db`; the example database URL uses port 5433. `docker compose down` stops services while preserving the database volume. The Compose credentials are for local development.

## Demo data

The dashboard starts empty on a fresh database. Register a real endpoint or, from `backend/` with the intended database configured, run:

```sh
python -m app.seed
```

The seed refuses a nonempty database. It creates four monitors, 384 simulated historical checks, and two incidents. Names start with `Demo ·`, and the UI displays a sample-data banner. Scheduled/manual checks after seeding perform real network requests. Seeded figures must not be presented as measured uptime. Screenshots use this dataset.

## Verification

From `backend/`:

```sh
python -m pytest -q
```

By default tests use an isolated temporary SQLite database and mocked external HTTP calls. PostgreSQL verification uses a unique temporary schema in a dedicated test database:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://apiwatch:password@localhost:5432/apiwatch_test'
python -m pytest -q
```

Create `apiwatch_test` first; the test role must be able to create schemas. Tests never use the development schema.

From `frontend/`:

```sh
npm ci
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser tests expect a **dedicated seeded demo backend** at port 8011 with `SCHEDULER_ENABLED=false`, and manage their own Vite server at port 5178. The CRUD test adds then deletes `https://httpbin.org/status/200`; do not run it against personal or production data. It performs one live manual check and accepts a properly recorded network failure. On this Windows machine, run `$env:PLAYWRIGHT_CHANNEL='msedge'` first to use installed Edge. Core backend tests are independent of external APIs.

Verified results and environment limits are recorded in [verification.md](docs/verification.md). CI configuration runs the same PostgreSQL and browser checks but has not yet been executed on GitHub.

## Deployment

See [deployment.md](docs/deployment.md) for the live Railway + Neon deployment and GitHub Pages dashboard at `api.ribence.com.np`. The Pages workflow publishes on frontend changes and can also be run manually. GitHub Pages hosts the frontend only; it uses the separately hosted Python backend and PostgreSQL. Railway's trial credits are limited, and monitoring pauses if the service is suspended or sleeping. The MVP has no authentication, so do not use it for private monitoring data without adding access protection.

This initial MVP has no user authentication and uses a single shared workspace. A public deployment exposes its management API to visitors; add authentication or protect it with an access gateway before storing private configuration.

## Structure

```text
backend/app/
  routes/          # HTTP adapters; no database queries
  services/        # Workflows, incident transitions, analytics composition
  repositories/    # Database operations and SQL
  models.py        # Relational models and constraints
  schemas.py       # Pydantic contracts
  dependencies.py  # Service/repository/session composition
  security.py      # Endpoint allowlist and DNS checks
  scheduler.py     # Background service invocation
  database.py      # Engine, sessions, metadata
  main.py          # Lifespan, routes, errors, built frontend
backend/tests/
frontend/src/components/
frontend/src/services/api.ts
frontend/tests/
database/          # PostgreSQL schema and analytics SQL
docs/              # Architecture, report, API, interview, deployment, screenshots
```

## Key behavior and limits

Uptime is the fraction of successful completed checks in the selected time range, not continuous availability. Latency measures DNS/connection/TLS through response headers; response bodies are not downloaded. Failed attempts contribute elapsed time to latency statistics. Current health uses the latest completed check, even if older than the chosen analytics window; inspect “Last checked” for freshness. Inactive monitors keep their history and any open incident until a future successful check resolves it.

Run **one backend worker and one replica**. The in-process duplicate-check guard does not coordinate across processes. Five scheduled network checks may run concurrently. Under load, checks run late rather than fabricating missed history. There is no retention policy, schema migration system, notification delivery, or authentication in the MVP. Endpoint addresses are immutable after creation to prevent mixing unrelated history; names, intervals, and active status are editable. The classroom allowlist is intentionally limited to five endpoints.

## Project documents

- [Architecture and data flow](docs/architecture.md)
- [Database design and ER diagram](docs/database_design.md)
- [API documentation](docs/api_documentation.md)
- [Project report](docs/project_report.md)
- [Interview preparation: 20 questions](docs/interview_preparation.md)
- [Deployment guide](docs/deployment.md)
- [Verified results](docs/verification.md)
