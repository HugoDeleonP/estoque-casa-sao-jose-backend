from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from estoque_doacoes.shared.database.db import Base, DataHoraUTC, agora
from estoque_doacoes.unidade.domain.enum.Grandeza import Grandeza


class UnidadeMedida(Base):
    """Unidade do CONTEÚDO de uma embalagem (ex.: pacote de 5 kg). `fator_base` converte
    para a unidade base da grandeza: g → kg = 0,001; dz → un = 12."""

    __tablename__ = "unidade_medida"

    id: Mapped[int] = mapped_column(primary_key=True)
    sigla: Mapped[str] = mapped_column(String(10))
    nome: Mapped[str] = mapped_column(String(40))
    grandeza: Mapped[Grandeza] = mapped_column(
        Enum(Grandeza, native_enum=False, create_constraint=True, length=10)
    )
    # asdecimal=False: o SQLite não tem DECIMAL nativo; float basta para fatores de conversão
    fator_base: Mapped[float] = mapped_column(Numeric(14, 6, asdecimal=False))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(DataHoraUTC, default=agora)
    deleted_at: Mapped[datetime | None] = mapped_column(DataHoraUTC, default=None)

    __table_args__ = (
        CheckConstraint("fator_base > 0", name="fator_base_positivo"),
        Index(
            "uq_unidade_medida_sigla_ativa",
            "sigla",
            unique=True,
            sqlite_where=deleted_at.is_(None),
        ),
    )

    def is_ativa(self) -> bool:
        return self.deleted_at is None
