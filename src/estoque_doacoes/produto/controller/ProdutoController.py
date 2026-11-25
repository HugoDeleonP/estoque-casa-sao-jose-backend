"""Camada HTTP de Produto: recebe, valida (schema), delega ao service e devolve.

Identidade na URL é o id: nem todo produto tem código de barras. O bip usa /codigo/{codigo}.
Permissões (D9/F3.5): todos consultam e cadastram; só ADMIN edita (inclusive o código de
barras), exclui e reativa."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from estoque_doacoes.auth.dependencies import Autenticado, SomenteAdmin, UsuarioAtual
from estoque_doacoes.produto.dto.ProdutoDTO import ProdutoExcluidoOut, ProdutoIn, ProdutoOut
from estoque_doacoes.produto.service.ProdutoService import ProdutoService
from estoque_doacoes.shared.database.db import get_session
from estoque_doacoes.shared.validation.tipos import CodigoBarras

router = APIRouter(prefix="/api/produtos", tags=["produtos"], dependencies=[Autenticado])


def get_service(session: Annotated[Session, Depends(get_session)]) -> ProdutoService:
    """Injeção de dependência: um service (e uma Session) por requisição."""
    return ProdutoService(session)


Service = Annotated[ProdutoService, Depends(get_service)]


@router.get("", response_model=list[ProdutoOut])
def listar(service: Service, categoria_id: Annotated[int | None, Query()] = None):
    return service.listar(categoria_id)


@router.get("/codigo/{codigo_barras}", response_model=ProdutoOut)
def buscar_por_codigo(codigo_barras: CodigoBarras, service: Service):
    """Chamado a cada bip. 404 → o frontend abre o formulário de cadastro."""
    return service.buscar_por_codigo(codigo_barras)


@router.get("/excluidos/codigo/{codigo_barras}", response_model=ProdutoExcluidoOut)
def buscar_excluido_por_codigo(codigo_barras: CodigoBarras, service: Service):
    """RN09: no bip de um código sem produto ativo, a bancada oferece reativação."""
    return service.buscar_excluido_por_codigo(codigo_barras)


@router.get("/{produto_id}", response_model=ProdutoOut)
def buscar(produto_id: int, service: Service):
    return service.buscar(produto_id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProdutoOut)
def cadastrar(dados: ProdutoIn, service: Service, autor: UsuarioAtual):
    return service.cadastrar(dados, autor)


@router.put("/{produto_id}", response_model=ProdutoOut, dependencies=[SomenteAdmin])
def atualizar(produto_id: int, dados: ProdutoIn, service: Service):
    return service.atualizar(produto_id, dados)


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[SomenteAdmin])
def excluir(produto_id: int, service: Service) -> None:
    """Soft delete. 409 se o saldo não for zero; o histórico de movimentações é mantido."""
    service.excluir(produto_id)


@router.post("/{produto_id}/reativar", response_model=ProdutoOut, dependencies=[SomenteAdmin])
def reativar(produto_id: int, service: Service):
    """Desfaz o soft delete (RF08). 409 se o código já está em outro produto ativo."""
    return service.reativar(produto_id)
