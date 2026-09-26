from sqlalchemy import func
from sqlmodel import Session, select

from app.features.auth.models import User
from app.features.units.models import Unit
from app.features.units.schemas import UnitCreate, UnitRead, UnitUpdate


def get_unit(session: Session, unit_id: int) -> Unit | None:
	return session.get(Unit, unit_id)


def get_unit_by_name(session: Session, name: str) -> Unit | None:
	return session.exec(select(Unit).where(func.lower(Unit.name) == name.strip().lower())).first()


def count_members(session: Session, unit_id: int) -> int:
	return session.exec(select(func.count()).select_from(User).where(User.unit_id == unit_id)).one()


def to_unit_read(session: Session, unit: Unit) -> UnitRead:
	return UnitRead(**unit.model_dump(), member_count=count_members(session, unit.id))


def list_units(session: Session) -> list[UnitRead]:
	counts = dict(
		session.exec(
			select(User.unit_id, func.count()).where(User.unit_id.is_not(None)).group_by(User.unit_id)
		).all()
	)
	units = session.exec(select(Unit).order_by(Unit.name)).all()
	return [UnitRead(**u.model_dump(), member_count=counts.get(u.id, 0)) for u in units]


def create_unit(session: Session, unit_in: UnitCreate) -> Unit:
	unit = Unit(**unit_in.model_dump())
	unit.name = unit.name.strip()
	session.add(unit)
	session.commit()
	session.refresh(unit)
	return unit


def update_unit(session: Session, unit: Unit, unit_in: UnitUpdate) -> Unit:
	for key, value in unit_in.model_dump(exclude_unset=True).items():
		setattr(unit, key, value.strip() if key == "name" and value else value)
	session.add(unit)
	session.commit()
	session.refresh(unit)
	return unit


def delete_unit(session: Session, unit: Unit) -> None:
	session.delete(unit)
	session.commit()
