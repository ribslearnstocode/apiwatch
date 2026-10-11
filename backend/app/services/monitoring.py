import asyncio
import time
from datetime import timezone

import httpx

from ..errors import ConflictError
from ..models import Incident, MonitorResult, utcnow
from ..repositories.monitors import MonitorRepository
from ..security import pinned_target

running_checks: set[int] = set()


async def probe(url):
    started = time.perf_counter()
    status = None
    error = None
    try:
        async with asyncio.timeout(15):
            host, address = await pinned_target(url)
            original = httpx.URL(url)
            target = original.copy_with(host=address)
            # Let HTTPX format Host correctly for IPv6 literals and nondefault ports.
            host_header = httpx.Request("GET", original).headers["Host"]
            async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=5),
                                         follow_redirects=False, trust_env=False) as client:
                async with client.stream("GET", target, headers={"Host": host_header, "User-Agent": "APIWatch/1.0"},
                                         extensions={"sni_hostname": host}) as response:
                    status = response.status_code
                    if not 200 <= status < 300:
                        error = f"HTTP {status}" + ("; redirects are disabled" if 300 <= status < 400 else "")
    except (httpx.TimeoutException, TimeoutError):
        error = "Request timed out"
    except (httpx.HTTPError, OSError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"[:500]
    return status, round((time.perf_counter() - started) * 1000, 2), error


def ensure_idle(monitor_id):
    if monitor_id in running_checks:
        raise ConflictError("A check is running; try again shortly")


class MonitoringService:
    """Inject a repository and probe to test the workflow without HTTP or SQL."""

    def __init__(self, repository: MonitorRepository, health_probe=None):
        self.repository = repository
        self.health_probe = health_probe or probe

    def due_monitor_ids(self):
        now = utcnow()
        return [monitor.id for monitor, last in self.repository.active_with_last_check()
                if last is None or (now - last.replace(tzinfo=last.tzinfo or timezone.utc)).total_seconds() >= monitor.check_interval]

    def record_result(self, monitor_id, status, elapsed, error):
        now = utcnow()
        success = status is not None and 200 <= status < 300 and error is None
        result = MonitorResult(monitor_id=monitor_id, status_code=status, response_time_ms=elapsed,
                               is_success=success, error_message=error, checked_at=now)
        incident = self.repository.open_incident(monitor_id)
        if not success and incident is None:
            incident = Incident(monitor_id=monitor_id, started_at=now, description=error or "Check failed")
        elif success and incident is not None:
            incident.resolved_at = now
        return self.repository.persist_check(result, incident)

    async def check(self, monitor_id):
        ensure_idle(monitor_id)
        monitor = self.repository.get(monitor_id)
        if not monitor.is_active:
            raise ConflictError("Enable monitoring before running a check")
        running_checks.add(monitor_id)
        try:
            values = await self.health_probe(monitor.url)
            return self.record_result(monitor_id, *values)
        finally:
            running_checks.discard(monitor_id)
