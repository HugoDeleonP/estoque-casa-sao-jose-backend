from collections.abc import Iterable

from sqlalchemy import Select, exists, func, select
from sqlalchemy.orm import Session

from estoque_doacoes.produto.domain.entity.Produto import Produto
from estoque_doacoes.shared.database.db import agora
from estoque_doacoes.unidade.domain.entity.UnidadeMedida import UnidadeMedida


class UnidadeRepository:
    """Consultas de Unidade de Medida. NUNCA faz commit — a transação é do service."""

    def __init__(self, session: Session):
        self.session = session

    def _ativas(self) -> Select[tuple[UnidadeMedida]]:
        return select(UnidadeMedida).where(UnidadeMedida.deleted_at.is_(None))

    def por_id(self, unidade_id: int) -> UnidadeMedida | None:
        return self.session.scalar(self._ativas().where(UnidadeMedida.id == unidade_id))

    def por_sigla(self, sigla: str) -> UnidadeMedida | None:
        """Sem diferenciar maiúsculas: "ml" e "mL" seriam a mesma unidade para o voluntário."""
        stmt = self._ativas().where(func.lower(UnidadeMedida.sigla) == sigla.lower())
        return self.session.scalar(stmt)

    def listar(self) -> list[UnidadeMedida]:
        stmt = self._ativas().order_by(UnidadeMedida.grandeza, UnidadeMedida.fator_base.desc())
        return list(self.session.scalars(stmt))

    def em_uso(self, unidade_id: int) -> bool:
        """Qualquer produto, inclusive excluído (pode ser reativado)."""
        return bool(
            self.session.scalar(select(exists().where(Produto.unidade_medida_id == unidade_id)))
        )

    def ids_em_uso(self, ids: Iterable[int]) -> set[int]:
        stmt = select(Produto.unidade_medida_id).where(Produto.unidade_medida_id.in_(list(ids)))
        return set(self.session.scalars(stmt.distinct()))

    def adicionar(self, unidade: UnidadeMedida) -> None:
        self.session.add(unidade)

    def excluir(self, unidade: UnidadeMedida) -> None:
        unidade.deleted_at = agora()
