"""Camada HTTP de Categoria: recebe, valida (schema), delega ao service e devolve."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from estoque_doacoes.categoria.dto.CategoriaDTO import CategoriaIn, CategoriaOut
from estoque_doacoes.categoria.service.CategoriaService import CategoriaService
from estoque_doacoes.shared.database.db import get_session

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


def get_service(session: Annotated[Session, Depends(get_session)]) -> CategoriaService:
    """Injeção de dependência: um service (e uma Session) por requisição."""
    return CategoriaService(session)


Service = Annotated[CategoriaService, Depends(get_service)]


@router.get("", response_model=list[CategoriaOut])
def listar(service: Service):
    return service.listar()


@router.get("/{categoria_id}", response_model=CategoriaOut)
def buscar(categoria_id: int, service: Service):
    return service.buscar(categoria_id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CategoriaOut)
def criar(dados: CategoriaIn, service: Service):
    return service.criar(dados.nome)


@router.put("/{categoria_id}", response_model=CategoriaOut)
def atualizar(categoria_id: int, dados: CategoriaIn, service: Service):
    return service.atualizar(categoria_id, dados.nome)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(categoria_id: int, service: Service) -> None:
    """409 se ainda houver produtos (mesmo excluídos) vinculados à categoria."""
    service.excluir(categoria_id)
