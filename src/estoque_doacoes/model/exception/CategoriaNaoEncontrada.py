class CategoriaNaoEncontrada(NaoEncontrado):
    def __init__(self, categoria_id: int):
        super().__init__(f"Categoria {categoria_id} não existe")