from typing import Literal

from pydantic import BaseModel, Field

from app.core.time import Instant, TimezoneName

from app.features.meetings.models import (
	MeetingLocationType,
	MeetingStatus,
	ParticipantRole,
	ParticipantStatus,
	empty_doc,
)


class MeetingCreate(BaseModel):
	title: str
	scheduled_start: Instant
	scheduled_end: Instant | None = None
	actual_start: Instant | None = None
	actual_end: Instant | None = None
	location_type: MeetingLocationType = MeetingLocationType.online
	location_place: str | None = None
	location_city: str | None = None
	is_formal: bool = True
	contact_person: str | None = None
	inviting_unit: str | None = None
	categories: list[str] = []
	notes: dict = Field(default_factory=empty_doc)
	# Where the organizer is (their browser's IANA zone) — defines the meeting's "day".
	timezone: TimezoneName = "UTC"
	# The organizer's own honorarium.
	has_takehome_pay: bool = False
	takehome_pay_paid: bool = False
	# People to invite straight away — each must be free for the scheduled window.
	invitee_ids: list[int] = []


class MeetingUpdate(BaseModel):
	title: str | None = None
	scheduled_start: Instant | None = None
	scheduled_end: Instant | None = None
	actual_start: Instant | None = None
	actual_end: Instant | None = None
	location_type: MeetingLocationType | None = None
	location_place: str | None = None
	location_city: str | None = None
	is_formal: bool | None = None
	contact_person: str | None = None
	inviting_unit: str | None = None
	categories: list[str] | None = None
	notes: dict | None = None
	timezone: TimezoneName | None = None
	has_takehome_pay: bool | None = None
	takehome_pay_paid: bool | None = None


class UserBrief(BaseModel):
	id: int
	full_name: str | None
	email: str
	position: str | None
	unit_name: str | None


class ParticipantRead(BaseModel):
	user: UserBrief
	role: ParticipantRole
	status: ParticipantStatus
	response_note: str | None
	invited_at: Instant
	responded_at: Instant | None


class MyParticipation(BaseModel):
	"""How the meeting relates to the person asking."""

	role: ParticipantRole
	status: ParticipantStatus
	has_takehome_pay: bool
	takehome_pay_paid: bool


class MeetingListItem(BaseModel):
	"""Omits `notes` — meeting notes get long and the list never renders them."""

	id: int
	title: str
	scheduled_start: Instant
	scheduled_end: Instant | None
	actual_start: Instant | None
	actual_end: Instant | None
	location_type: MeetingLocationType
	location_place: str | None
	location_city: str | None
	is_formal: bool
	contact_person: str | None
	inviting_unit: str | None
	categories: list[str]
	timezone: str
	status: MeetingStatus
	organizer: UserBrief
	me: MyParticipation
	accepted_count: int
	pending_count: int


class MeetingRead(MeetingListItem):
	notes: dict
	participants: list[ParticipantRead]
	created_at: Instant
	updated_at: Instant


class InviteRequest(BaseModel):
	user_ids: list[int] = Field(min_length=1)


class RespondRequest(BaseModel):
	action: Literal["accept", "decline", "cancel"]
	note: str | None = Field(default=None, max_length=500)


class MyPayUpdate(BaseModel):
	has_takehome_pay: bool
	takehome_pay_paid: bool


class PendingCount(BaseModel):
	count: int
