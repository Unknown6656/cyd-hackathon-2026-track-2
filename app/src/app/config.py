from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DO NOT CHANGE - provided by organizers.
    openai_base_url: str = "https://litellm.hackathon.intlab.ch/v1"
    openai_api_key: str = "EMPTY"
    model: str = "Qwen/Qwen3.8-Flash-Next"

    # app config
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    qdrant_url:str = "http://qdrant:6333"

    embedding_model: str = "qwen3-embedding:8b"
    vector_size: int = 4096

settings = Settings()
