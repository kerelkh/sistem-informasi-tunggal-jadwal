"""Units. Everyone signed in can list them (they drive filters and the availability
page); only administrators can change them."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.db import get_session
from app.features.auth.deps import get_current_user, require_admin
from app.features.auth.models import User
from app.features.units.crud import (
	count_members,
	create_unit,
	delete_unit,
	get_unit,
	get_unit_by_name,
	list_units,
	to_unit_read,
	update_unit,
)
from app.features.units.schemas import UnitCreate, UnitRead, UnitUpdate

router = APIRouter()


@router.get("", response_model=list[UnitRead])
def read_units(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> list[UnitRead]:
	return list_units(session)


@router.post("", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
def admin_create_unit(
	unit_in: UnitCreate,
	session: Session = Depends(get_session),
	admin: User = Depends(require_admin),
) -> UnitRead:
	if get_unit_by_name(session, unit_in.name):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit kerja dengan nama tersebut sudah ada.")
	return to_unit_read(session, create_unit(session, unit_in))


@router.put("/{unit_id}", response_model=UnitRead)
def admin_update_unit(
	unit_id: int,
	unit_in: UnitUpdate,
	session: Session = Depends(get_session),
	admin: User = Depends(require_admin),
) -> UnitRead:
	unit = get_unit(session, unit_id)
	if not unit:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit kerja tidak ditemukan.")
	if unit_in.name:
		existing = get_unit_by_name(session, unit_in.name)
		if existing and existing.id != unit.id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit kerja dengan nama tersebut sudah ada.")
	return to_unit_read(session, update_unit(session, unit, unit_in))


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_unit(
	unit_id: int,
	session: Session = Depends(get_session),
	admin: User = Depends(require_admin),
) -> None:
	unit = get_unit(session, unit_id)
	if not unit:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit kerja tidak ditemukan.")
	# Refuse rather than orphan people: move or deactivate the members first.
	if count_members(session, unit.id) > 0:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Unit kerja ini masih memiliki anggota. Pindahkan anggotanya ke unit kerja lain terlebih dahulu.",
		)
	delete_unit(session, unit)
