from estoque_doacoes.shared.exception.Erros import Conflito


class UnidadeEmUso(Conflito):
    """F1.4: mudar grandeza/fator de unidade em uso alteraria retroativamente os totais."""
