"""Indicadores do dashboard (RF04/RF05), calculados sempre a partir das movimentações.

Período: datas no fuso da Casa (America/Sao_Paulo), convertidas para o intervalo UTC
[início 00:00, fim+1 00:00) — o banco grava em UTC."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from estoque_doacoes.categoria.domain.entity.Categoria import Categoria
from estoque_doacoes.dashboard.dto.DashboardDTO import (
    DashboardResumo,
    PendenciaSaldo,
    PontoSerie,
    TotaisGrandeza,
)
from estoque_doacoes.movimentacao.domain.entity.Movimentacao import Movimentacao
from estoque_doacoes.movimentacao.domain.enum.TipoMovimentacao import TipoMovimentacao
from estoque_doacoes.produto.domain.entity.Produto import Produto
from estoque_doacoes.shared.exception.Erros import DadosInvalidos
from estoque_doacoes.unidade.domain.entity.UnidadeMedida import UnidadeMedida
from estoque_doacoes.unidade.domain.enum.Grandeza import Grandeza

FUSO = ZoneInfo("America/Sao_Paulo")
DIAS_PADRAO = 30
DIAS_MAXIMO = 366
FLUXO = (TipoMovimentacao.ENTRADA, TipoMovimentacao.SAIDA)


def hoje_local() -> date:
    return datetime.now(FUSO).date()


def _totais(linhas) -> TotaisGrandeza:
    """[(grandeza, total na unidade base)] → TotaisGrandeza."""
    t = TotaisGrandeza()
    campo = {
        Grandeza.MASSA: "massa_kg",
        Grandeza.VOLUME: "volume_l",
        Grandeza.CONTAGEM: "contagem_un",
    }
    for grandeza, total in linhas:
        setattr(t, campo[Grandeza(grandeza)], round(float(total or 0), 3))
    return t


class DashboardService:
    def __init__(self, session: Session):
        self.session = session

    # ---------- Período ----------

    @staticmethod
    def periodo(inicio: date | None, fim: date | None) -> tuple[date, date]:
        fim = fim or hoje_local()
        inicio = inicio or fim - timedelta(days=DIAS_PADRAO - 1)
        if inicio > fim:
            raise DadosInvalidos("A data inicial deve ser anterior ou igual à final")
        if (fim - inicio).days + 1 > DIAS_MAXIMO:
            raise DadosInvalidos(f"O período pode ter no máximo {DIAS_MAXIMO} dias")
        return inicio, fim

    @staticmethod
    def _utc(inicio: date, fim: date) -> tuple[datetime, datetime]:
        de = datetime.combine(inicio, time.min, FUSO).astimezone(UTC)
        ate = datetime.combine(fim + timedelta(days=1), time.min, FUSO).astimezone(UTC)
        return de, ate

    # ---------- Consultas ----------

    def _saldos(self, categoria_id: int | None) -> Select:
        """Uma linha por produto ATIVO: saldo (embalagens) e conversão para a base."""
        stmt = (
            select(
                Produto.id,
                Produto.nome,
                Produto.marca,
                Categoria.nome.label("categoria"),
                UnidadeMedida.grandeza,
                (Produto.conteudo_valor * UnidadeMedida.fator_base).label("por_embalagem"),
                func.coalesce(func.sum(Movimentacao.quantidade), 0).label("saldo"),
            )
            .join(Categoria, Produto.categoria_id == Categoria.id)
            .join(UnidadeMedida, Produto.unidade_medida_id == UnidadeMedida.id)
            .outerjoin(Movimentacao, Movimentacao.produto_id == Produto.id)
            .where(Produto.deleted_at.is_(None))
            .group_by(Produto.id)
        )
        if categoria_id is not None:
            stmt = stmt.where(Produto.categoria_id == categoria_id)
        return stmt

    def _fluxo(self, inicio: date, fim: date, categoria_id: int | None) -> Select:
        """ENTRADA/SAIDA no período, inclusive de produtos excluídos depois (doação houve)."""
        de, ate = self._utc(inicio, fim)
        stmt = (
            select(Movimentacao.tipo, Movimentacao.quantidade, Movimentacao.created_at)
            .join(Produto, Movimentacao.produto_id == Produto.id)
            .where(
                Movimentacao.tipo.in_(FLUXO),
                Movimentacao.created_at >= de,
                Movimentacao.created_at < ate,
            )
        )
        if categoria_id is not None:
            stmt = stmt.where(Produto.categoria_id == categoria_id)
        return stmt

    def resumo(
        self, inicio: date | None, fim: date | None, categoria_id: int | None
    ) -> DashboardResumo:
        inicio, fim = self.periodo(inicio, fim)
        produtos = self.session.execute(self._saldos(categoria_id)).all()

        estoque: dict[str, float] = {}
        for p in produtos:
            estoque[p.grandeza] = estoque.get(p.grandeza, 0) + p.saldo * p.por_embalagem

        de, ate = self._utc(inicio, fim)
        fluxo = (
            select(
                Movimentacao.tipo,
                UnidadeMedida.grandeza,
                func.sum(Movimentacao.quantidade),
                func.sum(
                    Movimentacao.quantidade * Produto.conteudo_valor * UnidadeMedida.fator_base
                ),
            )
            .join(Produto, Movimentacao.produto_id == Produto.id)
            .join(UnidadeMedida, Produto.unidade_medida_id == UnidadeMedida.id)
            .where(
                Movimentacao.tipo.in_(FLUXO),
                Movimentacao.created_at >= de,
                Movimentacao.created_at < ate,
            )
            .group_by(Movimentacao.tipo, UnidadeMedida.grandeza)
        )
        if categoria_id is not None:
            fluxo = fluxo.where(Produto.categoria_id == categoria_id)
        linhas = self.session.execute(fluxo).all()

        def soma(tipo: TipoMovimentacao) -> int:
            return abs(sum(int(q or 0) for t, _, q, _ in linhas if t == tipo))

        def por_grandeza(tipo: TipoMovimentacao) -> TotaisGrandeza:
            return _totais((g, abs(b or 0)) for t, g, _, b in linhas if t == tipo)

        return DashboardResumo(
            inicio=inicio,
            fim=fim,
            saldo_total=sum(p.saldo for p in produtos),
            total_produtos=len(produtos),
            produtos_saldo_negativo=sum(1 for p in produtos if p.saldo < 0),
            total_entradas=soma(TipoMovimentacao.ENTRADA),
            total_saidas=soma(TipoMovimentacao.SAIDA),
            estoque_grandeza=_totais(estoque.items()),
            entradas_grandeza=por_grandeza(TipoMovimentacao.ENTRADA),
            saidas_grandeza=por_grandeza(TipoMovimentacao.SAIDA),
        )

    def series(
        self, inicio: date | None, fim: date | None, categoria_id: int | None
    ) -> list[PontoSerie]:
        """Um ponto por dia do período (dias sem movimento = 0). Agrupado em Python: o dia
        depende do fuso local e o volume da Casa é pequeno."""
        inicio, fim = self.periodo(inicio, fim)
        dias = {inicio + timedelta(days=i): [0, 0] for i in range((fim - inicio).days + 1)}
        for tipo, quantidade, criado in self.session.execute(
            self._fluxo(inicio, fim, categoria_id)
        ):
            dia = criado.astimezone(FUSO).date()
            if dia in dias:
                dias[dia][0 if tipo == TipoMovimentacao.ENTRADA else 1] += abs(quantidade)
        return [PontoSerie(data=d, entradas=e, saidas=s) for d, (e, s) in dias.items()]

    def pendencias(self, categoria_id: int | None) -> list[PendenciaSaldo]:
        """Produtos ativos com saldo negativo (modelagem, seção 8.3), mais negativo primeiro."""
        stmt = self._saldos(categoria_id).having(func.sum(Movimentacao.quantidade) < 0)
        linhas = self.session.execute(stmt).all()
        return [
            PendenciaSaldo(
                produto_id=p.id, nome=p.nome, marca=p.marca, categoria=p.categoria, saldo=p.saldo
            )
            for p in sorted(linhas, key=lambda p: (p.saldo, p.nome))
        ]
