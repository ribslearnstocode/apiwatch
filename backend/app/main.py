import logging
from pathlib import Path
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .database import Base, engine
from .scheduler import scheduled_tick
from .errors import ConflictError, NotFoundError, InvalidEndpointError
from .routes import dashboard, monitors


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    scheduler = AsyncIOScheduler(timezone="UTC")
    if settings.scheduler_enabled:
        scheduler.add_job(scheduled_tick, "interval", seconds=5, max_instances=1, coalesce=True)
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)
    engine.dispose()


app = FastAPI(title="APIWatch", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])
app.include_router(monitors.router)
app.include_router(dashboard.router)


@app.exception_handler(InvalidEndpointError)
async def invalid_endpoint(request: Request, exc: InvalidEndpointError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(NotFoundError)
async def not_found(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    logging.getLogger(__name__).error("Database operation failed", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable. Please try again shortly."})


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Same-origin production UI. Registered last so API routes retain precedence.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
