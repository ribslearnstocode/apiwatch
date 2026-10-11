# Deployment: api.ribence.com.np

## Current status

The complete source and deployment configurations are prepared locally. GitHub account access was confirmed. Render and Neon integrations were discoverable but not connected during implementation. No repository was selected/created for this project, no provider deployment was completed, and no DNS or Cloudflare settings were changed. Public hosting therefore remains unverified.

## Recommended free classroom setup: Render + Neon

Render can run the Dockerfile, which builds React and serves it through the same FastAPI application. Neon supplies external PostgreSQL. This avoids splitting the frontend and backend between origins.

1. Create a GitHub repository for this project and push the source, excluding `.env`, `.venv`, `.local-pg`, `node_modules` and generated test files. `.gitignore` already excludes them.
2. Create a free Neon PostgreSQL project. Copy the connection string into Render's secret environment settings as `DATABASE_URL`; retain its SSL parameters. `postgres://` and `postgresql://` prefixes are normalized to the Psycopg SQLAlchemy driver by the application. Never place the connection string in frontend environment variables or commit it.
3. Connect the repository in Render using its Blueprint workflow and the root `render.yaml`. The service requests the free plan and asks for `DATABASE_URL`.
4. Deploy one instance. The Docker command starts one Uvicorn worker. The platform's `PORT` is respected. The frontend and API share the generated HTTPS hostname. Check `/api/health`, `/docs`, and the dashboard, then create and manually check an endpoint.
5. In Render, add `api.ribence.com.np` as the custom domain. Configure the DNS record displayed by Render in Cloudflare. Use the provider's verification process and valid origin TLS before enabling proxying. Exact DNS values depend on the created service and cannot be filled in beforehand.
6. Verify the domain, certificate, endpoint creation, scheduled checks and persisted history after deployment. Configure access protection if the shared management workspace should not be public.

**Free-tier limitation:** Render's free web service spins down after 15 minutes without inbound traffic. Its in-process scheduler stops while the service sleeps and resumes when it wakes; missed checks are not backfilled. Free database compute/storage also has quotas. This setup is suitable for demonstrations, not a claim of continuous 24/7 monitoring. Render's own free PostgreSQL expires after 30 days, so this configuration uses an external Neon database instead. See [Render free limits](https://render.com/docs/free) and [Neon free-plan guidance](https://neon.com/blog/how-to-make-the-most-of-neons-free-plan). Plan details should be checked again at deployment.

## Optional: GitHub Pages frontend

GitHub Pages is a static host and cannot run FastAPI, APScheduler or PostgreSQL. The included `pages.yml` workflow intentionally refuses deployment until a backend URL is configured.

1. Deploy the backend with an external PostgreSQL database.
2. Set the repository **Actions variable** `VITE_API_BASE_URL` to its HTTPS origin, for example `https://your-service.onrender.com`, with no trailing slash. It is a public URL, not a secret.
3. Set backend `CORS_ORIGINS` to `["https://api.ribence.com.np"]`. If testing a temporary Pages hostname, add its exact origin too.
4. In repository Settings → Pages, select GitHub Actions as the deployment source.
5. Run “Publish dashboard to GitHub Pages” manually. It builds `frontend/dist` and writes the requested domain into the Pages CNAME artifact.
6. Set the repository's Pages custom domain to `api.ribence.com.np`. In Cloudflare create the CNAME that GitHub specifies for the account's Pages hostname and follow GitHub domain verification/HTTPS instructions.

The workflow assumes the final custom domain serves the dashboard at `/`. A repository-subpath URL needs a corresponding Vite `base` setting and asset paths. Do not point the same hostname to both Pages and Render; choose one frontend host. The Pages site must call the Render backend hostname separately.

Reference: [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

## Local container deployment

Run `docker compose config` to validate configuration, then `docker compose up --build`. PostgreSQL data persists in a named volume. The app and database ports bind only to loopback by default. For a server deployment, use a reverse proxy with HTTPS and appropriate access control rather than exposing the development database. Avoid multiple replicas until scheduler ownership is redesigned.

## Source upload commands

After creating an empty GitHub repository named `apiwatch` in your account:

```sh
git init -b main
git add .
git commit -m "Build APIWatch with layered service-repository architecture"
git remote add origin https://github.com/ribslearnstocode/apiwatch.git
git push -u origin main
```

These commands are instructions, not a claim that the repository exists or that a push occurred.
