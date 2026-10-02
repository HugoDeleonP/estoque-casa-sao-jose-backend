from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from estoque_doacoes.model import TipoMovimentacao
from estoque_doacoes.dto.ProdutoDTO import CodigoBarras


class MovimentacaoCreate(BaseModel):
    """Entrada vinda do bip: identifica o produto pelo CÓDIGO, não pelo id interno."""

    codigo_barras: CodigoBarras
    tipo: TipoMovimentacao
    quantidade: int = Field(default=1)
    observacao: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _quantidade_coerente(self):
        # Mesma regra do CHECK do banco, mas aqui gera erro 422 legível para o frontend
        if self.tipo is TipoMovimentacao.AJUSTE and self.quantidade == 0:
            raise ValueError("AJUSTE não pode ter quantidade zero")
        if self.tipo is not TipoMovimentacao.AJUSTE and self.quantidade <= 0:
            raise ValueError(f"{self.tipo} exige quantidade positiva")
        return self


class MovimentacaoOut(BaseModel):
    id: int
    codigo_barras: str
    tipo: TipoMovimentacao
    quantidade: int
    criado_em: datetime
    saldo_atual: int
    alerta_saldo_negativo: bool  # alerta, não bloqueio (decisão do MVP)
