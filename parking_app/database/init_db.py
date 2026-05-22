from parking_app.database.db import Base, engine
from parking_app.database import models  # noqa: F401
from parking_app.database.migrations import apply_mvp_migrations


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        apply_mvp_migrations(connection)
