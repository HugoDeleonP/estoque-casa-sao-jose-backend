from estoque_doacoes.shared.exception.Erros import Conflito


class ProdutoComSaldo(Conflito):
    def __init__(self, produto_id: int, saldo: int):
        super().__init__(
            f"Produto {produto_id} tem saldo {saldo}; zere o estoque com um AJUSTE antes de excluir"
        )
