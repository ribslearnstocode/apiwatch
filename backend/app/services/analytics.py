from datetime import timedelta, timezone

from ..errors import NotFoundError
from ..models import utcnow
from ..repositories.analytics import AnalyticsRepository


def since_hours(hours):
    return utcnow() - timedelta(hours=hours)


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    def summary(self, hours=24):
        rows = self.repository.monitor_statistics(since_hours(hours))
        for row in rows:
            checked = row["last_checked"]
            if checked is not None:
                if hasattr(checked, "isoformat"):
                    checked = checked.replace(tzinfo=checked.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()
                elif "+" not in checked and not checked.endswith("Z"):
                    checked = checked.replace(" ", "T") + "+00:00"
                row["last_checked"] = checked
        count = sum(row["total_checks"] for row in rows)
        weighted_sum = sum((row["avg_response_time"] or 0) * row["total_checks"] for row in rows)
        active = sum(bool(row["is_active"]) for row in rows)
        return {
            "total_monitors": len(rows), "active_monitors": active,
            "inactive_monitors": len(rows) - active,
            "healthy_monitors": sum(row["status"] == "healthy" for row in rows),
            "unhealthy_monitors": sum(row["status"] == "unhealthy" for row in rows),
            "average_response_time": weighted_sum / count if count else None,
            "successful_checks": sum(row["successful_checks"] for row in rows),
            "failed_checks": sum(row["failed_checks"] for row in rows), "monitors": rows,
        }

    def monitor(self, monitor_id, hours):
        for row in self.summary(hours)["monitors"]:
            if row["id"] == monitor_id:
                return row
        raise NotFoundError("Monitor not found")
