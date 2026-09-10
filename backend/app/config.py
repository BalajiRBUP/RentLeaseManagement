from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central app configuration.
    Values are loaded from a .env file (copy .env.example to .env and edit it).
    """
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/rent_lease_db"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    # Local, free AI chatbot (Ollama) - no external API, nothing leaves the machine.
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
