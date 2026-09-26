from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.features.notifications.models import Notification, NotificationType

LIST_LIMIT = 20


def add_notification(
	session: Session,
	*,
	user_id: int,
	type: NotificationType,
	title: str,
	body: str | None = None,
	link: str | None = None,
	event_at: datetime | None = None,
) -> None:
	"""Stages a notification without committing, so it lands in the same transaction
	as the change it describes — an invite never exists without its notification."""
	session.add(
		Notification(user_id=user_id, type=type, title=title, body=body, link=link, event_at=event_at)
	)


def list_notifications(session: Session, user_id: int, *, limit: int = LIST_LIMIT) -> list[Notification]:
	return list(
		session.exec(
			select(Notification)
			.where(Notification.user_id == user_id)
			.order_by(Notification.created_at.desc())
			.limit(limit)
		).all()
	)


def count_unread(session: Session, user_id: int) -> int:
	return session.exec(
		select(func.count())
		.select_from(Notification)
		.where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
	).one()


def get_notification(session: Session, notification_id: int, user_id: int) -> Notification | None:
	"""Only ever returns the caller's own notification — someone else's reads as not found."""
	notification = session.get(Notification, notification_id)
	return notification if notification and notification.user_id == user_id else None


def set_read(session: Session, notification: Notification, is_read: bool) -> Notification:
	notification.is_read = is_read
	session.add(notification)
	session.commit()
	session.refresh(notification)
	return notification


def mark_all_read(session: Session, user_id: int) -> None:
	notifications = session.exec(
		select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
	).all()
	for notification in notifications:
		notification.is_read = True
		session.add(notification)
	session.commit()


def delete_notification(session: Session, notification: Notification) -> None:
	session.delete(notification)
	session.commit()
