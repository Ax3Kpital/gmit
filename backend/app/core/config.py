from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://gmit:gmit@localhost:5432/gmit"
    secret_key: str = "dev-secret-change-in-production-32chars"
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]

    llm_provider: str = "mock"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    fred_api_key: str = ""
    eia_api_key: str = ""

    session_expire_hours: int = 24 * 7  # 7 days

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
