import asyncio
import logging

from .database import SessionLocal
from .errors import ConflictError, NotFoundError
from .repositories.monitors import MonitorRepository
from .services.monitoring import MonitoringService

logger = logging.getLogger(__name__)


async def scheduled_tick():
    """Composition root for background jobs: each concurrent check owns a session."""
    try:
        with SessionLocal() as db:
            due = MonitoringService(MonitorRepository(db)).due_monitor_ids()
        semaphore = asyncio.Semaphore(5)

        async def run(monitor_id):
            async with semaphore:
                try:
                    with SessionLocal() as db:
                        await MonitoringService(MonitorRepository(db)).check(monitor_id)
                except (ConflictError, NotFoundError):
                    pass
                except Exception:
                    logger.exception("Scheduled check failed for monitor %s", monitor_id)

        await asyncio.gather(*(run(monitor_id) for monitor_id in due))
    except Exception:
        logger.exception("Could not load scheduled monitors; retrying next tick")
