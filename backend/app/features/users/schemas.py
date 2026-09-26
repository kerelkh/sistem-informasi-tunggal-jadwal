from pydantic import BaseModel, EmailStr, Field

from app.features.auth.models import UserRole


class AdminUserCreate(BaseModel):
	email: EmailStr
	full_name: str = Field(min_length=1, max_length=200)
	position: str | None = None
	password: str = Field(min_length=8, max_length=200)
	role: UserRole = UserRole.user
	unit_id: int | None = None


class AdminUserUpdate(BaseModel):
	email: EmailStr | None = None
	full_name: str | None = Field(default=None, min_length=1, max_length=200)
	position: str | None = None
	role: UserRole | None = None
	unit_id: int | None = None
	is_active: bool | None = None


class PasswordReset(BaseModel):
	new_password: str = Field(min_length=8, max_length=200)
