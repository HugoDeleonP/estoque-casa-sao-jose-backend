"""Configuração lida de variáveis de ambiente / arquivo .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_prefix="ESTOQUE_",
        extra="ignore",
    )

    db_path: Path = BACKEND_DIR / "data" / "estoque.db"
    host: str = "127.0.0.1" 
    port: int = 8000
    debug: bool = False

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
