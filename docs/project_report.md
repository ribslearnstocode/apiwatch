# APIWatch — API Monitoring & Analytics Platform

## 1. Abstract

APIWatch is a full-stack web application that periodically checks approved public APIs, stores response information, detects outage episodes, and presents historical performance through a dashboard. It combines Python services, a relational PostgreSQL database, and a React interface. The project demonstrates REST development, dependency injection, SQL aggregation, background scheduling, validation, testing, and layered software design at undergraduate scope.

## 2. Problem statement

Applications depend on external APIs whose availability can change without warning. Manual checks provide limited visibility and no organized history. A small monitoring tool can record repeated observations and help developers understand failures and response-time changes. The tool must distinguish an observed successful check from a claim of uninterrupted availability.

## 3. Objectives

Register approved endpoints; schedule periodic checks; persist successful and failed attempts; detect and resolve incidents; calculate SQL-based statistics; expose a documented REST API; provide an accessible responsive dashboard; and validate behavior with automated tests. Keep the source understandable enough to explain every layer during a technical interview.

## 4. Technologies

React and TypeScript provide typed UI components. Vite builds and serves the frontend; Tailwind CSS and application CSS define its visual system. Recharts visualizes response times. FastAPI handles HTTP and Pydantic contracts. SQLAlchemy manages PostgreSQL persistence. HTTPX performs asynchronous health probes. APScheduler 3.x initiates periodic work. Pytest, FastAPI TestClient, mocks and Playwright verify behavior. Docker Compose is an optional deployment package.

## 5. System architecture

The implementation follows **Layered Architecture with the Service–Repository Pattern**. React is the presentation layer. FastAPI routers are HTTP adapters. Services contain workflows and incident decisions. Repositories contain database access and SQL. PostgreSQL maintains persistent relational state. Dependency factories compose sessions, repositories, and services. APScheduler invokes the service layer without HTTP requests. See the [architecture diagram and data-flow explanation](architecture.md).

This structure applies MVC ideas without forcing server-side views into a React application. Reusable services are particularly valuable because both manual HTTP requests and background jobs need the same monitoring behavior. A small number of concrete classes provides separation without introducing generic frameworks.

## 6. Database design

Three normalized tables represent configurations, completed checks, and outage episodes. Monitor results and incidents have foreign keys to monitors. Deletion cascades remove dependent records. Composite indexes support per-monitor history, and a partial unique index prevents duplicate open incidents. UTC-aware timestamps and PostgreSQL timestamptz represent instants consistently. The [database document](database_design.md) contains the ER diagram and field explanations; `database/schema.sql` matches the models.

## 7. Functional requirements implemented

Users can create, list, rename, pause, enable, and delete monitors. They can change check intervals, request immediate checks, filter the monitoring table, choose analytics periods, and inspect charts and incidents. URL changes require a new monitor so that historical measurements remain meaningful. The interface shows healthy, unhealthy, unchecked and inactive states. Error messages cover validation, duplicate configurations, unavailable records and database failures.

The classroom edition deliberately supports five exact public endpoints. It validates DNS addresses, pins the selected public address, preserves TLS hostname verification and disables redirects. This follows the original brief's allowlist alternative for a manageable safety policy.

## 8. Backend implementation

`MonitorService` handles management rules. `MonitoringService` checks active state, guards concurrent checks, runs the injected probe, decides whether an incident should open or resolve, and asks its repository to persist the result atomically. `AnalyticsService` composes repository aggregates and calculates weighted dashboard totals. Repository classes encapsulate SQLAlchemy operations, raw SQL and transaction boundaries.

An APScheduler interval job scans every five seconds and checks due monitors with a concurrency limit of five. Each concurrent operation owns its database session. The application uses one backend process; multiple schedulers would duplicate work because the in-memory guard is local to one process. Exceptions are logged by the scheduler so later ticks can continue.

## 9. Frontend implementation

The single-page dashboard contains summary cards, a status banner, endpoint management, response-time charts, check proportions and incident history. A central typed fetch helper interprets API errors and applies a request deadline. React state manages the selected monitor, filters, time range, forms, deletion confirmation and notifications. Summary polling repeats 12 seconds after the previous request completes. Effect cleanup ignores stale results after a filter change or unmount. Native dialogs provide keyboard focus containment and Escape behavior.

Desktop and mobile screenshots in `docs/screenshots/` show an explicitly labelled seeded dataset. Browser testing checks that the mobile document does not overflow horizontally, while wide data tables scroll inside their panels.

## 10. SQL queries

The production query demonstrates SELECT, WHERE in subqueries, LEFT JOIN, GROUP BY, ORDER BY, COUNT, SUM, AVG, MIN, MAX and CASE WHEN. Separate aggregates avoid double counting checks when a monitor has several incidents. NULLIF prevents division by zero. A latest-row subquery retrieves current state independently of the historical range. An additional standalone PostgreSQL query demonstrates hourly bucketing with date_trunc. See [database design](database_design.md) for interpretation.

## 11. Testing methodology and verified results

Backend integration tests use FastAPI TestClient and an isolated database. External HTTP calls are mocked for deterministic successes, failures, redirects and timeouts. Separate service tests inject mock repositories and probes, including a simultaneous-check test. A layer-boundary test prevents routers from importing database/repository modules and services from importing SQLAlchemy/FastAPI.

The 26-test backend suite passed against PostgreSQL 17 after the architectural refactor. Three Playwright browser tests passed against the real backend and PostgreSQL, covering CRUD, manual checking, filters, charts, mobile layout and error recovery. TypeScript compilation and the Vite production build passed. PostgreSQL schema and analytics scripts executed successfully. The production npm dependency audit reported zero known vulnerabilities. Final evidence and remaining unverified areas are maintained in [verification.md](verification.md).

## 12. Challenges encountered

The running Docker engine was unavailable, but PostgreSQL binaries were already installed outside PATH. A separate local cluster allowed real database testing without changing the existing server. Windows blocked the downloaded Psycopg binary DLL, so verification used Psycopg's Python implementation with the installed PostgreSQL client library. A downloaded browser binary could not start; installed Microsoft Edge provided the Playwright browser. Ports 8000 and 5173 were occupied, so the project uses 8011 and 5178.

The first browser analytics test used an ambiguous button selector; it was corrected to target the endpoint selection button. Moving from the initial modular implementation to the requested service–repository architecture required relocating every query and separating HTTP exceptions from domain errors. The expanded tests passed after the refactor.

## 13. Limitations

The application measures samples, not continuous availability or SLA compliance. It records time to response headers, not complete body download time. There is no authentication, alert delivery, retention job, migration history or multi-user ownership. Historical charts show at most the latest 500 samples, while SQL statistics cover the entire chosen period. The allowlist is small and URLs are immutable after creation. Synchronous database operations and one scheduler process limit throughput. Free hosting that sleeps pauses the scheduler, and a deployment restart does not reconstruct missed checks.

## 14. Future enhancements

Add authentication and ownership, safe reviewed endpoint expansion, retention and aggregation, database migrations, configurable success rules, maintenance windows, notification channels, and distributed scheduler coordination. Optimize from measured load before introducing additional infrastructure. A full production system would need operational backups, rate limits and controlled deployment transitions.

## 15. Development plan and reproducibility

A realistic three-day plan remains: day one for schema, repositories, services and API tests; day two for React components, integration and visual design; day three for incident edge cases, browser checks and documentation. These are suggested learning milestones, not a claim about elapsed implementation time. The README includes installation, execution, seeding and verification commands; dependency lockfiles support reproduction.

## 16. Conclusion

APIWatch implements the monitoring workflow from endpoint registration to SQL analysis and browser visualization. The five-layer architecture separates HTTP, business decisions and persistence, enabling the same monitoring service to serve both manual actions and scheduled jobs. Automated verification supports the main functional behavior while the documentation identifies deployment and scale limits explicitly.
