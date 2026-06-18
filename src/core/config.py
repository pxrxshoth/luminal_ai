from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Luminal AI"
    POSTGRES_URL: str = "postgresql://luminal:luminal@localhost:5432/luminal_db"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    OPENAI_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    PINECONE_ENV: str = ""
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
