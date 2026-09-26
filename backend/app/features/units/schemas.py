from pydantic import BaseModel, Field

from app.core.time import Instant


class UnitCreate(BaseModel):
	name: str = Field(min_length=1, max_length=200)
	code: str | None = None
	description: str | None = None


class UnitUpdate(BaseModel):
	name: str | None = Field(default=None, min_length=1, max_length=200)
	code: str | None = None
	description: str | None = None


class UnitRead(BaseModel):
	id: int
	name: str
	code: str | None
	description: str | None
	member_count: int
	created_at: Instant
