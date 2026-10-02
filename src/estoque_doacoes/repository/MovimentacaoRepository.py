from collections.abc import Iterable

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from estoque_doacoes.model.entity.Movimentacao import Movimentacao
from estoque_doacoes.model.enum.TipoMovimentacao import TipoMovimentacao
# Quantidade com sinal: SAIDA subtrai; ENTRADA e AJUSTE já carregam o sinal correto.
# Definida UMA vez — catálogo, dashboard e alerta usam a mesma regra.
_quantidade_assinada = case(
    (Movimentacao.tipo == TipoMovimentacao.SAIDA, -Movimentacao.quantidade),
    else_=Movimentacao.quantidade,
)


class MovimentacaoRepository:
    def __init__(self, session: Session):
        self.session = session

    def adicionar(self, mov: Movimentacao) -> None:
        self.session.add(mov)

    def saldo(self, produto_id: int) -> int:
        stmt = select(func.coalesce(func.sum(_quantidade_assinada), 0)).where(
            Movimentacao.produto_id == produto_id
        )
        return self.session.scalar(stmt)

    def saldos(self, produto_ids: Iterable[int]) -> dict[int, int]:
        """Saldo de vários produtos em UMA query (GROUP BY), em vez de uma por produto."""
        ids = list(produto_ids)
        if not ids:
            return {}
        stmt = (
            select(Movimentacao.produto_id, func.sum(_quantidade_assinada))
            .where(Movimentacao.produto_id.in_(ids))
            .group_by(Movimentacao.produto_id)
        )
        encontrados = dict(self.session.execute(stmt).tuples().all())
        return {pid: encontrados.get(pid, 0) for pid in ids}
