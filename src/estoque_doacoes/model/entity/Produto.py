from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from estoque_doacoes.db import Base

if TYPE_CHECKING:
    from estoque_doacoes.model.entity.Categoria import Categoria
    from estoque_doacoes.model.entity.Movimentacao import Movimentacao


def agora() -> datetime:
    return datetime.now(UTC)


class Produto(Base):
    """Um SKU: cada código de barras = um produto com embalagem de tamanho fixo."""

    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_barras: Mapped[str] = mapped_column(String(14))
    nome: Mapped[str] = mapped_column(String(120))
    embalagem: Mapped[str] = mapped_column(String(30))  # ex.: "1 kg", "lata 350 g"
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    categoria: Mapped[Categoria] = relationship(back_populates="produtos")
    movimentacoes: Mapped[list[Movimentacao]] = relationship(back_populates="produto")

    __table_args__ = (
        # Índice ÚNICO PARCIAL: o código só é único entre produtos ATIVOS.
        # Um UNIQUE comum impediria recadastrar um código cujo produto foi excluído
        # (soft delete mantém a linha antiga na tabela).
        Index(
            "uq_produto_codigo_ativo",
            "codigo_barras",
            unique=True,
            sqlite_where=deleted_at.is_(None),
        ),
    )

    @property
    def ativo(self) -> bool:
        return self.deleted_at is None
