from sqlalchemy import Select, exists, select
from sqlalchemy.orm import Session

from estoque_doacoes.categoria.domain.entity.Categoria import Categoria
from estoque_doacoes.produto.domain.entity.Produto import Produto
from estoque_doacoes.shared.database.db import agora


class CategoriaRepository:
    """Consultas de Categoria. NUNCA faz commit — a transação é do service."""

    def __init__(self, session: Session):
        self.session = session

    def _ativas(self) -> Select[tuple[Categoria]]:
        return select(Categoria).where(Categoria.deleted_at.is_(None))

    def por_id(self, categoria_id: int) -> Categoria | None:
        return self.session.scalar(self._ativas().where(Categoria.id == categoria_id))

    def listar(self) -> list[Categoria]:
        return list(self.session.scalars(self._ativas().order_by(Categoria.nome)))

    def possui_produtos_ativos(self, categoria_id: int) -> bool:
        stmt = select(
            exists().where(Produto.categoria_id == categoria_id, Produto.deleted_at.is_(None))
        )
        return bool(self.session.scalar(stmt))

    def adicionar(self, categoria: Categoria) -> None:
        self.session.add(categoria)

    def excluir(self, categoria: Categoria) -> None:
        """Soft delete: produtos já excluídos continuam apontando para ela."""
        categoria.deleted_at = agora()
