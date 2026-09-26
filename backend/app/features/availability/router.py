from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.db import get_session
from app.core.time import Instant, TimezoneName
from app.features.auth.deps import get_current_user
from app.features.auth.models import User
from app.features.availability.schemas import AvailabilityResult, BusySlot, UserAvailability
from app.features.availability.service import find_overlaps, resolve_window
from app.features.meetings.crud import user_briefs
from app.features.users.crud import search_users

router = APIRouter()

# Enough for a whole unit or a search result page; the picker narrows by typing.
MAX_USERS = 50


@router.get("", response_model=AvailabilityResult)
def check_availability(
	start: Instant,
	end: Instant | None = None,
	tz: TimezoneName = "UTC",
	q: str | None = None,
	unit_id: int | None = None,
	user_ids: list[int] = Query(default=[]),
	exclude_meeting_id: int | None = None,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> AvailabilityResult:
	"""Who among the matching people is free between `start` and `end`.

	Both are instants with an offset. Without `end`, the window runs to midnight in
	`tz` — the asker's own zone, so "the rest of today" means their today.

	People come from `user_ids` if given, otherwise from a directory search by
	`q` / `unit_id`. `exclude_meeting_id` leaves out the meeting being edited, so its
	own attendees don't show up as clashing with it.
	"""
	window_start, window_end = resolve_window(start, end, tz)
	if window_end <= window_start:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waktu selesai harus setelah waktu mulai.")

	if user_ids:
		people = search_users(session, ids=user_ids, active_only=True)
	else:
		people = search_users(session, q=q, unit_id=unit_id, active_only=True, limit=MAX_USERS)

	ids = [u.id for u in people]
	overlaps = find_overlaps(session, ids, window_start, window_end, exclude_meeting_id=exclude_meeting_id)
	briefs = user_briefs(session, ids)

	return AvailabilityResult(
		window_start=window_start,
		window_end=window_end,
		users=[
			UserAvailability(
				user=briefs[uid],
				available=not any(o.blocking for o in overlaps.get(uid, [])),
				busy=[
					BusySlot(
						meeting_id=o.meeting.id,
						title=o.meeting.title,
						scheduled_start=o.meeting.scheduled_start,
						scheduled_end=o.meeting.scheduled_end,
						is_formal=o.meeting.is_formal,
						status=o.status,
						assumed_end=o.assumed_end,
						blocking=o.blocking,
						tentative=o.tentative,
					)
					for o in overlaps.get(uid, [])
				],
			)
			for uid in ids
		],
	)
