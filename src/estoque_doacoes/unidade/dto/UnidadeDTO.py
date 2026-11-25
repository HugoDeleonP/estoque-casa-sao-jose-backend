from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from estoque_doacoes.unidade.domain.enum.Grandeza import Grandeza

Sigla = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10)]
NomeUnidade = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=40)]


class UnidadeIn(BaseModel):
    """POST e PUT. Em unidade usada por algum produto, só o `nome` pode mudar (F1.4)."""

    sigla: Sigla
    nome: NomeUnidade
    grandeza: Grandeza
    fator_base: float = Field(gt=0, le=1_000_000, description="Converte para kg, L ou un")


class UnidadeResumo(BaseModel):
    """Embutida no produto."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sigla: str
    nome: str
    grandeza: Grandeza
    fator_base: float


class UnidadeOut(UnidadeResumo):
    em_uso: bool
