from estoque_doacoes.shared.exception.Erros import Conflito


class SiglaDuplicada(Conflito):
    def __init__(self, sigla: str):
        super().__init__(f"Já existe unidade ativa com a sigla {sigla}")
