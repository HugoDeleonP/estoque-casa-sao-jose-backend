from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from estoque_doacoes.movimentacao.domain.entity.Movimentacao import Movimentacao
from estoque_doacoes.movimentacao.domain.enum.TipoMovimentacao import TipoMovimentacao


class MovimentacaoRepository:
    """Consultas de Movimentação. NUNCA faz commit — a transação é do service."""

    def __init__(self, session: Session):
        self.session = session

    def por_id(self, movimentacao_id: int) -> Movimentacao | None:
        stmt = (
            select(Movimentacao)
            .where(Movimentacao.id == movimentacao_id)
            .options(joinedload(Movimentacao.produto))
        )
        return self.session.scalar(stmt)

    def listar(
        self,
        *,
        produto_id: int | None = None,
        tipo: TipoMovimentacao | None = None,
        limite: int = 100,
    ) -> list[Movimentacao]:
        """Histórico mais recente primeiro. Inclui movimentações de produtos excluídos."""
        stmt = (
            select(Movimentacao)
            .options(joinedload(Movimentacao.produto))
            .order_by(Movimentacao.created_at.desc(), Movimentacao.id.desc())
            .limit(limite)
        )
        if produto_id is not None:
            stmt = stmt.where(Movimentacao.produto_id == produto_id)
        if tipo is not None:
            stmt = stmt.where(Movimentacao.tipo == tipo)
        return list(self.session.scalars(stmt))

    def adicionar(self, mov: Movimentacao) -> None:
        self.session.add(mov)

    def saldos(self, produto_ids: Iterable[int]) -> dict[int, int]:
        """Saldo de vários produtos em UMA query (GROUP BY). Para listagens, no lugar de
        chamar Produto.saldo() item a item (N+1)."""
        ids = list(produto_ids)
        if not ids:
            return {}
        stmt = (
            select(Movimentacao.produto_id, func.sum(Movimentacao.quantidade))
            .where(Movimentacao.produto_id.in_(ids))
            .group_by(Movimentacao.produto_id)
        )
        encontrados = dict(self.session.execute(stmt).tuples().all())
        return {pid: encontrados.get(pid, 0) for pid in ids}
