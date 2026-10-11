"""Run `python -m app.seed` against an EMPTY database to add labelled demo data."""
from .database import Base, SessionLocal, engine
from .repositories.demo import DemoRepository
from .services.demo import DemoService


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        DemoService(DemoRepository(session)).seed()
    print("Added 4 labelled demo monitors and 384 simulated historical checks.")


if __name__ == "__main__":
    main()
