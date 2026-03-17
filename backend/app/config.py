from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama
    ollama_host: str = "http://ollama:11434"
    llm_model: str = "phi3.5:mini-instruct"
    embed_model: str = "nomic-embed-text"
    ollama_num_gpu: int = 1

    # Qdrant
    qdrant_host: str = "http://qdrant:6333"
    qdrant_collection: str = "books"

    # Backend
    upload_dir: str = "/app/uploads"
    db_path: str = "/app/data/db.sqlite"
    max_upload_size_mb: int = 200
    chunk_size: int = 300
    chunk_overlap: int = 50
    parent_chunk_size: int = 1000
    top_k_results: int = 6

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
