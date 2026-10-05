from estoque_doacoes.shared.exception.Erros import NaoEncontrado


class ProdutoNaoEncontrado(NaoEncontrado):
    @classmethod
    def por_id(cls, produto_id: int) -> "ProdutoNaoEncontrado":
        return cls(f"Produto {produto_id} não existe")

    @classmethod
    def por_codigo(cls, codigo: str) -> "ProdutoNaoEncontrado":
        return cls(f"Produto com código {codigo} não cadastrado")
