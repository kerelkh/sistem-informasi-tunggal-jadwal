"""User administration. Accounts are only ever created here, by an administrator —
there is no self-registration beyond bootstrapping the first admin."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.db import get_session
from app.features.auth.crud import get_user, get_user_by_email, to_user_read
from app.features.auth.deps import require_admin
from app.features.auth.models import User, UserRole
from app.features.auth.schemas import UserRead
from app.features.users.crud import (
	UserValidationError,
	create_user,
	reset_password,
	search_users,
	update_user,
)
from app.features.users.schemas import AdminUserCreate, AdminUserUpdate, PasswordReset

router = APIRouter()


@router.get("", response_model=list[UserRead])
def admin_list_users(
	q: str | None = None,
	unit_id: int | None = Query(default=None),
	session: Session = Depends(get_session),
	admin: User = Depends(require_admin),
) -> list[UserRead]:
	return [to_user_read(session, u) for u in search_users(session, q=q, unit_id=unit_id)]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def admin_create_user(
	user_in: AdminUserCreate,
	session: Session = Depends(get_session),
	admin: User = Depends(require_admin),
) -> UserRead:
	if get_user_by_email(session, user_in.email):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah terdaftar.")
	try:
		return to_user_read(session, create_user(session, user_in))
	except UserValidationError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{user_id}", response_model=UserRead)
def admin_update_user(
	user_id: int,
	user_in: AdminUserUpdate,
	session: Session = Depends(get_session),
	admin: User = Depends(require_admin),
) -> UserRead:
	user = get_user(session, user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pengguna tidak ditemukan.")

	# An admin who demotes or deactivates themselves could leave nobody able to
	# manage accounts — make another admin do it.
	if user.id == admin.id and (
		(user_in.role is not None and user_in.role != UserRole.admin) or user_in.is_active is False
	):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Anda tidak dapat mencabut akses administrator atau menonaktifkan akun Anda sendiri.",
		)

	if user_in.email and user_in.email != user.email:
		existing = get_user_by_email(session, user_in.email)
		if existing and existing.id != user.id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah digunakan.")

	try:
		return to_user_read(session, update_user(session, user, user_in))
	except UserValidationError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def admin_reset_password(
	user_id: int,
	reset_in: PasswordReset,
	session: Session = Depends(get_session),
	admin: User = Depends(require_admin),
) -> None:
	user = get_user(session, user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pengguna tidak ditemukan.")
	reset_password(session, user, reset_in.new_password)
