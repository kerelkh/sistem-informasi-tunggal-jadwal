from collections import Counter

from sqlalchemy import func
from sqlmodel import Session, delete, select

from app.core.time import utcnow
from app.features.auth.models import User
from app.features.availability.service import blocking_user_ids
from app.features.meetings.models import (
	Meeting,
	MeetingLocationType,
	MeetingParticipant,
	MeetingStatus,
	ParticipantRole,
	ParticipantStatus,
)
from app.features.meetings.schemas import (
	MeetingCreate,
	MeetingListItem,
	MeetingRead,
	MeetingUpdate,
	MyParticipation,
	ParticipantRead,
	UserBrief,
)
from app.features.notifications.crud import add_notification
from app.features.notifications.models import NotificationType
from app.features.units.models import Unit

# Participants who still expect to hear about the meeting — people who declined or
# pulled out have already moved on.
ACTIVE_STATUSES = (ParticipantStatus.pending, ParticipantStatus.accepted)

# Changing any of these changes whether/where/when an invitee has to be somewhere.
MATERIAL_FIELDS = (
	"title",
	"scheduled_start",
	"scheduled_end",
	"location_type",
	"location_place",
	"location_city",
)

PAY_FIELDS = ("has_takehome_pay", "takehome_pay_paid")


class MeetingValidationError(ValueError):
	"""Raised when a meeting's fields contradict each other, or a request doesn't fit
	the meeting's current state."""


class InviteConflictError(ValueError):
	"""Raised when someone being invited already has a formal meeting in that slot."""


def validate_meeting(meeting: Meeting) -> None:
	"""Checks the resolved record, not the incoming patch — a partial update can only
	be judged once the change is applied."""
	for label, start, end in (
		("jadwal", meeting.scheduled_start, meeting.scheduled_end),
		("realisasi", meeting.actual_start, meeting.actual_end),
	):
		if start and end and end < start:
			raise MeetingValidationError(f"Waktu selesai {label} tidak boleh sebelum waktu mulai {label}.")

	if meeting.location_type == MeetingLocationType.online and (
		meeting.location_place or meeting.location_city
	):
		raise MeetingValidationError("Rapat daring tidak boleh memiliki tempat dan kota.")

	if meeting.location_type == MeetingLocationType.offline and not (
		meeting.location_place or meeting.location_city
	):
		raise MeetingValidationError("Rapat luring wajib diisi tempat atau kota.")


def validate_pay(participant: MeetingParticipant) -> None:
	if participant.takehome_pay_paid and not participant.has_takehome_pay:
		raise MeetingValidationError("Honorarium tidak dapat ditandai sudah dibayar jika rapat tidak memiliki honorarium.")


def display_name(user: User | UserBrief) -> str:
	return user.full_name or user.email


def meeting_link(meeting: Meeting) -> str:
	return f"/dashboard/meetings/{meeting.id}"


# --- reads -----------------------------------------------------------------------


def user_briefs(session: Session, user_ids: list[int]) -> dict[int, UserBrief]:
	if not user_ids:
		return {}
	rows = session.exec(
		select(User, Unit).join(Unit, Unit.id == User.unit_id, isouter=True).where(User.id.in_(user_ids))
	).all()
	return {
		user.id: UserBrief(
			id=user.id,
			full_name=user.full_name,
			email=user.email,
			position=user.position,
			unit_name=unit.name if unit else None,
		)
		for user, unit in rows
	}


def get_meeting(session: Session, meeting_id: int) -> Meeting | None:
	return session.get(Meeting, meeting_id)


def get_participation(session: Session, meeting_id: int, user_id: int) -> MeetingParticipant | None:
	return session.exec(
		select(MeetingParticipant).where(
			MeetingParticipant.meeting_id == meeting_id, MeetingParticipant.user_id == user_id
		)
	).first()


def _participants(session: Session, meeting_id: int) -> list[MeetingParticipant]:
	return list(
		session.exec(select(MeetingParticipant).where(MeetingParticipant.meeting_id == meeting_id)).all()
	)


def _status_counts(session: Session, meeting_ids: list[int]) -> dict[int, Counter]:
	counts: dict[int, Counter] = {mid: Counter() for mid in meeting_ids}
	if meeting_ids:
		rows = session.exec(
			select(MeetingParticipant.meeting_id, MeetingParticipant.status).where(
				MeetingParticipant.meeting_id.in_(meeting_ids)
			)
		).all()
		for meeting_id, status in rows:
			counts[meeting_id][status] += 1
	return counts


def _my_participation(p: MeetingParticipant) -> MyParticipation:
	return MyParticipation(
		role=p.role,
		status=p.status,
		has_takehome_pay=p.has_takehome_pay,
		takehome_pay_paid=p.takehome_pay_paid,
	)


def _list_item_fields(meeting: Meeting) -> dict:
	return meeting.model_dump(exclude={"notes", "organizer_id", "created_at", "updated_at"})


def list_my_meetings(session: Session, user_id: int) -> list[MeetingListItem]:
	"""Every meeting the user has a place in — organised, accepted, pending, or turned
	down. The client decides what to show where."""
	rows = session.exec(
		select(MeetingParticipant, Meeting)
		.join(Meeting, Meeting.id == MeetingParticipant.meeting_id)
		.where(MeetingParticipant.user_id == user_id)
		.order_by(Meeting.scheduled_start.desc())
	).all()

	meeting_ids = [m.id for _, m in rows]
	organizers = user_briefs(session, list({m.organizer_id for _, m in rows}))
	counts = _status_counts(session, meeting_ids)

	return [
		MeetingListItem(
			**_list_item_fields(meeting),
			organizer=organizers[meeting.organizer_id],
			me=_my_participation(participant),
			accepted_count=counts[meeting.id][ParticipantStatus.accepted],
			pending_count=counts[meeting.id][ParticipantStatus.pending],
		)
		for participant, meeting in rows
	]


def build_meeting_read(session: Session, meeting: Meeting, me: MeetingParticipant) -> MeetingRead:
	participants = _participants(session, meeting.id)
	briefs = user_briefs(session, [p.user_id for p in participants] + [meeting.organizer_id])
	counts = Counter(p.status for p in participants)

	# Organizer first, then invitees by when they were asked.
	participants.sort(key=lambda p: (p.role != ParticipantRole.organizer, p.invited_at))

	return MeetingRead(
		**_list_item_fields(meeting),
		notes=meeting.notes,
		created_at=meeting.created_at,
		updated_at=meeting.updated_at,
		organizer=briefs[meeting.organizer_id],
		me=_my_participation(me),
		accepted_count=counts[ParticipantStatus.accepted],
		pending_count=counts[ParticipantStatus.pending],
		participants=[
			ParticipantRead(
				user=briefs[p.user_id],
				role=p.role,
				status=p.status,
				response_note=p.response_note,
				invited_at=p.invited_at,
				responded_at=p.responded_at,
			)
			for p in participants
		],
	)


def count_pending_invitations(session: Session, user_id: int) -> int:
	return session.exec(
		select(func.count())
		.select_from(MeetingParticipant)
		.join(Meeting, Meeting.id == MeetingParticipant.meeting_id)
		.where(
			MeetingParticipant.user_id == user_id,
			MeetingParticipant.status == ParticipantStatus.pending,
			Meeting.status == MeetingStatus.scheduled,
		)
	).one()


def list_categories(session: Session) -> list[str]:
	rows = session.exec(select(Meeting.categories)).all()
	return sorted({c for row in rows for c in (row or [])})


def list_inviting_units(session: Session) -> list[str]:
	rows = session.exec(select(Meeting.inviting_unit).where(Meeting.inviting_unit.is_not(None))).all()
	return sorted({u for u in rows if u})


# --- invitations -----------------------------------------------------------------


def _check_invitees(session: Session, meeting: Meeting, organizer_id: int, user_ids: list[int]) -> list[User]:
	user_ids = list(dict.fromkeys(user_ids))  # de-duplicate, keep order
	if organizer_id in user_ids:
		raise MeetingValidationError("Anda sudah terdaftar di rapat ini sebagai penyelenggara.")

	users = list(session.exec(select(User).where(User.id.in_(user_ids))).all())
	if len(users) != len(user_ids) or any(not u.is_active for u in users):
		raise MeetingValidationError("Sebagian pengguna tersebut tidak ditemukan atau sudah dinonaktifkan.")

	busy = blocking_user_ids(
		session,
		user_ids,
		meeting.scheduled_start,
		meeting.scheduled_end,
		tz=meeting.timezone,
		exclude_meeting_id=meeting.id,
	)
	if busy:
		names = ", ".join(sorted(display_name(u) for u in users if u.id in busy))
		raise InviteConflictError(f"Tidak tersedia pada waktu tersebut: {names}.")
	return users


def _stage_invites(session: Session, meeting: Meeting, organizer: User, users: list[User]) -> int:
	"""Adds (or re-opens) invitations without committing. Returns how many were sent.

	Someone who already has a live invitation is left alone. Someone who declined or
	pulled out gets a fresh one — being asked again is a new question.
	"""
	sent = 0
	for user in users:
		existing = get_participation(session, meeting.id, user.id) if meeting.id else None
		if existing and existing.status in ACTIVE_STATUSES:
			continue
		if existing:
			existing.status = ParticipantStatus.pending
			existing.response_note = None
			existing.responded_at = None
			existing.invited_at = utcnow()
			session.add(existing)
		else:
			session.add(MeetingParticipant(meeting_id=meeting.id, user_id=user.id))
		add_notification(
			session,
			user_id=user.id,
			type=NotificationType.meeting_invitation,
			title=f"{display_name(organizer)} mengundang Anda ke rapat \"{meeting.title}\"",
			event_at=meeting.scheduled_start,
			link=meeting_link(meeting),
		)
		sent += 1
	return sent


def invite(session: Session, meeting: Meeting, organizer: User, user_ids: list[int]) -> int:
	if meeting.status == MeetingStatus.cancelled:
		raise MeetingValidationError("Rapat ini telah dibatalkan.")
	users = _check_invitees(session, meeting, organizer.id, user_ids)
	sent = _stage_invites(session, meeting, organizer, users)
	session.commit()
	return sent


def revoke(session: Session, meeting: Meeting, participant: MeetingParticipant) -> None:
	if participant.role == ParticipantRole.organizer:
		raise MeetingValidationError("Penyelenggara tidak dapat dikeluarkan dari rapatnya sendiri.")
	if participant.status in ACTIVE_STATUSES and meeting.status == MeetingStatus.scheduled:
		add_notification(
			session,
			user_id=participant.user_id,
			type=NotificationType.invitation_revoked,
			title=f"Anda dikeluarkan dari rapat \"{meeting.title}\"",
			event_at=meeting.scheduled_start,
		)
	session.delete(participant)
	session.commit()


def respond(
	session: Session,
	meeting: Meeting,
	participant: MeetingParticipant,
	action: str,
	note: str | None,
) -> MeetingParticipant:
	"""An invitee accepting, declining, or pulling out after accepting."""
	if participant.role == ParticipantRole.organizer:
		raise MeetingValidationError("Anda penyelenggara rapat ini — batalkan rapatnya saja.")
	if meeting.status == MeetingStatus.cancelled:
		raise MeetingValidationError("Rapat ini telah dibatalkan.")

	transitions = {
		"accept": (ParticipantStatus.pending, ParticipantStatus.accepted, NotificationType.invitation_accepted, "menerima undangan"),
		"decline": (ParticipantStatus.pending, ParticipantStatus.declined, NotificationType.invitation_declined, "menolak undangan"),
		"cancel": (ParticipantStatus.accepted, ParticipantStatus.cancelled, NotificationType.invitation_cancelled, "membatalkan kehadiran di"),
	}
	required, new_status, notification_type, verb = transitions[action]
	if participant.status != required:
		raise MeetingValidationError(
			{
				"accept": "Hanya undangan yang belum dijawab yang dapat diterima.",
				"decline": "Hanya undangan yang belum dijawab yang dapat ditolak.",
				"cancel": "Anda hanya dapat membatalkan kehadiran pada undangan yang sudah diterima.",
			}[action]
		)

	note = note.strip() if note and note.strip() else None
	participant.status = new_status
	participant.response_note = None if action == "accept" else note
	participant.responded_at = utcnow()
	if action != "accept":
		# Not attending → no honorarium to chase.
		participant.has_takehome_pay = False
		participant.takehome_pay_paid = False
	session.add(participant)

	invitee = session.get(User, participant.user_id)
	add_notification(
		session,
		user_id=meeting.organizer_id,
		type=notification_type,
		title=f"{display_name(invitee)} {verb} rapat \"{meeting.title}\"",
		body=note,
		event_at=meeting.scheduled_start,
		link=meeting_link(meeting),
	)
	session.commit()
	session.refresh(participant)
	return participant


def set_my_pay(session: Session, participant: MeetingParticipant, has_pay: bool, paid: bool) -> None:
	if participant.status != ParticipantStatus.accepted:
		raise MeetingValidationError("Honorarium hanya berlaku untuk rapat yang Anda hadiri.")
	participant.has_takehome_pay = has_pay
	participant.takehome_pay_paid = paid
	validate_pay(participant)
	session.add(participant)
	session.commit()


# --- the meeting itself -----------------------------------------------------------


def _notify_active_invitees(
	session: Session,
	meeting: Meeting,
	*,
	type: NotificationType,
	title: str,
	body: str | None = None,
	link: str | None,
) -> None:
	for p in _participants(session, meeting.id):
		if p.role == ParticipantRole.invitee and p.status in ACTIVE_STATUSES:
			add_notification(
				session,
				user_id=p.user_id,
				type=type,
				title=title,
				body=body,
				link=link,
				event_at=meeting.scheduled_start,
			)


def create_meeting(session: Session, meeting_in: MeetingCreate, organizer: User) -> Meeting:
	meeting = Meeting(
		**meeting_in.model_dump(exclude={"invitee_ids", *PAY_FIELDS}),
		organizer_id=organizer.id,
	)
	validate_meeting(meeting)

	me = MeetingParticipant(
		user_id=organizer.id,
		role=ParticipantRole.organizer,
		status=ParticipantStatus.accepted,
		has_takehome_pay=meeting_in.has_takehome_pay,
		takehome_pay_paid=meeting_in.takehome_pay_paid,
		responded_at=utcnow(),
	)
	validate_pay(me)

	# Check invitees before writing anything, so a clash doesn't leave behind a
	# half-created meeting.
	invitees = (
		_check_invitees(session, meeting, organizer.id, meeting_in.invitee_ids)
		if meeting_in.invitee_ids
		else []
	)

	session.add(meeting)
	session.flush()  # assigns meeting.id for the participant rows and notification links
	me.meeting_id = meeting.id
	session.add(me)
	_stage_invites(session, meeting, organizer, invitees)
	session.commit()
	session.refresh(meeting)
	return meeting


def update_meeting(
	session: Session, meeting: Meeting, me: MeetingParticipant, meeting_in: MeetingUpdate
) -> Meeting:
	data = meeting_in.model_dump(exclude_unset=True)
	pay = {k: data.pop(k) for k in PAY_FIELDS if k in data}

	before = {f: getattr(meeting, f) for f in MATERIAL_FIELDS}
	for key, value in data.items():
		setattr(meeting, key, value)
	for key, value in pay.items():
		setattr(me, key, value)

	try:
		validate_meeting(meeting)
		validate_pay(me)
	except MeetingValidationError:
		# Both objects are attached to the session and already mutated — drop the
		# changes so a rejected update can't leak into any later flush.
		session.rollback()
		raise

	meeting.updated_at = utcnow()
	session.add(meeting)
	session.add(me)

	changed = [f for f in MATERIAL_FIELDS if getattr(meeting, f) != before[f]]
	if changed and meeting.status == MeetingStatus.scheduled:
		_notify_active_invitees(
			session,
			meeting,
			type=NotificationType.meeting_updated,
			title=f"Rapat \"{meeting.title}\" diubah",
			body="Jadwal baru" if {"scheduled_start", "scheduled_end"} & set(changed) else "Detail rapat diperbarui",
			link=meeting_link(meeting),
		)

	session.commit()
	session.refresh(meeting)
	return meeting


def cancel_meeting(session: Session, meeting: Meeting) -> Meeting:
	if meeting.status == MeetingStatus.cancelled:
		raise MeetingValidationError("Rapat ini sudah dibatalkan.")
	meeting.status = MeetingStatus.cancelled
	meeting.updated_at = utcnow()
	session.add(meeting)
	_notify_active_invitees(
		session,
		meeting,
		type=NotificationType.meeting_cancelled,
		title=f"Rapat \"{meeting.title}\" dibatalkan",
		link=meeting_link(meeting),
	)
	session.commit()
	session.refresh(meeting)
	return meeting


def delete_meeting(session: Session, meeting: Meeting) -> None:
	if meeting.status == MeetingStatus.scheduled:
		# Nothing left to link to once it's gone.
		_notify_active_invitees(
			session,
			meeting,
			type=NotificationType.meeting_cancelled,
			title=f"Rapat \"{meeting.title}\" dibatalkan",
				link=None,
		)
	# Explicit rather than relying on ON DELETE CASCADE, which SQLite skips by default.
	session.exec(delete(MeetingParticipant).where(MeetingParticipant.meeting_id == meeting.id))
	session.delete(meeting)
	session.commit()
