from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from estoque_doacoes.db import Base

if TYPE_CHECKING:
    from estoque_doacoes.model.entity.Produto import Produto


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)

    produtos: Mapped[list[Produto]] = relationship(back_populates="categoria")
