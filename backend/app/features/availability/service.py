"""The "is this person free?" question, asked across everyone's calendar.

Ported from the single-user tracker's client-side `findOverlaps`, with the same rules:

- Uses SCHEDULED dates only, never actual execution. Availability is about a
  commitment on the calendar — what someone agreed to attend — not how long it
  happened to overrun.
- Only formal meetings the person has accepted (or organises) rule a slot out.
  Informal ones and still-pending invitations come back too, marked non-blocking:
  they don't rule the slot out, but you want to see them before committing.
- A meeting with no scheduled end is treated as running to the end of its day. That
  over-reports rather than under-reports, which is the right direction to be wrong.
  "Its day" is the day where it's held — in the organizer's timezone, stored on the
  meeting — since midnight falls at different instants in different places.
- Intervals are half-open: a meeting ending at 12:00 doesn't clash with one starting then.

All times are UTC instants, so comparisons don't depend on anyone's timezone.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.time import to_utc
from app.features.meetings.models import (
	Meeting,
	MeetingParticipant,
	MeetingStatus,
	ParticipantStatus,
)


@dataclass
class Overlap:
	meeting: Meeting
	status: ParticipantStatus
	# True when the meeting records no end time, so its finish had to be assumed.
	assumed_end: bool
	blocking: bool
	# Invited but hasn't answered yet.
	tentative: bool


def next_midnight(instant: datetime, tz: str) -> datetime:
	"""The first instant of the following day, as the calendar runs in `tz`."""
	zone = ZoneInfo(tz)
	tomorrow = instant.astimezone(zone).date() + timedelta(days=1)
	return to_utc(datetime.combine(tomorrow, time.min, tzinfo=zone))


def meeting_end(meeting: Meeting) -> datetime:
	return meeting.scheduled_end or next_midnight(meeting.scheduled_start, meeting.timezone)


def resolve_window(start: datetime, end: datetime | None, tz: str = "UTC") -> tuple[datetime, datetime]:
	"""No end means "the rest of that day" — the day as the asker's calendar has it."""
	start = to_utc(start)
	return start, to_utc(end) if end else next_midnight(start, tz)


def find_overlaps(
	session: Session,
	user_ids: list[int],
	start: datetime,
	end: datetime | None,
	*,
	tz: str = "UTC",
	exclude_meeting_id: int | None = None,
) -> dict[int, list[Overlap]]:
	if not user_ids:
		return {}
	window_start, window_end = resolve_window(start, end, tz)

	stmt = (
		select(MeetingParticipant, Meeting)
		.join(Meeting, Meeting.id == MeetingParticipant.meeting_id)
		.where(
			MeetingParticipant.user_id.in_(user_ids),
			MeetingParticipant.status.in_([ParticipantStatus.accepted, ParticipantStatus.pending]),
			Meeting.status == MeetingStatus.scheduled,
			Meeting.scheduled_start < window_end,
			or_(
				Meeting.scheduled_end > window_start,
				# No end → runs to midnight where it's held. That's at most a day after it
				# starts, so fetch anything from the day before and settle it below.
				Meeting.scheduled_end.is_(None) & (Meeting.scheduled_start > window_start - timedelta(days=1)),
			),
		)
		.order_by(Meeting.scheduled_start)
	)
	if exclude_meeting_id is not None:
		stmt = stmt.where(Meeting.id != exclude_meeting_id)

	result: dict[int, list[Overlap]] = defaultdict(list)
	for participant, meeting in session.exec(stmt).all():
		if meeting_end(meeting) <= window_start:
			continue
		accepted = participant.status == ParticipantStatus.accepted
		result[participant.user_id].append(
			Overlap(
				meeting=meeting,
				status=participant.status,
				assumed_end=meeting.scheduled_end is None,
				blocking=accepted and meeting.is_formal,
				tentative=not accepted,
			)
		)
	return result


def blocking_user_ids(
	session: Session,
	user_ids: list[int],
	start: datetime,
	end: datetime | None,
	*,
	tz: str = "UTC",
	exclude_meeting_id: int | None = None,
) -> set[int]:
	overlaps = find_overlaps(session, user_ids, start, end, tz=tz, exclude_meeting_id=exclude_meeting_id)
	return {uid for uid, items in overlaps.items() if any(o.blocking for o in items)}
