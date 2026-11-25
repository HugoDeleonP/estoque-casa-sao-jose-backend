from estoque_doacoes.shared.exception.Erros import Conflito


class UltimoAdmin(Conflito):
    def __init__(self):
        super().__init__("O sistema precisa manter ao menos um ADMIN ativo")
