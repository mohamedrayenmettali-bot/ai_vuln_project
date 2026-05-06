import os
from pydantic_settings import BaseSettings, SettingsConfigDict

def _csv_env(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else ["*"]

class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "info"
    
    API_TITLE: str = "AI Vulnerability Risk API"
    API_DESCRIPTION: str = (
        "Real-time vulnerability risk scoring powered by a SecureBERT NLP + "
        "5-model stacked ensemble. Trained on CVEfixes with EPSS enrichment."
    )
    API_VERSION: str = "1.0.0"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    ROOT_PATH: str = "/"
    HEALTH_PATH: str = "/health"
    
    REQUEST_ID_HEADER: str = "X-Request-ID"
    PROCESS_TIME_HEADER: str = "X-Process-Time"
    
    CORS_ALLOWED_ORIGINS: str = "*"
    
    @property
    def CORS_ALLOW_ORIGINS(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    DEFAULT_CORS_ALLOW_METHODS: list[str] = ["*"]
    DEFAULT_CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    PREDICT_BATCH_MAX_FINDINGS: int = 200
    EPSS_BATCH_MAX_CVES: int = 100
    
    DEFAULT_NLP_MODEL_NAME: str = "cisco-ai/SecureBERT2.0-biencoder"
    ENCODER_WARMUP_TEXT: str = "warm-up"

    MODEL_LOADING_MESSAGE: str = "Model artifacts are still loading. Please retry shortly."
    MODEL_NOT_LOADED_MESSAGE: str = "Model not yet loaded."
    SERVICE_NOT_READY_MESSAGE: str = "Service not ready - model or NLP encoder still loading."
    PREDICTION_FAILED_MESSAGE: str = "Prediction failed."
    BATCH_PREDICTION_FAILED_MESSAGE: str = "Batch prediction failed."
    MODEL_RELOAD_FAILED_MESSAGE: str = "Model reload failed."

    EPSS_NOT_FOUND_TEMPLATE: str = "{cve_id} not found in EPSS database."
    EPSS_SOURCE_NAME: str = "FIRST.org API"
    
    # DefectDojo Integration
    DEFECTDOJO_URL: str = "http://localhost:8080"
    DEFECTDOJO_API_TOKEN: str = ""
    USE_EPSS: bool = True
    AUTH_SESSION_TTL_SECONDS: int = 12 * 60 * 60
    PASSWORD_RESET_TOKEN_TTL_SECONDS: int = 30 * 60
    PASSWORD_RESET_URL_TEMPLATE: str = "http://localhost:3000/reset-password?token={token}"

    # SMTP mail delivery for password resets.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "SecureOps"
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SAST_INGESTION_TARGET: str = "database"

    
    # DB vars
    DATABASE_URL: str | None = None
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "ai_vuln_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
