"""Meetings. Everyone sees only the meetings they have a place in; only the organizer
can change a meeting or who is invited to it."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.db import get_session
from app.features.auth.deps import get_current_user
from app.features.auth.models import User
from app.features.meetings.crud import (
	InviteConflictError,
	MeetingValidationError,
	ScheduleConflictError,
	build_meeting_read,
	cancel_meeting,
	count_pending_invitations,
	create_meeting,
	delete_meeting,
	get_meeting,
	get_participation,
	invite,
	list_categories,
	list_inviting_units,
	list_my_meetings,
	respond,
	revoke,
	set_my_pay,
	update_meeting,
)
from app.features.meetings.models import Meeting, MeetingParticipant, ParticipantRole
from app.features.meetings.schemas import (
	InviteRequest,
	MeetingCreate,
	MeetingListItem,
	MeetingRead,
	MeetingUpdate,
	MyPayUpdate,
	PendingCount,
	RespondRequest,
)

router = APIRouter()


def _load(session: Session, meeting_id: int, user: User) -> tuple[Meeting, MeetingParticipant]:
	"""The meeting plus the caller's place in it. A meeting you have no place in reads
	as not found rather than forbidden — no confirming it exists."""
	meeting = get_meeting(session, meeting_id)
	me = get_participation(session, meeting_id, user.id) if meeting else None
	if not meeting or not me:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapat tidak ditemukan.")
	return meeting, me


def _load_as_organizer(session: Session, meeting_id: int, user: User) -> tuple[Meeting, MeetingParticipant]:
	meeting, me = _load(session, meeting_id, user)
	if me.role != ParticipantRole.organizer:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya penyelenggara rapat yang dapat melakukan ini.")
	return meeting, me


def _bad_request(exc: Exception) -> HTTPException:
	code = status.HTTP_409_CONFLICT if isinstance(exc, (InviteConflictError, ScheduleConflictError)) else status.HTTP_400_BAD_REQUEST
	return HTTPException(status_code=code, detail=str(exc))


@router.get("", response_model=list[MeetingListItem])
def read_my_meetings(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> list[MeetingListItem]:
	return list_my_meetings(session, current_user.id)


@router.get("/meta/pending-count", response_model=PendingCount)
def read_pending_count(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> PendingCount:
	return PendingCount(count=count_pending_invitations(session, current_user.id))


@router.get("/meta/categories", response_model=list[str])
def read_categories(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> list[str]:
	return list_categories(session)


@router.get("/meta/units", response_model=list[str])
def read_inviting_units(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> list[str]:
	return list_inviting_units(session)


@router.get("/{meeting_id}", response_model=MeetingRead)
def read_meeting(
	meeting_id: int,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	meeting, me = _load(session, meeting_id, current_user)
	return build_meeting_read(session, meeting, me)


@router.post("", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
def add_meeting(
	meeting_in: MeetingCreate,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	try:
		meeting = create_meeting(session, meeting_in, current_user)
	except (MeetingValidationError, InviteConflictError, ScheduleConflictError) as exc:
		raise _bad_request(exc) from exc
	return build_meeting_read(session, meeting, get_participation(session, meeting.id, current_user.id))


@router.put("/{meeting_id}", response_model=MeetingRead)
def edit_meeting(
	meeting_id: int,
	meeting_in: MeetingUpdate,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	meeting, me = _load_as_organizer(session, meeting_id, current_user)
	try:
		meeting = update_meeting(session, meeting, me, meeting_in)
	except (MeetingValidationError, InviteConflictError, ScheduleConflictError) as exc:
		raise _bad_request(exc) from exc
	session.refresh(me)
	return build_meeting_read(session, meeting, me)


@router.post("/{meeting_id}/cancel", response_model=MeetingRead)
def cancel(
	meeting_id: int,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	meeting, me = _load_as_organizer(session, meeting_id, current_user)
	try:
		meeting = cancel_meeting(session, meeting)
	except MeetingValidationError as exc:
		raise _bad_request(exc) from exc
	return build_meeting_read(session, meeting, me)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_meeting(
	meeting_id: int,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> None:
	meeting, _ = _load_as_organizer(session, meeting_id, current_user)
	delete_meeting(session, meeting)


@router.post("/{meeting_id}/participants", response_model=MeetingRead)
def invite_participants(
	meeting_id: int,
	invite_in: InviteRequest,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	meeting, me = _load_as_organizer(session, meeting_id, current_user)
	try:
		invite(session, meeting, current_user, invite_in.user_ids)
	except (MeetingValidationError, InviteConflictError) as exc:
		raise _bad_request(exc) from exc
	return build_meeting_read(session, meeting, me)


@router.delete("/{meeting_id}/participants/{user_id}", response_model=MeetingRead)
def remove_participant(
	meeting_id: int,
	user_id: int,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	meeting, me = _load_as_organizer(session, meeting_id, current_user)
	participant = get_participation(session, meeting_id, user_id)
	if not participant:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peserta tidak ditemukan.")
	try:
		revoke(session, meeting, participant)
	except MeetingValidationError as exc:
		raise _bad_request(exc) from exc
	return build_meeting_read(session, meeting, me)


@router.post("/{meeting_id}/respond", response_model=MeetingRead)
def respond_to_invitation(
	meeting_id: int,
	respond_in: RespondRequest,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	meeting, me = _load(session, meeting_id, current_user)
	try:
		me = respond(session, meeting, me, respond_in.action, respond_in.note)
	except MeetingValidationError as exc:
		raise _bad_request(exc) from exc
	return build_meeting_read(session, meeting, me)


@router.put("/{meeting_id}/my-pay", response_model=MeetingRead)
def update_my_pay(
	meeting_id: int,
	pay_in: MyPayUpdate,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> MeetingRead:
	meeting, me = _load(session, meeting_id, current_user)
	try:
		set_my_pay(session, me, pay_in.has_takehome_pay, pay_in.takehome_pay_paid)
	except MeetingValidationError as exc:
		session.rollback()
		raise _bad_request(exc) from exc
	session.refresh(me)
	return build_meeting_read(session, meeting, me)
