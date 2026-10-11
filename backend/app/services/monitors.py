from ..errors import ConflictError, InvalidEndpointError
from ..repositories.monitors import MonitorRepository
from ..security import EXAMPLE_ENDPOINTS, pinned_target
from .analytics import since_hours
from .monitoring import ensure_idle


class MonitorService:
    def __init__(self, repository: MonitorRepository):
        self.repository = repository

    def example_endpoints(self):
        return EXAMPLE_ENDPOINTS

    def list(self):
        return self.repository.list()

    def get(self, monitor_id):
        return self.repository.get(monitor_id)

    async def create(self, data):
        try:
            await pinned_target(data.url)
        except TimeoutError:
            raise InvalidEndpointError("DNS lookup timed out. Check the URL and try again.") from None
        except OSError:
            raise InvalidEndpointError("The hostname could not be resolved. Check the public API URL.") from None
        except ValueError as exc:
            raise InvalidEndpointError(str(exc)) from None
        return self.repository.save(data.model_dump())

    def update(self, monitor_id, data):
        ensure_idle(monitor_id)
        monitor = self.repository.get(monitor_id)
        if monitor.url != data.url:
            raise ConflictError("Create a new monitor to change its endpoint and keep history accurate")
        return self.repository.save(data.model_dump(), monitor)

    def delete(self, monitor_id):
        ensure_idle(monitor_id)
        self.repository.delete(monitor_id)

    def results(self, monitor_id, hours, limit, offset):
        self.repository.get(monitor_id)
        return self.repository.results(monitor_id, since_hours(hours), limit, offset)

    def incidents(self, monitor_id, limit, offset):
        self.repository.get(monitor_id)
        return self.repository.incidents(monitor_id, limit, offset)
