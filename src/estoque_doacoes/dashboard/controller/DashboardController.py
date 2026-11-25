"""Dashboard: somente ADMIN (D7). COMUM recebe 403 mesmo acessando a URL direto (RNF05)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from estoque_doacoes.auth.dependencies import SomenteAdmin
from estoque_doacoes.dashboard.dto.DashboardDTO import DashboardResumo, PendenciaSaldo, PontoSerie
from estoque_doacoes.dashboard.service.DashboardService import DashboardService
from estoque_doacoes.shared.database.db import get_session

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[SomenteAdmin])


def get_service(session: Annotated[Session, Depends(get_session)]) -> DashboardService:
    return DashboardService(session)


Service = Annotated[DashboardService, Depends(get_service)]
Inicio = Annotated[date | None, Query(description="AAAA-MM-DD; padrão: fim − 29 dias")]
Fim = Annotated[date | None, Query(description="AAAA-MM-DD; padrão: hoje")]
CategoriaId = Annotated[int | None, Query()]


@router.get("/resumo", response_model=DashboardResumo)
def resumo(
    service: Service, inicio: Inicio = None, fim: Fim = None, categoria_id: CategoriaId = None
):
    """Saldo (embalagens), entradas e saídas no período (sem AJUSTE), pendências e totais
    convertidos em kg, L e un."""
    return service.resumo(inicio, fim, categoria_id)


@router.get("/series", response_model=list[PontoSerie])
def series(
    service: Service, inicio: Inicio = None, fim: Fim = None, categoria_id: CategoriaId = None
):
    """Entradas e saídas (embalagens) por dia do período."""
    return service.series(inicio, fim, categoria_id)


@router.get("/pendencias", response_model=list[PendenciaSaldo])
def pendencias(service: Service, categoria_id: CategoriaId = None):
    """Produtos ativos com saldo negativo."""
    return service.pendencias(categoria_id)
