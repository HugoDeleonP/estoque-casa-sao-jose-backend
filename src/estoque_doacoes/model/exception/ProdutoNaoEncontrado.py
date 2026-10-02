class ProdutoNaoEncontrado(NaoEncontrado):
    def __init__(self, codigo: str):
        super().__init__(f"Produto com código {codigo} não cadastrado")
        self.codigo = codigo