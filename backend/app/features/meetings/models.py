import enum
from datetime import datetime

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.core.time import UtcDateTime, utcnow


class MeetingLocationType(str, enum.Enum):
	online = "online"
	offline = "offline"


class MeetingStatus(str, enum.Enum):
	scheduled = "scheduled"
	cancelled = "cancelled"


class ParticipantRole(str, enum.Enum):
	organizer = "organizer"
	invitee = "invitee"


class ParticipantStatus(str, enum.Enum):
	pending = "pending"
	accepted = "accepted"
	declined = "declined"
	# Accepted earlier, then pulled out.
	cancelled = "cancelled"


def empty_doc() -> dict:
	return {"type": "doc", "content": [{"type": "paragraph"}]}


class Meeting(SQLModel, table=True):
	"""A meeting on someone's calendar, plus what actually happened.

	All times are absolute instants in UTC; every viewer sees them on their own clock.
	`timezone` records where the organizer was when they set it up — it's what "the
	meeting's day" means for a meeting with no end time.

	Who attends lives in MeetingParticipant, including the organizer.
	"""

	id: int | None = Field(default=None, primary_key=True)
	title: str

	# What was scheduled...
	scheduled_start: datetime = Field(sa_column=Column(UtcDateTime(), nullable=False, index=True))
	scheduled_end: datetime | None = Field(default=None, sa_column=Column(UtcDateTime(), nullable=True))
	# ...and what actually happened. Null until the meeting has run.
	actual_start: datetime | None = Field(default=None, sa_column=Column(UtcDateTime(), nullable=True))
	actual_end: datetime | None = Field(default=None, sa_column=Column(UtcDateTime(), nullable=True))
	# IANA name, e.g. "Asia/Jakarta" — the organizer's zone.
	timezone: str = Field(default="UTC")

	location_type: MeetingLocationType = Field(default=MeetingLocationType.online)
	location_place: str | None = Field(default=None)
	location_city: str | None = Field(default=None)

	# Only formal meetings block a slot — an informal one can share the day with
	# anything else, so availability checks ignore them.
	is_formal: bool = Field(default=True)

	contact_person: str | None = Field(default=None)
	# Free text on purpose: the invitation often comes from outside the organisation
	# (another ministry, a regional office), not from one of our own units.
	inviting_unit: str | None = Field(default=None, index=True)
	categories: list[str] = Field(default_factory=list, sa_column=Column(JSON))

	notes: dict = Field(default_factory=empty_doc, sa_column=Column(JSON))

	status: MeetingStatus = Field(default=MeetingStatus.scheduled, index=True)
	organizer_id: int = Field(foreign_key="user.id", index=True)
	created_at: datetime = Field(default_factory=utcnow, sa_column=Column(UtcDateTime(), nullable=False))
	updated_at: datetime = Field(default_factory=utcnow, sa_column=Column(UtcDateTime(), nullable=False))


class MeetingParticipant(SQLModel, table=True):
	"""One person's place in a meeting: the organizer, or someone they invited.

	Takehome pay is tracked here rather than on the meeting: an honorarium is paid to
	a person, and two people at the same meeting rarely get paid on the same day — or
	at all, in the organizer's case.
	"""

	__table_args__ = (UniqueConstraint("meeting_id", "user_id"),)

	id: int | None = Field(default=None, primary_key=True)
	meeting_id: int = Field(foreign_key="meeting.id", index=True, ondelete="CASCADE")
	user_id: int = Field(foreign_key="user.id", index=True)
	role: ParticipantRole = Field(default=ParticipantRole.invitee)
	status: ParticipantStatus = Field(default=ParticipantStatus.pending, index=True)
	# Why someone declined or pulled out — passed on to the organizer.
	response_note: str | None = Field(default=None)

	# Two flags, not one: a meeting with no honorarium attached should not sit in the
	# list looking permanently unpaid.
	has_takehome_pay: bool = Field(default=False)
	takehome_pay_paid: bool = Field(default=False)

	invited_at: datetime = Field(default_factory=utcnow, sa_column=Column(UtcDateTime(), nullable=False))
	responded_at: datetime | None = Field(default=None, sa_column=Column(UtcDateTime(), nullable=True))
