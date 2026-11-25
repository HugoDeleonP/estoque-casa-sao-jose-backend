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

    # ---------- Sessão (cookie assinado) ----------
    # Em produção vem de /etc/estoque/env. Ausente → chave aleatória por processo
    # (as sessões caem a cada reinício; aceitável só em desenvolvimento).
    secret_key: str | None = None
    # true em produção (HTTPS). Em http://localhost o navegador descartaria o cookie Secure.
    cookie_secure: bool = False
    sessao_horas: int = 12
    # Custo do bcrypt (2^n iterações). 12 ≈ 0,25 s por login na t3.micro; testes usam 4.
    bcrypt_rounds: int = 12

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
