from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.db import get_session
from app.core.limiter import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.features.auth.crud import (
	any_user_exists,
	create_first_admin,
	get_user_by_email,
	set_password,
	to_user_read,
	update_account,
)
from app.features.auth.deps import get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import (
	AccountUpdate,
	HasUser,
	PasswordChange,
	Token,
	UserCreate,
	UserLogin,
	UserRead,
)

router = APIRouter()


@router.get("/has-user", response_model=HasUser)
def has_user(session: Session = Depends(get_session)) -> HasUser:
	return HasUser(exists=any_user_exists(session))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, session: Session = Depends(get_session)) -> UserRead:
	# Registration only bootstraps the very first administrator. Every account after
	# that is created by an administrator from the Users screen.
	if any_user_exists(session):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pendaftaran sudah ditutup.")
	return to_user_read(session, create_first_admin(session, user_in))


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user_in: UserLogin, session: Session = Depends(get_session)) -> Token:
	user = get_user_by_email(session, user_in.email)
	if not user or not verify_password(user_in.password, user.hashed_password):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email atau kata sandi salah.")
	if not user.is_active:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akun ini telah dinonaktifkan.")
	return Token(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=UserRead)
def me(
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> UserRead:
	return to_user_read(session, current_user)


@router.put("/me", response_model=UserRead)
def update_me(
	update_in: AccountUpdate,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> UserRead:
	if update_in.email and update_in.email != current_user.email:
		existing = get_user_by_email(session, update_in.email)
		if existing and existing.id != current_user.id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah digunakan.")
	return to_user_read(session, update_account(session, current_user, update_in))


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
	change_in: PasswordChange,
	session: Session = Depends(get_session),
	current_user: User = Depends(get_current_user),
) -> None:
	if not verify_password(change_in.current_password, current_user.hashed_password):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kata sandi saat ini salah.")
	set_password(session, current_user, hash_password(change_in.new_password))
