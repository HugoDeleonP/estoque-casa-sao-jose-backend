"""Camada HTTP: recebe, valida (schema), delega ao service e devolve. Sem regra de negócio."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, StringConstraints
from sqlalchemy.orm import Session

from estoque_doacoes.db import get_session
from estoque_doacoes.dto.MovimentacaoDTO import MovimentacaoCreate, MovimentacaoOut
from estoque_doacoes.dto.ProdutoDTO import CodigoBarras, ProdutoCreate, ProdutoOut
from estoque_doacoes.service.CatalogoService import CatalogoService

router = APIRouter(prefix="/api", tags=["catálogo"])


def get_catalogo(session: Annotated[Session, Depends(get_session)]) -> CatalogoService:
    """Injeção de dependência: um service (e uma Session) por requisição."""
    return CatalogoService(session)


Catalogo = Annotated[CatalogoService, Depends(get_catalogo)]


class CategoriaIn(BaseModel):
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]


class CategoriaOut(BaseModel):
    id: int
    nome: str


@router.post("/categorias", status_code=status.HTTP_201_CREATED, response_model=CategoriaOut)
def criar_categoria(dados: CategoriaIn, catalogo: Catalogo):
    c = catalogo.criar_categoria(dados.nome)
    return CategoriaOut(id=c.id, nome=c.nome)


@router.get("/produtos", response_model=list[ProdutoOut])
def listar_produtos(catalogo: Catalogo, categoria_id: Annotated[int | None, Query()] = None):
    return catalogo.listar(categoria_id)


@router.get("/produtos/{codigo_barras}", response_model=ProdutoOut)
def buscar_por_codigo(codigo_barras: CodigoBarras, catalogo: Catalogo):
    """Chamado a cada bip. 404 → o frontend abre o formulário de cadastro."""
    return catalogo.buscar_por_codigo(codigo_barras)


@router.post("/produtos", status_code=status.HTTP_201_CREATED, response_model=ProdutoOut)
def cadastrar_produto(dados: ProdutoCreate, catalogo: Catalogo):
    return catalogo.cadastrar(dados)


@router.post("/movimentacoes", status_code=status.HTTP_201_CREATED, response_model=MovimentacaoOut)
def registrar_movimentacao(dados: MovimentacaoCreate, catalogo: Catalogo):
    return catalogo.registrar_movimentacao(dados)
