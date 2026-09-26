from datetime import datetime

from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from app.core.time import UtcDateTime, utcnow


class Unit(SQLModel, table=True):
	"""An organisational unit (biro, direktorat, bagian...) that groups users."""

	id: int | None = Field(default=None, primary_key=True)
	name: str = Field(unique=True, index=True)
	code: str | None = Field(default=None)
	description: str | None = Field(default=None)
	created_at: datetime = Field(default_factory=utcnow, sa_column=Column(UtcDateTime(), nullable=False))
