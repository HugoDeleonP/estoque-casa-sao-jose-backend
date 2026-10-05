from estoque_doacoes.shared.exception.Erros import Conflito


class CodigoDuplicado(Conflito):
    def __init__(self, codigo: str):
        super().__init__(f"Já existe produto ativo com código {codigo}")
