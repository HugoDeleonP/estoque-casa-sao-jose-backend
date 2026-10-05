"""Aplica migrações pendentes do Alembic de dentro da aplicação.

Na máquina da ONG ninguém vai rodar `alembic upgrade head` num terminal:
a API faz isso sozinha ao iniciar. Atualizar o sistema = substituir os arquivos
e reabrir; o banco é migrado automaticamente, preservando os dados.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def alembic_config(connection: Connection | None = None) -> Config:
    # Sem depender do alembic.ini: os scripts vivem DENTRO do pacote, então
    # vão junto no wheel e no PyInstaller.
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.attributes["configurar_log"] = False
    if connection is not None:
        cfg.attributes["connection"] = connection
    return cfg


def migrar(connection: Connection | None = None) -> None:
    command.upgrade(alembic_config(connection), "head")
