from pydantic import BaseModel

from app.core.time import Instant

from app.features.meetings.models import ParticipantStatus
from app.features.meetings.schemas import UserBrief


class BusySlot(BaseModel):
	meeting_id: int
	title: str
	scheduled_start: Instant
	scheduled_end: Instant | None
	is_formal: bool
	status: ParticipantStatus
	assumed_end: bool
	blocking: bool
	tentative: bool


class UserAvailability(BaseModel):
	user: UserBrief
	available: bool
	busy: list[BusySlot]


class AvailabilityResult(BaseModel):
	window_start: Instant
	window_end: Instant
	users: list[UserAvailability]
