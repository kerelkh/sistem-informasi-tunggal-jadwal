# Import every feature's models module here so Alembic's autogenerate can discover it.
from app.features.auth.models import User
from app.features.meetings.models import Meeting, MeetingParticipant
from app.features.notifications.models import Notification
from app.features.units.models import Unit

__all__ = [
	"Unit",
	"User",
	"Meeting",
	"MeetingParticipant",
	"Notification",
]
