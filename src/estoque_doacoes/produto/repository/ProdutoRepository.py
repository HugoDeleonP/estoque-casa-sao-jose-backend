from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from estoque_doacoes.produto.domain.entity.Produto import Produto
from estoque_doacoes.shared.database.db import agora


class ProdutoRepository:
    """Consultas de Produto. NUNCA faz commit — a transação é do service."""

    def __init__(self, session: Session):
        self.session = session

    def _ativos(self) -> Select[tuple[Produto]]:
        # Único lugar do módulo que conhece a regra do soft delete
        return (
            select(Produto)
            .where(Produto.deleted_at.is_(None))
            .options(joinedload(Produto.categoria))  # evita N+1 ao serializar a categoria
        )

    def por_id(self, produto_id: int) -> Produto | None:
        return self.session.scalar(self._ativos().where(Produto.id == produto_id))

    def por_codigo(self, codigo: str) -> Produto | None:
        """Operação mais frequente do sistema: todo bip passa por aqui (usa o índice parcial)."""
        return self.session.scalar(self._ativos().where(Produto.codigo_barras == codigo))

    def listar(self, *, categoria_id: int | None = None) -> list[Produto]:
        stmt = self._ativos().order_by(Produto.nome)
        if categoria_id is not None:
            stmt = stmt.where(Produto.categoria_id == categoria_id)
        return list(self.session.scalars(stmt))

    def adicionar(self, produto: Produto) -> None:
        self.session.add(produto)

    def excluir(self, produto: Produto) -> None:
        """Soft delete: preserva o histórico de movimentações do produto."""
        produto.deleted_at = agora()
