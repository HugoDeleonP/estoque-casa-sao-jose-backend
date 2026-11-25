from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, func, select
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from estoque_doacoes.movimentacao.domain.entity.Movimentacao import Movimentacao
from estoque_doacoes.shared.database.db import Base, DataHoraUTC, agora

if TYPE_CHECKING:
    from estoque_doacoes.categoria.domain.entity.Categoria import Categoria
    from estoque_doacoes.unidade.domain.entity.UnidadeMedida import UnidadeMedida


class Produto(Base):
    """Item do catálogo. Pode não ter código de barras (ex.: doação a granel, sem rótulo)."""

    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_barras: Mapped[str | None] = mapped_column(String(14), default=None)
    nome: Mapped[str] = mapped_column(String(120))
    marca: Mapped[str | None] = mapped_column(String(80), default=None)
    # Conteúdo de UMA embalagem (pacote de arroz = 5 kg). O estoque continua contando
    # embalagens (movimentacao.quantidade); peso total = saldo × conteúdo × fator_base.
    conteudo_valor: Mapped[float] = mapped_column(Numeric(12, 3, asdecimal=False))
    unidade_medida_id: Mapped[int] = mapped_column(ForeignKey("unidade_medida.id"))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(DataHoraUTC, default=agora)
    updated_at: Mapped[datetime] = mapped_column(DataHoraUTC, default=agora, onupdate=agora)
    deleted_at: Mapped[datetime | None] = mapped_column(DataHoraUTC, default=None)

    # Unidirecional (@ManyToOne): sem `movimentacoes` aqui, para não induzir consultas N+1
    categoria: Mapped[Categoria] = relationship()
    unidade_medida: Mapped[UnidadeMedida] = relationship()

    __table_args__ = (
        CheckConstraint("conteudo_valor > 0", name="conteudo_positivo"),
        # Índice ÚNICO PARCIAL: o código só é único entre produtos ATIVOS (soft delete mantém
        # a linha antiga). NULL nunca colide, então vários produtos podem ficar sem código.
        Index(
            "uq_produto_codigo_ativo",
            "codigo_barras",
            unique=True,
            sqlite_where=deleted_at.is_(None),
        ),
    )

    def saldo(self) -> int:
        """SUM(movimentacao.quantidade); pode ser negativo. Valor DERIVADO, nunca gravado.
        Uma query por chamada: em listagens use MovimentacaoRepository.saldos()."""
        session = object_session(self)
        if session is None or self.id is None:
            return 0
        stmt = select(func.coalesce(func.sum(Movimentacao.quantidade), 0)).where(
            Movimentacao.produto_id == self.id
        )
        return session.scalar(stmt)

    def is_ativo(self) -> bool:
        return self.deleted_at is None

    def pode_excluir(self) -> bool:
        # Excluir com saldo ≠ 0 faria o estoque "sumir" sem movimentação que explique
        return self.saldo() == 0
