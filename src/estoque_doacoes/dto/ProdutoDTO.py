"""Contratos da API (DTOs). Separados dos models de propósito:
- `deleted_at`, `categoria_id` interno etc. nunca vazam no JSON;
- `saldo` aparece na saída sem existir como coluna."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# EAN-8, UPC-A (12), EAN-13 e ITF-14: só dígitos, 8 a 14
CodigoBarras = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{8,14}$")]


class ProdutoCreate(BaseModel):
    codigo_barras: CodigoBarras
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
    embalagem: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
    categoria_id: int = Field(gt=0)


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # permite montar a partir do model ORM

    id: int
    codigo_barras: str
    nome: str
    embalagem: str
    categoria: str
    saldo: int
