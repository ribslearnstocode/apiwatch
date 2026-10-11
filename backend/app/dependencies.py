from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db
from .repositories.analytics import AnalyticsRepository
from .repositories.monitors import MonitorRepository
from .services.analytics import AnalyticsService
from .services.monitoring import MonitoringService
from .services.monitors import MonitorService


def get_monitor_service(db: Session = Depends(get_db)):
    return MonitorService(MonitorRepository(db))


def get_monitoring_service(db: Session = Depends(get_db)):
    return MonitoringService(MonitorRepository(db))


def get_analytics_service(db: Session = Depends(get_db)):
    return AnalyticsService(AnalyticsRepository(db))
