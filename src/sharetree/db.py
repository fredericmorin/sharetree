from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from sharetree.settings import DATA_PATH

engine = create_engine(f"sqlite:///{DATA_PATH / 'sharetree.db'}", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


def get_session() -> Session:
    return Session(engine)


def init_db() -> None:
    Base.metadata.create_all(engine)
