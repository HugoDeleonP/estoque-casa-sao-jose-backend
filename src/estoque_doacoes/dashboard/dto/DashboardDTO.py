from datetime import date

from pydantic import BaseModel


class TotaisGrandeza(BaseModel):
    """Cada grandeza na sua unidade base. Nunca somadas entre si (F2.2)."""

    massa_kg: float = 0
    volume_l: float = 0
    contagem_un: float = 0


class DashboardResumo(BaseModel):
    inicio: date
    fim: date
    # Estoque atual (não depende do período), em embalagens
    saldo_total: int
    total_produtos: int
    produtos_saldo_negativo: int
    # Fluxo no período, em embalagens. AJUSTE não entra (RF04); saídas em valor absoluto
    total_entradas: int
    total_saidas: int
    # Mesmos números convertidos pelo conteúdo de cada embalagem
    estoque_grandeza: TotaisGrandeza
    entradas_grandeza: TotaisGrandeza
    saidas_grandeza: TotaisGrandeza


class PontoSerie(BaseModel):
    data: date  # dia no fuso America/Sao_Paulo
    entradas: int
    saidas: int  # valor absoluto


class PendenciaSaldo(BaseModel):
    produto_id: int
    nome: str
    marca: str | None
    categoria: str
    saldo: int
