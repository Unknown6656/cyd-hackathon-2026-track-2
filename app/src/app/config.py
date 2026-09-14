from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_level: str = "INFO"
    openai_url: str = "https://litellm.hackathon.intlab.ch/v1"
    openai_api_key: str = "EMPTY"
    model_name: str = "Qwen/Qwen3.8-Flash-Next"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()