from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class CategoriaIn(BaseModel):
    """Usado no POST e no PUT (a categoria só tem o nome editável)."""

    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
