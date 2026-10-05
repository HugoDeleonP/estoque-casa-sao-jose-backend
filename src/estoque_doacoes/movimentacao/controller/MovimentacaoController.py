"""Camada HTTP de Movimentação: recebe, valida (schema), delega ao service e devolve.

Sem PUT/DELETE: imutável após criada. Correção = nova movimentação do tipo AJUSTE."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from estoque_doacoes.movimentacao.domain.enum.TipoMovimentacao import TipoMovimentacao
from estoque_doacoes.movimentacao.dto.MovimentacaoDTO import (
    MovimentacaoCreate,
    MovimentacaoOut,
    MovimentacaoRegistrada,
)
from estoque_doacoes.movimentacao.service.MovimentacaoService import MovimentacaoService
from estoque_doacoes.shared.database.db import get_session

router = APIRouter(prefix="/api/movimentacoes", tags=["movimentações"])


def get_service(session: Annotated[Session, Depends(get_session)]) -> MovimentacaoService:
    """Injeção de dependência: um service (e uma Session) por requisição."""
    return MovimentacaoService(session)


Service = Annotated[MovimentacaoService, Depends(get_service)]


@router.get("", response_model=list[MovimentacaoOut])
def listar(
    service: Service,
    produto_id: Annotated[int | None, Query()] = None,
    tipo: Annotated[TipoMovimentacao | None, Query()] = None,
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """Histórico, mais recente primeiro."""
    return service.listar(produto_id, tipo, limite)


@router.get("/{movimentacao_id}", response_model=MovimentacaoOut)
def buscar(movimentacao_id: int, service: Service):
    return service.buscar(movimentacao_id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MovimentacaoRegistrada)
def registrar(dados: MovimentacaoCreate, service: Service):
    return service.registrar(dados)
