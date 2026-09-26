from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.db import get_session
from app.core.security import decode_access_token
from app.features.auth.crud import get_user
from app.features.auth.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
	token: str | None = Depends(oauth2_scheme),
	session: Session = Depends(get_session),
) -> User:
	credentials_error = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Sesi tidak valid. Silakan masuk kembali.",
		headers={"WWW-Authenticate": "Bearer"},
	)

	if token is None:
		raise credentials_error

	user_id = decode_access_token(token)
	if user_id is None:
		raise credentials_error

	user = get_user(session, int(user_id))
	if user is None or not user.is_active:
		raise credentials_error

	return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
	if current_user.role != UserRole.admin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya administrator yang dapat melakukan ini.")
	return current_user
