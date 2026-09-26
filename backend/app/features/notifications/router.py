from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.db import get_session
from app.features.auth.deps import get_current_user
from app.features.auth.models import User
from app.features.notifications.crud import (
	count_unread,
	delete_notification,
	get_notification,
	list_notifications,
	mark_all_read,
	set_read,
)
from app.features.notifications.schemas import NotificationRead, UnreadCount

router = APIRouter()


@router.get("", response_model=list[NotificationRead])
def read_notifications(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> list[NotificationRead]:
	return list_notifications(session, current_user.id)


@router.get("/unread-count", response_model=UnreadCount)
def read_unread_count(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> UnreadCount:
	return UnreadCount(count=count_unread(session, current_user.id))


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> None:
	mark_all_read(session, current_user.id)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def set_notification_read(
	notification_id: int,
	is_read: bool = True,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> NotificationRead:
	notification = get_notification(session, notification_id, current_user.id)
	if not notification:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notifikasi tidak ditemukan.")
	return set_read(session, notification, is_read)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_notification(
	notification_id: int,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> None:
	notification = get_notification(session, notification_id, current_user.id)
	if not notification:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notifikasi tidak ditemukan.")
	delete_notification(session, notification)
