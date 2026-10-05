from estoque_doacoes.shared.exception.Erros import Conflito


class CategoriaDuplicada(Conflito):
    def __init__(self, nome: str):
        super().__init__(f"Já existe categoria com nome {nome}")
