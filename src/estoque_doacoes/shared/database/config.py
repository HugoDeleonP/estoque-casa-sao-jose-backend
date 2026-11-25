"""Configuração lida de variáveis de ambiente / arquivo .env."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[4]


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
    # Pasta com o build do Vue (dist/). Ausente/inexistente → a API sobe sem servir o front.
    front_dist: Path | None = None

    @field_validator("db_path", "front_dist")
    @classmethod
    def _relativo_ao_backend(cls, v: Path | None) -> Path | None:
        # Caminho relativo no .env é resolvido a partir de backend/, NÃO da pasta onde o
        # comando foi rodado — senão rodar da raiz do repo cria um segundo banco vazio.
        if v is None:
            return None
        return v if v.is_absolute() else (BACKEND_DIR / v).resolve()

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
