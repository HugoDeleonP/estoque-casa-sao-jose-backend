from estoque_doacoes.shared.exception.Erros import Conflito


class OperacaoSobreSiMesmo(Conflito):
    """ADMIN não desativa a si mesmo nem rebaixa o próprio perfil (evita trancar-se fora)."""
