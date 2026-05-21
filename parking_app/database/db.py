from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from parking_app.app.config import DB_PATH


class Base(DeclarativeBase):
    pass


engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
