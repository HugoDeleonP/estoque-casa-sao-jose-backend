from estoque_doacoes.shared.exception.Erros import NaoEncontrado


class MovimentacaoNaoEncontrada(NaoEncontrado):
    def __init__(self, movimentacao_id: int):
        super().__init__(f"Movimentação {movimentacao_id} não existe")
