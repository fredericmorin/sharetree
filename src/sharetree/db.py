import json

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from sharetree.settings import DATA_PATH

engine = create_engine(f"sqlite:///{DATA_PATH / 'sharetree.db'}", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class AccessCode(Base):
    __tablename__ = "access_codes"

    code: Mapped[str] = mapped_column(primary_key=True)
    _patterns_json: Mapped[str] = mapped_column(name="patterns")
    nick: Mapped[str | None]

    @property
    def patterns(self) -> list[str]:
        return json.loads(self._patterns_json)

    @patterns.setter
    def patterns(self, value: list[str]) -> None:
        self._patterns_json = json.dumps(value)


def get_session() -> Session:
    return Session(engine)


def init_db() -> None:
    Base.metadata.create_all(engine)
