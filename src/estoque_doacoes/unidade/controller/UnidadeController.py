"""Unidades de medida: todos os perfis listam (seletor do cadastro); só ADMIN altera."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from estoque_doacoes.auth.dependencies import Autenticado, SomenteAdmin, UsuarioAtual
from estoque_doacoes.shared.database.db import get_session
from estoque_doacoes.unidade.dto.UnidadeDTO import UnidadeIn, UnidadeOut
from estoque_doacoes.unidade.service.UnidadeService import UnidadeService

router = APIRouter(prefix="/api/unidades", tags=["unidades de medida"], dependencies=[Autenticado])


def get_service(session: Annotated[Session, Depends(get_session)]) -> UnidadeService:
    return UnidadeService(session)


Service = Annotated[UnidadeService, Depends(get_service)]


@router.get("", response_model=list[UnidadeOut])
def listar(service: Service):
    return service.listar()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UnidadeOut,
    dependencies=[SomenteAdmin],
)
def criar(dados: UnidadeIn, service: Service, autor: UsuarioAtual):
    return service.criar(dados, autor)


@router.put("/{unidade_id}", response_model=UnidadeOut, dependencies=[SomenteAdmin])
def atualizar(unidade_id: int, dados: UnidadeIn, service: Service):
    """Unidade em uso: só o nome é editável (409 para sigla, grandeza ou fator)."""
    return service.atualizar(unidade_id, dados)


@router.delete("/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[SomenteAdmin])
def excluir(unidade_id: int, service: Service) -> None:
    """Exclusão lógica. 409 se algum produto usa a unidade."""
    service.excluir(unidade_id)
