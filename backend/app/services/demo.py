import math
import random
from datetime import timedelta

from ..models import Incident, Monitor, MonitorResult, utcnow
from ..repositories.demo import DemoRepository


class DemoService:
    """Opt-in, clearly labelled synthetic history for classroom demonstrations."""
    def __init__(self, repository: DemoRepository):
        self.repository = repository

    def seed(self):
        if not self.repository.is_empty():
            raise ValueError("Demo seed requires an empty database; existing records were not changed.")
        rng = random.Random(42)
        now = utcnow()
        endpoints = [
            ("JSONPlaceholder", "https://jsonplaceholder.typicode.com/posts/1", 145, True),
            ("GitHub Zen", "https://api.github.com/zen", 220, True),
            ("HTTPBin availability", "https://httpbin.org/status/503", 370, True),
            ("DummyJSON", "https://dummyjson.com/products/1", 115, False),
        ]
        for index, (name, url, base, active) in enumerate(endpoints):
            monitor = Monitor(name=f"Demo · {name}", url=url, check_interval=60, is_active=active,
                              created_at=now - timedelta(days=1))
            self.repository.insert_monitor(monitor)
            rows = []
            for step in range(96):
                checked_at = now - timedelta(minutes=(95 - step) * 15)
                failed = (index == 2 and step >= 90) or (index == 0 and 45 <= step < 48)
                elapsed = round(base + math.sin(step / 4) * 35 + rng.uniform(-18, 18), 2)
                rows.append(MonitorResult(monitor_id=monitor.id, status_code=503 if failed else 200,
                                          response_time_ms=elapsed, is_success=not failed,
                                          error_message="HTTP 503 (simulated)" if failed else None, checked_at=checked_at))
            if index == 0:
                rows.append(Incident(monitor_id=monitor.id, started_at=now - timedelta(minutes=750),
                                     resolved_at=now - timedelta(minutes=705), description="HTTP 503 (simulated)"))
            elif index == 2:
                rows.append(Incident(monitor_id=monitor.id, started_at=now - timedelta(minutes=75),
                                     description="HTTP 503 (simulated)"))
            self.repository.save_history(rows)
        self.repository.commit()
