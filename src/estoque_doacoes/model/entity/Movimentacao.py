from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from estoque_doacoes.db import Base
from estoque_doacoes.model.entity.Produto import agora

if TYPE_CHECKING:
    from estoque_doacoes.model.entity.Produto import Produto

class Movimentacao(Base):
    """Fonte da verdade do estoque. O saldo é SEMPRE derivado daqui (SUM), nunca gravado."""

    __tablename__ = "movimentacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), index=True)
    tipo: Mapped[TipoMovimentacao] = mapped_column(
        # native_enum=False → VARCHAR + CHECK no SQLite (que não tem tipo ENUM)
        Enum(TipoMovimentacao, native_enum=False, create_constraint=True, length=10)
    )
    quantidade: Mapped[int]
    observacao: Mapped[str | None] = mapped_column(String(200), default=None)
    # Indexado: o dashboard filtra por período
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)

    produto: Mapped[Produto] = relationship(back_populates="movimentacoes")

    __table_args__ = (
        # Regra no BANCO, não só na API: protege contra bug no service ou script manual
        CheckConstraint(
            "(tipo = 'AJUSTE' AND quantidade <> 0) OR (tipo <> 'AJUSTE' AND quantidade > 0)",
            name="ck_movimentacao_quantidade_por_tipo",
        ),
    )
