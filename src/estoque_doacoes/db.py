"""Engine e sessão do SQLAlchemy para SQLite."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from estoque_doacoes.config import settings

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


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição."""
    with SessionLocal() as session:
        yield session
