from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DO NOT CHANGE - provided by organizers.
    openai_base_url: str = "https://litellm.hackathon.intlab.ch/v1"
    openai_api_key: str = "EMPTY"
    model: str = "Qwen/Qwen3.8-Flash-Next"

    # The data is mounted read-only at /corpus:
    #   legislation/    20 PDFs   KMG, KMV, GKG, GKV, EmbG in de/fr/it/en
    #   control_lists/   6 PDFs   dual-use list and Annex 3, de/fr/it only
    #   parties/        public_sanctions.json, internal_flagged.json
    corpus_dir: str = "/corpus"
    output_dir: str = "/output"
    data_dir: str = "/data"

    # app config
    log_level: str = "INFO"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str = ""
    embedding_model: str = "qwen3-embedding:8b"
    vector_size: int = 4096

    ekn_collection_name: str = "control_lists"
    legislation_collection_name: str = "legislation"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
