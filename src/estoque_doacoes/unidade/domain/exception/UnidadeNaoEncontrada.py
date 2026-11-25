from estoque_doacoes.shared.exception.Erros import NaoEncontrado


class UnidadeNaoEncontrada(NaoEncontrado):
    def __init__(self, unidade_id: int):
        super().__init__(f"Unidade de medida {unidade_id} não existe")
