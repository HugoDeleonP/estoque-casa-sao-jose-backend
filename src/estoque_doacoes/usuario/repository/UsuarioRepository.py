from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from estoque_doacoes.shared.database.db import agora
from estoque_doacoes.usuario.domain.entity.Usuario import Usuario
from estoque_doacoes.usuario.domain.enum.Role import Role


class UsuarioRepository:
    """Consultas de Usuário. NUNCA faz commit — a transação é do service."""

    def __init__(self, session: Session):
        self.session = session

    def _ativos(self) -> Select[tuple[Usuario]]:
        return select(Usuario).where(Usuario.deleted_at.is_(None))

    def por_id(self, usuario_id: int) -> Usuario | None:
        return self.session.scalar(self._ativos().where(Usuario.id == usuario_id))

    def por_email(self, email: str) -> Usuario | None:
        return self.session.scalar(self._ativos().where(Usuario.email == email.strip().lower()))

    def listar(self) -> list[Usuario]:
        return list(self.session.scalars(self._ativos().order_by(Usuario.nome)))

    def total_admins_ativos(self) -> int:
        stmt = (
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.deleted_at.is_(None), Usuario.role == Role.ADMIN)
        )
        return self.session.scalar(stmt) or 0

    def adicionar(self, usuario: Usuario) -> None:
        self.session.add(usuario)

    def desativar(self, usuario: Usuario) -> None:
        usuario.deleted_at = agora()
        usuario.sessao_versao += 1
