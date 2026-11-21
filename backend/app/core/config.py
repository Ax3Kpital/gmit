from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://gmit:gmit@localhost:5432/gmit"
    secret_key: str = "dev-secret-change-in-production-32chars"
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]

    llm_provider: str = "mock"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    openai_api_key: str = ""

    fred_api_key: str = ""
    eia_api_key: str = ""

    # Email (SMTP)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_address: str = ""
    notification_email: str = ""

    # Telegram bot
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    session_expire_hours: int = 24 * 7  # 7 days

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def email_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password and self.notification_email)

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


settings = Settings()
