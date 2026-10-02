from __future__ import annotations

from enum import StrEnum

class TipoMovimentacao(StrEnum):
    ENTRADA = "ENTRADA"  # quantidade > 0, soma no saldo
    SAIDA = "SAIDA"  # quantidade > 0, subtrai do saldo
    AJUSTE = "AJUSTE"  # quantidade com sinal (+/-), corrige contagem física

