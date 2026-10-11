from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import ConflictError, NotFoundError
from ..models import Incident, Monitor, MonitorResult


class MonitorRepository:
    """Owns persistence; services decide when these operations should happen."""

    def __init__(self, session: Session):
        self.session = session

    def list(self):
        return self.session.scalars(select(Monitor).order_by(Monitor.id.desc())).all()

    def get(self, monitor_id):
        monitor = self.session.get(Monitor, monitor_id)
        if monitor is None:
            raise NotFoundError("Monitor not found")
        return monitor

    def save(self, values, monitor=None):
        monitor = monitor or Monitor()
        for key, value in values.items():
            setattr(monitor, key, value)
        self.session.add(monitor)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ConflictError("This endpoint is already registered")
        self.session.refresh(monitor)
        return monitor

    def delete(self, monitor_id):
        self.session.delete(self.get(monitor_id))
        self.session.commit()

    def results(self, monitor_id, since, limit, offset):
        return self.session.scalars(select(MonitorResult).where(
            MonitorResult.monitor_id == monitor_id, MonitorResult.checked_at >= since
        ).order_by(MonitorResult.checked_at.desc(), MonitorResult.id.desc()).offset(offset).limit(limit)).all()

    def incidents(self, monitor_id, limit, offset):
        return self.session.scalars(select(Incident).where(Incident.monitor_id == monitor_id)
                                   .order_by(Incident.started_at.desc()).offset(offset).limit(limit)).all()

    def active_with_last_check(self):
        return self.session.execute(select(Monitor, func.max(MonitorResult.checked_at))
                                    .outerjoin(MonitorResult, MonitorResult.monitor_id == Monitor.id)
                                    .where(Monitor.is_active.is_(True)).group_by(Monitor.id)).all()

    def open_incident(self, monitor_id):
        return self.session.scalar(select(Incident).where(
            Incident.monitor_id == monitor_id, Incident.resolved_at.is_(None)))

    def persist_check(self, result, incident):
        self.session.add(result)
        if incident is not None:
            self.session.add(incident)
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.session.refresh(result)
        return result
