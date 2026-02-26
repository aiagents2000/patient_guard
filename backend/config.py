"""
Configurazione centralizzata per il backend PatientGuard.

Carica variabili d'ambiente da .env e fornisce settings tipizzati.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings dell'applicazione, caricati da variabili d'ambiente."""

    # App
    app_name: str = "PatientGuard API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "info"

    # Supabase
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # LLM (OpenAI o Anthropic)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # CORS — frontend Vercel
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # ML
    ml_models_dir: str = "ml/models"

    # JSON fallback (demo senza DB)
    demo_json_path: str = "data/sample/synthetic_patients.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def use_supabase(self) -> bool:
        """True se le credenziali Supabase sono configurate."""
        return bool(self.supabase_url and self.supabase_key)

    @property
    def use_llm(self) -> bool:
        """True se almeno un provider LLM è configurato."""
        return bool(self.openai_api_key or self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
