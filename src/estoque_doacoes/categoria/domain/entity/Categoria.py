from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from estoque_doacoes.shared.database.db import Base, DataHoraUTC


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    deleted_at: Mapped[datetime | None] = mapped_column(DataHoraUTC, default=None)

    # Sem `produtos` (coleção inversa) de propósito: navegação unidirecional Produto → Categoria.

    __table_args__ = (
        # Nome único só entre categorias ATIVAS: permite recriar uma categoria excluída
        Index("uq_categoria_nome_ativa", "nome", unique=True, sqlite_where=deleted_at.is_(None)),
    )

    def is_ativa(self) -> bool:
        return self.deleted_at is None
