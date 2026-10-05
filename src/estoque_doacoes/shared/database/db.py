"""Engine e sessão do SQLAlchemy para SQLite."""

from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy import DateTime, MetaData, TypeDecorator, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from estoque_doacoes.shared.database.config import settings

settings.db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    # FastAPI roda endpoints síncronos num threadpool; o SQLite por padrão
    # recusa conexão usada fora da thread que a criou.
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_conn, _):
    cur = dbapi_conn.cursor()

    cur.execute("PRAGMA foreign_keys=ON")

    cur.execute("PRAGMA journal_mode=WAL")

    cur.execute("PRAGMA busy_timeout=5000")
    cur.close()


def agora() -> datetime:
    """Default das colunas de data: sempre UTC com fuso (o frontend converte para local)."""
    return datetime.now(UTC)


class DataHoraUTC(TypeDecorator[datetime]):
    """DateTime que SEMPRE volta do banco com fuso UTC.

    O SQLite não guarda fuso: sem isto, a data recém-criada sai como "...Z" e a mesma
    data relida do banco sai sem fuso — o frontend leria horários diferentes."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(UTC)  # grava sempre em UTC
        return value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    # Nomes determinísticos para TODA constraint. No SQLite o Alembic altera tabela
    # recriando-a ("batch mode"); constraint sem nome não pode ser removida/alterada depois.
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_N_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def get_session() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição."""
    with SessionLocal() as session:
        yield session
