import json

from sqlalchemy.orm import Mapped, mapped_column

from sharetree.db import Base


class AccessCode(Base):
    __tablename__ = "access_codes"

    code: Mapped[str] = mapped_column(primary_key=True)
    _patterns_json: Mapped[str] = mapped_column(name="patterns")
    nick: Mapped[str | None]
    session_id: Mapped[str | None] = mapped_column(index=True, default=None)

    @property
    def patterns(self) -> list[str]:
        return json.loads(self._patterns_json)

    @patterns.setter
    def patterns(self, value: list[str]) -> None:
        self._patterns_json = json.dumps(value)
