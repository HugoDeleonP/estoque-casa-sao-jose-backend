"""Contratos da API (DTOs). Separados dos models de propósito:
- `deleted_at` e outros detalhes internos nunca vazam no JSON;
- `saldo` aparece na saída sem existir como coluna."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from estoque_doacoes.categoria.dto.CategoriaDTO import CategoriaOut
from estoque_doacoes.shared.validation.tipos import CodigoBarras, VazioComoNulo
from estoque_doacoes.unidade.dto.UnidadeDTO import UnidadeResumo

Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Marca = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]


class ProdutoIn(BaseModel):
    """Usado no POST e no PUT (o PUT substitui todos os campos editáveis)."""

    codigo_barras: Annotated[CodigoBarras | None, VazioComoNulo] = None
    nome: Nome
    marca: Annotated[Marca | None, VazioComoNulo] = None
    conteudo_valor: float = Field(gt=0, le=100_000, description="Conteúdo de uma embalagem")
    unidade_medida_id: int = Field(gt=0)
    categoria_id: int = Field(gt=0)


class ProdutoOut(BaseModel):
    id: int
    codigo_barras: str | None
    nome: str
    marca: str | None
    conteudo_valor: float
    unidade_medida: UnidadeResumo
    categoria: CategoriaOut
    saldo: int
    created_at: datetime
    updated_at: datetime


class ProdutoExcluidoOut(ProdutoOut):
    """Produto em soft delete: a bancada oferece reativação em vez de novo cadastro (RN09)."""

    deleted_at: datetime
