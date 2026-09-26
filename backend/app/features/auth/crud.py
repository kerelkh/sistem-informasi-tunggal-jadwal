from sqlalchemy import func
from sqlmodel import Session, select

from app.core.security import hash_password
from app.features.auth.models import User, UserRole
from app.features.auth.schemas import AccountUpdate, UnitSummary, UserCreate, UserRead
from app.features.units.models import Unit


def any_user_exists(session: Session) -> bool:
	return session.exec(select(func.count()).select_from(User)).one() > 0


def get_user_by_email(session: Session, email: str) -> User | None:
	return session.exec(select(User).where(User.email == email)).first()


def get_user(session: Session, user_id: int) -> User | None:
	return session.get(User, user_id)


def to_user_read(session: Session, user: User) -> UserRead:
	unit = session.get(Unit, user.unit_id) if user.unit_id else None
	return UserRead(
		**user.model_dump(exclude={"hashed_password", "unit_id"}),
		unit=UnitSummary(id=unit.id, name=unit.name) if unit else None,
	)


def create_first_admin(session: Session, user_in: UserCreate) -> User:
	user = User(
		email=user_in.email,
		full_name=user_in.full_name,
		hashed_password=hash_password(user_in.password),
		role=UserRole.admin,
	)
	session.add(user)
	session.commit()
	session.refresh(user)
	return user


def update_account(session: Session, user: User, update_in: AccountUpdate) -> User:
	data = update_in.model_dump(exclude_unset=True)
	for key, value in data.items():
		setattr(user, key, value)
	session.add(user)
	session.commit()
	session.refresh(user)
	return user


def set_password(session: Session, user: User, hashed_password: str) -> User:
	user.hashed_password = hashed_password
	session.add(user)
	session.commit()
	session.refresh(user)
	return user
