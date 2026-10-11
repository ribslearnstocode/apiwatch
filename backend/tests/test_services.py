import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.errors import ConflictError
from app.services.monitoring import MonitoringService, running_checks


def test_monitoring_workflow_without_database_or_fastapi():
    repository = Mock()
    repository.get.return_value = SimpleNamespace(id=999, is_active=True, url="https://httpbin.org/status/200")
    repository.open_incident.return_value = None
    repository.persist_check.side_effect = lambda result, incident: result
    service = MonitoringService(repository, health_probe=AsyncMock(return_value=(503, 25, "HTTP 503")))
    result = asyncio.run(service.check(999))
    assert result.is_success is False
    incident = repository.persist_check.call_args.args[1]
    assert incident.monitor_id == 999 and incident.resolved_at is None
    assert 999 not in running_checks


def test_recovery_and_lock_cleanup_without_database():
    repository = Mock()
    repository.get.return_value = SimpleNamespace(is_active=True, url="https://httpbin.org/status/200")
    incident = SimpleNamespace(resolved_at=None)
    repository.open_incident.return_value = incident
    repository.persist_check.side_effect = lambda result, incident: result
    service = MonitoringService(repository, health_probe=AsyncMock(return_value=(200, 35, None)))
    assert asyncio.run(service.check(999)).is_success
    assert incident.resolved_at is not None
    service.health_probe = AsyncMock(side_effect=RuntimeError("unexpected"))
    with pytest.raises(RuntimeError):
        asyncio.run(service.check(999))
    assert 999 not in running_checks


def test_simultaneous_checks_rejected():
    repository = Mock()
    repository.get.return_value = SimpleNamespace(is_active=True, url="https://httpbin.org/status/200")
    repository.open_incident.return_value = None
    repository.persist_check.side_effect = lambda result, incident: result

    async def run():
        entered, release = asyncio.Event(), asyncio.Event()
        async def waiting_probe(url):
            entered.set()
            await release.wait()
            return 200, 10, None
        service = MonitoringService(repository, waiting_probe)
        first = asyncio.create_task(service.check(999))
        await entered.wait()
        try:
            with pytest.raises(ConflictError):
                await service.check(999)
        finally:
            release.set()
            await first
    asyncio.run(run())


def test_layer_boundaries():
    root = Path(__file__).parents[1] / "app"
    for path in (root / "routes").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any("sqlalchemy" in module or "repositories" in module or "database" in module for module in imports), path
    for path in (root / "services").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any("fastapi" in module or "sqlalchemy" in module for module in imports), path
