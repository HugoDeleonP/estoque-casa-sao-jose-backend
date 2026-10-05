"""Ambiente do Alembic. Usado tanto pela CLI (`uv run alembic ...`) quanto
programaticamente na inicialização da API (estoque_doacoes.migrar)."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

# Importar todas as entidades registra suas tabelas no metadata (create_all/autogenerate).
# Módulo novo com tabela → adicionar aqui.
import estoque_doacoes.categoria.domain.entity.Categoria  # noqa: F401
import estoque_doacoes.movimentacao.domain.entity.Movimentacao  # noqa: F401
import estoque_doacoes.produto.domain.entity.Produto  # noqa: F401
from estoque_doacoes.shared.database.db import Base, engine

config = context.config

# Pela CLI, configura logging pelo alembic.ini. Pela API, NÃO — senão o Alembic
# sobrescreve a configuração de log do uvicorn.
if config.config_file_name is not None and config.attributes.get("configurar_log", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configurar(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # SQLite não suporta a maioria dos ALTER TABLE: o batch mode recria a tabela
        # (cria nova → copia dados → apaga antiga → renomeia).
        render_as_batch=True,
        compare_type=True,
    )


def run_migrations_offline() -> None:
    """`alembic upgrade head --sql`: gera o SQL sem tocar no banco (útil para revisar)."""
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Reaproveita a MESMA engine da aplicação: mesmo arquivo (.env) e mesmos PRAGMAs.
    connectable = config.attributes.get("connection") or engine
    if isinstance(connectable, Connection):
        _rodar(connectable)
        return
    with connectable.connect() as connection:
        _rodar(connection)


def _rodar(connection: Connection) -> None:
    # O batch mode apaga e recria tabelas; com FK ligada, apagar `produto` falharia
    # (movimentacao aponta para ele). Desliga só durante a migração e confere no fim.
    # PRAGMA foreign_keys é ignorado dentro de transação, por isso vem antes do begin.
    connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
    # SQLAlchemy 2.0 abre transação implícita (autobegin) no comando acima; encerrá-la
    # é o que permite ao Alembic abrir e COMMITAR a própria transação depois.
    connection.commit()
    try:
        _configurar(connection)
        with context.begin_transaction():
            context.run_migrations()
        violacoes = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violacoes:
            raise RuntimeError(f"Migração deixou FKs inválidas: {violacoes}")
    finally:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
