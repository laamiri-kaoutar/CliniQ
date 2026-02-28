from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CliniQ API"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str
    COHERE_API_KEY: str 
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
   
    MLFLOW_TRACKING_URI: str = "http://cliniq_mlflow:5000"
    
    EXPANSION_MODEL: str = "gemini-2.5-flash-lite"
    EXPANSION_TEMP: float = 0.2
    
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RETRIEVAL_K: int = 5
    
    RERANK_MODEL: str = "rerank-multilingual-v3.0"
    RERANK_TOP_N: int = 3
    
    GENERATOR_MODEL: str = "gemini-flash-latest"
    GENERATOR_TEMP: float = 0.0

    class Config:
        env_file = ".env"

settings = Settings()