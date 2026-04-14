from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # PostgreSQL
    POSTGRES_HOST: str = "192.168.2.8"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "rag_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "root"
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20

    # Milvus
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_TOKEN: str = "root:Milvus"        # default creds — change if auth is customised
    MILVUS_DB_NAME: str = "default"
    MILVUS_COLLECTION: str = "document_chunks"
    SECURE: bool = False

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


setting = Settings()