import enum
from datetime import datetime

from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from app.core.time import UtcDateTime, utcnow


class NotificationType(str, enum.Enum):
	# To an invitee
	meeting_invitation = "meeting_invitation"
	invitation_revoked = "invitation_revoked"
	meeting_updated = "meeting_updated"
	meeting_cancelled = "meeting_cancelled"
	# To the organizer
	invitation_accepted = "invitation_accepted"
	invitation_declined = "invitation_declined"
	invitation_cancelled = "invitation_cancelled"


class Notification(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id", index=True)
	type: NotificationType
	title: str
	body: str | None = Field(default=None)
	link: str | None = Field(default=None)
	is_read: bool = Field(default=False, index=True)
	# The moment the notification is about (e.g. a meeting's new start). Kept as an
	# instant, not baked into the text, so each reader sees it on their own clock.
	event_at: datetime | None = Field(default=None, sa_column=Column(UtcDateTime(), nullable=True))
	created_at: datetime = Field(default_factory=utcnow, sa_column=Column(UtcDateTime(), nullable=False, index=True))
