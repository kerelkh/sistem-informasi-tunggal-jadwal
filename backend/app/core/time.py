"""Time as absolute instants.

Every time in the system is a point on the global timeline — what a Unix timestamp
counts — stored and sent in UTC. Nobody's clock is privileged: a meeting at
02.00 UTC is 09.00 in Jakarta, 10.00 in Makassar and 03.00 in London, and each
viewer's browser shows it in their own zone.

- Storage: `UtcDateTime` columns hold UTC. They also re-attach UTC on the way out,
  because SQLite (the test database) forgets the zone.
- API input: `Instant` only accepts times that say which zone they're in
  ("…Z" or "…+07:00"). A bare "09:00" is ambiguous — whose nine o'clock? — so it's
  refused rather than guessed.
- API output: always UTC, e.g. "2026-10-01T02:00:00Z".
"""

from datetime import datetime, timezone
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, AwareDatetime
from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
	return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
	return dt.astimezone(timezone.utc)


Instant = Annotated[AwareDatetime, AfterValidator(to_utc)]


def valid_timezone(name: str) -> str:
	"""An IANA zone name such as "Asia/Jakarta", as browsers report it."""
	try:
		ZoneInfo(name)
	except (ZoneInfoNotFoundError, ValueError) as exc:
		raise ValueError("unknown timezone") from exc
	return name


TimezoneName = Annotated[str, AfterValidator(valid_timezone)]


class UtcDateTime(TypeDecorator):
	"""A timestamp column that only ever holds and returns aware UTC datetimes."""

	impl = DateTime(timezone=True)
	cache_ok = True

	def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
		if value is None:
			return None
		if value.tzinfo is None:
			raise ValueError("Refusing to store a datetime without a timezone.")
		return value.astimezone(timezone.utc)

	def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
		if value is None:
			return None
		return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
