from pydantic import BaseModel, EmailStr, Field

from app.core.time import Instant
from app.features.auth.models import UserRole


class UserCreate(BaseModel):
	email: EmailStr
	full_name: str | None = None
	password: str = Field(min_length=8, max_length=200)


class UnitSummary(BaseModel):
	id: int
	name: str


class UserRead(BaseModel):
	id: int
	email: EmailStr
	full_name: str | None
	position: str | None
	role: UserRole
	unit: UnitSummary | None
	is_active: bool
	created_at: Instant


class UserLogin(BaseModel):
	email: EmailStr
	password: str


class Token(BaseModel):
	access_token: str
	token_type: str = "bearer"


class AccountUpdate(BaseModel):
	full_name: str | None = None
	email: EmailStr | None = None


class PasswordChange(BaseModel):
	current_password: str
	new_password: str = Field(min_length=8, max_length=200)


class HasUser(BaseModel):
	exists: bool
