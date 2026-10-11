from sqlalchemy import select

from ..models import Monitor


class DemoRepository:
    def __init__(self, session):
        self.session = session

    def is_empty(self):
        return self.session.scalar(select(Monitor.id).limit(1)) is None

    def insert_monitor(self, monitor):
        self.session.add(monitor)
        self.session.flush()

    def save_history(self, rows):
        self.session.add_all(rows)

    def commit(self):
        self.session.commit()
