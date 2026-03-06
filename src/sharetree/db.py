from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from sharetree.settings import DATA_PATH

engine = create_engine(f"sqlite:///{DATA_PATH / 'sharetree.db'}", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


def get_session() -> Session:
    return Session(engine)


def run_migrations() -> None:
    """Run all pending Alembic migrations up to head."""
    ini_path = Path(__file__).parent.parent.parent / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    command.upgrade(alembic_cfg, "head")
