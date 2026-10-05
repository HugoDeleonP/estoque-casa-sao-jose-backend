from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

from estoque_doacoes.movimentacao.domain.enum.TipoMovimentacao import TipoMovimentacao
from estoque_doacoes.shared.validation.tipos import VazioComoNulo

Observacao = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class MovimentacaoCreate(BaseModel):
    """O produto é identificado pelo id: nem todo produto tem código de barras.
    No bip, o frontend resolve o código → id em GET /api/produtos/codigo/{codigo}."""

    produto_id: int = Field(gt=0)
    tipo: TipoMovimentacao
    quantidade: int = Field(description="ENTRADA > 0, SAIDA < 0, AJUSTE ≠ 0")
    observacao: Annotated[Observacao | None, VazioComoNulo] = None

    @model_validator(mode="after")
    def _quantidade_coerente(self):
        # Mesma regra do CHECK do banco, mas aqui gera erro 422 legível para o frontend
        match self.tipo:
            case TipoMovimentacao.ENTRADA if self.quantidade <= 0:
                raise ValueError("ENTRADA exige quantidade positiva")
            case TipoMovimentacao.SAIDA if self.quantidade >= 0:
                raise ValueError("SAIDA exige quantidade negativa")
            case TipoMovimentacao.AJUSTE if self.quantidade == 0:
                raise ValueError("AJUSTE não pode ter quantidade zero")
            case TipoMovimentacao.AJUSTE if self.observacao is None:
                raise ValueError("AJUSTE exige observação (motivo da correção)")
        return self


class MovimentacaoOut(BaseModel):
    """Uma linha do histórico (GET)."""

    id: int
    produto_id: int
    produto_nome: str
    tipo: TipoMovimentacao
    quantidade: int
    observacao: str | None
    created_at: datetime


class MovimentacaoRegistrada(MovimentacaoOut):
    """Resposta do POST: além da movimentação, o saldo do produto logo após ela."""

    saldo_atual: int
    alerta_saldo_negativo: bool  # alerta, não bloqueio (decisão do MVP)
