from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.core.security import hash_password
from app.features.auth.models import User, UserRole
from app.features.units.models import Unit
from app.features.users.schemas import AdminUserCreate, AdminUserUpdate


class UserValidationError(ValueError):
	"""Raised when a user's fields contradict each other."""


def validate_user(session: Session, user: User) -> None:
	"""Checks the resolved record, so a partial update is judged after it's applied."""
	if user.role == UserRole.user and user.unit_id is None:
		raise UserValidationError("Pengguna biasa wajib terdaftar di sebuah unit kerja.")
	if user.unit_id is not None and session.get(Unit, user.unit_id) is None:
		raise UserValidationError("Unit kerja tersebut tidak ditemukan.")


def search_users(
	session: Session,
	*,
	q: str | None = None,
	unit_id: int | None = None,
	ids: list[int] | None = None,
	active_only: bool = False,
	limit: int | None = None,
) -> list[User]:
	stmt = select(User)
	if q and q.strip():
		pattern = f"%{q.strip().lower()}%"
		stmt = stmt.where(
			or_(
				func.lower(User.full_name).like(pattern),
				func.lower(User.email).like(pattern),
				func.lower(User.position).like(pattern),
			)
		)
	if unit_id is not None:
		stmt = stmt.where(User.unit_id == unit_id)
	if ids is not None:
		stmt = stmt.where(User.id.in_(ids))
	if active_only:
		stmt = stmt.where(User.is_active == True)  # noqa: E712
	stmt = stmt.order_by(User.full_name, User.email)
	if limit:
		stmt = stmt.limit(limit)
	return list(session.exec(stmt).all())


def create_user(session: Session, user_in: AdminUserCreate) -> User:
	user = User(
		**user_in.model_dump(exclude={"password"}),
		hashed_password=hash_password(user_in.password),
	)
	validate_user(session, user)
	session.add(user)
	session.commit()
	session.refresh(user)
	return user


def update_user(session: Session, user: User, user_in: AdminUserUpdate) -> User:
	for key, value in user_in.model_dump(exclude_unset=True).items():
		setattr(user, key, value)
	try:
		validate_user(session, user)
	except UserValidationError:
		session.rollback()
		raise
	session.add(user)
	session.commit()
	session.refresh(user)
	return user


def reset_password(session: Session, user: User, new_password: str) -> None:
	user.hashed_password = hash_password(new_password)
	session.add(user)
	session.commit()
