"""Contratos da API (DTOs). Separados dos models de propósito:
- `deleted_at` e outros detalhes internos nunca vazam no JSON;
- `saldo` aparece na saída sem existir como coluna."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from estoque_doacoes.categoria.dto.CategoriaDTO import CategoriaOut
from estoque_doacoes.shared.validation.tipos import CodigoBarras, VazioComoNulo

Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Marca = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
Unidade = Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)]


class ProdutoIn(BaseModel):
    """Usado no POST e no PUT (o PUT substitui todos os campos editáveis)."""

    codigo_barras: Annotated[CodigoBarras | None, VazioComoNulo] = None
    nome: Nome
    marca: Annotated[Marca | None, VazioComoNulo] = None
    unidade: Annotated[Unidade | None, VazioComoNulo] = None
    categoria_id: int = Field(gt=0)


class ProdutoOut(BaseModel):
    id: int
    codigo_barras: str | None
    nome: str
    marca: str | None
    unidade: str | None
    categoria: CategoriaOut
    saldo: int
    created_at: datetime
    updated_at: datetime
