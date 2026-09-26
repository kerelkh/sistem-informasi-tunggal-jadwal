from pydantic import BaseModel

from app.core.time import Instant
from app.features.notifications.models import NotificationType


class NotificationRead(BaseModel):
	id: int
	type: NotificationType
	title: str
	body: str | None
	link: str | None
	event_at: Instant | None
	is_read: bool
	created_at: Instant


class UnreadCount(BaseModel):
	count: int
