from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./nextwatch.db"
    secret_key: str = "change-this-before-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    google_client_id: str = """"""
    tmdb_api_key: str = ""
    cors_origins: str = "http://localhost:5173"
    admin_emails: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
