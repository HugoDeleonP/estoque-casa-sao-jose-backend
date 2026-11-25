from enum import StrEnum


class Grandeza(StrEnum):
    """Cada grandeza tem uma unidade base; o dashboard nunca soma grandezas diferentes."""

    MASSA = "MASSA"  # base: kg
    VOLUME = "VOLUME"  # base: L
    CONTAGEM = "CONTAGEM"  # base: un

    @property
    def unidade_base(self) -> str:
        return {"MASSA": "kg", "VOLUME": "L", "CONTAGEM": "un"}[self.value]
