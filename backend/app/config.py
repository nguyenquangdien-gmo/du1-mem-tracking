from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5500,http://localhost:3000,http://localhost:5500"

    # ChatOps (Mattermost) settings
    chatops_url: str = "https://chat.runsystem.vn"
    chatops_token: str = ""
    chatops_assistant_id: str = ""
    
    # DB SSL settings
    database_ssl_ca: str = ""
    database_ssl: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
