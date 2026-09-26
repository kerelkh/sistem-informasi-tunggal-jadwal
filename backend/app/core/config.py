from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	app_name: str = "SITUNG API"
	database_url: str = "sqlite:///./situng.db"

	jwt_secret_key: str = "dev-secret-change-me-32-bytes-minimum"
	jwt_algorithm: str = "HS256"
	access_token_expire_minutes: int = 60 * 24


settings = Settings()
