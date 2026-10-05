from enum import StrEnum


class TipoMovimentacao(StrEnum):
    ENTRADA = "ENTRADA"  # quantidade > 0
    SAIDA = "SAIDA"  # quantidade < 0 (o sinal é gravado)
    AJUSTE = "AJUSTE"  # quantidade ≠ 0 (+/-), corrige contagem física; exige observação
