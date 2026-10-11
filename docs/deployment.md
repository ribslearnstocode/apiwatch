# Deployment: `api.ribence.com.np`

## Live deployment

The dashboard is published on GitHub Pages at [https://api.ribence.com.np](https://api.ribence.com.np). The FastAPI backend runs on Railway, and PostgreSQL is hosted by Neon.

| Component | Deployment |
| --- | --- |
| Dashboard | GitHub Pages, custom domain `api.ribence.com.np`, HTTPS enforced |
| Backend/API | `https://apiwatch-production-b472.up.railway.app` |
| API health | `https://apiwatch-production-b472.up.railway.app/api/health` |
| API documentation | `https://apiwatch-production-b472.up.railway.app/docs` |
| Database | Neon PostgreSQL; connection string is stored as Railway's `DATABASE_URL` variable |
| Pages workflow | [Publish dashboard to GitHub Pages](https://github.com/ribslearnstocode/apiwatch/actions/workflows/pages.yml) |

The GitHub Pages custom domain is configured, its certificate is approved, and HTTPS is enforced. DNS currently resolves `api.ribence.com.np` to `ribslearnstocode.github.io`. The Railway API health endpoint and database-backed monitors endpoint were verified; the dashboard loads and reports a connected workspace. The initial database is empty.

The Pages workflow uses the repository Actions variable `VITE_API_BASE_URL` for the public Railway API origin. The Railway `CORS_ORIGINS` variable allows `https://api.ribence.com.np`. Frontend changes and changes to the Pages workflow publish automatically from `main`; the workflow can also be run manually from GitHub Actions.

## Operations and limitations

- Railway is using a limited trial allowance (the account showed `$5.00` or 30 days remaining at deployment). Monitor usage and the provider's current pricing; the service may stop when trial credits expire or are exhausted. No paid-plan upgrade was made.
- Keep one Railway service instance and one Uvicorn worker. The APScheduler runs inside the web process, so monitoring pauses whenever Railway stops or sleeps the service. Missed checks are not backfilled.
- This MVP has no user authentication and exposes monitor management publicly. Do not use it for private or production monitoring data until access protection is added.
- Never commit `.env` files or database connection strings. Keep `DATABASE_URL` only in the hosting provider's secret variables; `VITE_API_BASE_URL` is a public URL and belongs in GitHub Actions variables.

## Redeployment

Railway is linked to the `main` branch of `ribslearnstocode/apiwatch` and builds the root `Dockerfile`. The Dockerfile builds the React dashboard and starts one Uvicorn worker. Railway supplies the `PORT` environment variable.

GitHub Actions builds and publishes the frontend. To publish manually, open the Pages workflow above and select **Run workflow** on `main`. The workflow builds `frontend/dist`, writes `api.ribence.com.np` to its `CNAME` file, and publishes the artifact.

If changing the API host, update the repository Actions variable `VITE_API_BASE_URL` and Railway's `CORS_ORIGINS`, then redeploy both services. Keep the API host and Pages custom domain separate.

## Local container deployment

Run `docker compose config` to validate configuration, then `docker compose up --build`. PostgreSQL data persists in a named volume. The app and database ports bind only to loopback by default. For another server deployment, use a reverse proxy with HTTPS and appropriate access control rather than exposing the development database. Avoid multiple replicas until scheduler ownership is redesigned.
