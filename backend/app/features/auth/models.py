import enum
from datetime import datetime

from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from app.core.time import UtcDateTime, utcnow


class UserRole(str, enum.Enum):
	admin = "admin"
	user = "user"


class User(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	email: str = Field(unique=True, index=True)
	full_name: str | None = Field(default=None)
	# Jabatan — shown next to the name when picking people to invite.
	position: str | None = Field(default=None)
	hashed_password: str
	role: UserRole = Field(default=UserRole.user)
	# Admins may sit outside any unit; regular users always belong to one.
	unit_id: int | None = Field(default=None, foreign_key="unit.id", index=True)
	is_active: bool = Field(default=True)
	created_at: datetime = Field(default_factory=utcnow, sa_column=Column(UtcDateTime(), nullable=False))
