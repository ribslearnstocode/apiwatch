# Interview preparation

## Explain the system in one minute

“APIWatch is a React dashboard backed by a FastAPI monitoring application and PostgreSQL. I used five layers: presentation, API, services, repositories and database. The API validates JSON and delegates to injected services. APScheduler independently calls the same monitoring service. HTTPX probes an approved public endpoint, and the service determines success and incident transitions. A repository commits the check and incident atomically. SQL aggregates calculate historical metrics, and React polls every 12 seconds to display them.”

## Source-file map

| File | What to explain |
|---|---|
| `main.py` | Startup/shutdown, scheduler registration, errors, built frontend |
| `config.py` | Environment settings and database URL normalization |
| `database.py` | Engine, declarative base, request-scoped sessions |
| `models.py` | Tables, keys, constraints and indexes |
| `schemas.py` | Pydantic inputs, outputs and UTC serialization |
| `dependencies.py` | Session → repository → service dependency factories |
| `routes/monitors.py` | HTTP adapters for management, results and checks |
| `routes/dashboard.py` | Summary endpoint adapter |
| `services/monitors.py` | Management rules and history-preserving updates |
| `services/monitoring.py` | Probe, guard, success rules, incident transitions |
| `services/analytics.py` | Period boundaries and weighted summary composition |
| `repositories/monitors.py` | CRUD, history, latest times and transactional writes |
| `repositories/analytics.py` | Parameterized aggregate SQL |
| `security.py` | Exact allowlist, public DNS checks, pinned target |
| `scheduler.py` | Background dependency composition and bounded concurrency |
| `services/demo.py`, `repositories/demo.py`, `seed.py` | Opt-in synthetic data through the same layer boundaries |
| `frontend/src/App.tsx` | Dashboard state, polling, selected monitor and actions |
| `frontend/src/services/api.ts` | Typed fetch client and error interpretation |
| `frontend/src/components/` | Cards, table, form, chart and incident display |

## Twenty likely questions

1. **Why layered architecture rather than strict MVC?** React already owns rendering, and background jobs have no controller/view. Services allow the API and scheduler to reuse workflows; repositories isolate persistence. MVC ideas still map to React views, router controllers and persistent models.

2. **How does React communicate with FastAPI?** It sends JSON with Fetch to `/api`. Vite proxies requests locally; a combined production container uses the same origin. A separate Pages deployment uses `VITE_API_BASE_URL` and an explicit backend CORS origin.

3. **What does dependency injection do here?** FastAPI obtains a session, builds a repository, then a service. The router receives the service. Tests can supply different dependencies or instantiate a service with a mock repository and probe.

4. **Why three database tables?** Configuration is stable, checks are frequent observations, and incidents are outage episodes. Separate tables avoid repeating configuration in every result and avoid treating repeated failures as separate incidents.

5. **How does SQLAlchemy interact with PostgreSQL?** Mapped classes define schema metadata. Sessions track objects and execute SQL through the Psycopg driver. Repositories use ORM expressions for CRUD and parameterized text for analytics. Commit and rollback define persistence boundaries.

6. **What is the difference between validation and database constraints?** Pydantic rejects invalid requests with useful HTTP messages. Database keys, checks and indexes protect integrity even if a write comes from a script or concurrent request. Both are necessary.

7. **How do you calculate uptime?** Successful completed checks divided by all completed checks in a selected window, multiplied by 100. No checks yields null. Sampling cannot prove continuous availability between checks.

8. **Why not average endpoint averages?** An endpoint with two checks should not receive the same statistical weight as one with 200 checks. The service weights each SQL average by its check count.

9. **How are incidents detected?** A failed check opens an incident if none is open. Further failures reuse it. The next successful check resolves it. The first-ever failed check also opens an incident, even without a previously observed healthy state.

10. **How do you prevent duplicate incidents?** An in-process guard prevents overlapping checks on a monitor, and a PostgreSQL partial unique index enforces one unresolved incident per monitor. Result and incident changes commit together.

11. **How does scheduling work?** APScheduler scans every five seconds. The service selects active monitors whose latest completion is older than their configured interval. Five scheduled probes run concurrently. One job instance prevents overlapping scans.

12. **What happens with multiple backend workers?** Each worker would run its own scheduler and have its own in-memory guard. The MVP requires one worker and replica. A scaled deployment needs one scheduler owner or distributed job coordination.

13. **What counts as a failed check?** Any non-2xx HTTP code, timeout, connection/TLS error, unsafe DNS response or other expected request error. A result records elapsed time and an error; a network failure has no HTTP status. Redirects are deliberately not followed.

14. **How do you reduce SSRF risk?** Accept only exact reviewed HTTPS URLs, reject DNS answers containing any nonglobal address, connect to the validated IP directly, preserve TLS SNI/Host, disable redirects and environment proxies, and impose deadlines. The allowlist is intentionally constrained.

15. **Why use a LEFT JOIN in analytics?** A monitor with no results must remain visible as unchecked. COUNT of the result ID ignores the null joined row. A separate incident subquery avoids multiplying results by incidents.

16. **How do indexes help?** `(monitor_id, checked_at)` narrows a monitor's history and supports recent-row access. The incident composite index helps history retrieval; the partial unique index also enforces a business invariant. Indexes consume space and add write work.

17. **How is testing isolated?** Default tests use a temporary SQLite file. PostgreSQL runs create a uniquely named test schema in a dedicated database and remove it afterward. HTTP probes are mocked; unit service tests need no database. Browser tests use a separate seeded development dataset.

18. **What happens when the endpoint count grows?** History size, aggregate query cost, active database sessions and network duration all increase. Checks may run late under bounded concurrency. Add retention, bucketed summaries, monitor pagination and distributed coordination only after measuring the bottleneck.

19. **How could this be deployed?** Docker Compose runs the complete stack locally. A Render Docker web service can serve both React and FastAPI, with Neon providing PostgreSQL. Alternatively Pages serves React and a separate host serves FastAPI. Free sleeping hosts cannot guarantee uninterrupted monitoring.

20. **What would you improve next?** Authentication and endpoint ownership, schema migrations, safe endpoint expansion, retention, alerts, freshness indicators and operational deployment controls. The current project deliberately focuses on an explainable working monitoring loop.

## Suggested classroom demonstration

Start with a clean database or clearly labelled demo history. Open the dashboard, explain the five layers, register the HTTPBin 200 endpoint, run a check, rename and pause it, then enable it again. Show the HTTPBin 503 endpoint creating an incident. Use deterministic tests to demonstrate recovery, because live public failures should not be manipulated for the presentation. Open the production SQL query and explain COUNT, CASE, LEFT JOIN and the latest-row subquery. End with verified test output and the documented single-worker limit.
