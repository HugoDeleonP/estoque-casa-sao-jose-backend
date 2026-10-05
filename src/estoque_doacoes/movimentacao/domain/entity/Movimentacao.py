from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from estoque_doacoes.movimentacao.domain.enum.TipoMovimentacao import TipoMovimentacao
from estoque_doacoes.shared.database.db import Base, DataHoraUTC, agora

if TYPE_CHECKING:
    from estoque_doacoes.produto.domain.entity.Produto import Produto


class Movimentacao(Base):
    """Fonte da verdade do estoque e IMUTÁVEL após criada. A quantidade já carrega o sinal
    (SAIDA < 0), então saldo = SUM(quantidade), sem CASE."""

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
    created_at: Mapped[datetime] = mapped_column(DataHoraUTC, default=agora, index=True)

    # Unidirecional (@ManyToOne)
    produto: Mapped[Produto] = relationship()

    __table_args__ = (
        # Regra no BANCO, não só na API: protege contra bug no service ou script manual.
        # Nome curto: a naming convention (shared/database/db.py) gera "ck_movimentacao_…".
        CheckConstraint(
            "(tipo = 'ENTRADA' AND quantidade > 0)"
            " OR (tipo = 'SAIDA' AND quantidade < 0)"
            " OR (tipo = 'AJUSTE' AND quantidade <> 0"
            " AND observacao IS NOT NULL AND trim(observacao) <> '')",
            name="quantidade_por_tipo",
        ),
    )
