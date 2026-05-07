from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://evaluser:evalpass@db:5432/evallab"
    cors_origins: str = "http://localhost:5173"
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def provider_configured(self) -> bool:
        if self.llm_provider == "mock":
            return True
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return False


settings = Settings()
