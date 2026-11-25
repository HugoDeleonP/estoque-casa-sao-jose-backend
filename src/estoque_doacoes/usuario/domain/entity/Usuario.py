from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from estoque_doacoes.shared.database.db import Base, DataHoraUTC, agora
from estoque_doacoes.usuario.domain.enum.Role import Role


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))  # sempre minúsculo (normalizado no DTO)
    senha_hash: Mapped[str] = mapped_column(String(100))  # bcrypt; a senha nunca é gravada
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, create_constraint=True, length=10)
    )
    # Incrementada ao trocar senha/perfil ou desativar: derruba as sessões abertas,
    # já que o cookie guarda (id, versão) e é conferido a cada requisição.
    sessao_versao: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DataHoraUTC, default=agora)
    deleted_at: Mapped[datetime | None] = mapped_column(DataHoraUTC, default=None)

    __table_args__ = (
        # E-mail único só entre usuários ATIVOS: permite recriar um usuário desativado
        Index("uq_usuario_email_ativo", "email", unique=True, sqlite_where=deleted_at.is_(None)),
    )

    def is_ativo(self) -> bool:
        return self.deleted_at is None

    def is_admin(self) -> bool:
        return self.role == Role.ADMIN
