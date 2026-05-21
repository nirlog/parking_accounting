from parking_app.database.db import Base, engine
from parking_app.database import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
