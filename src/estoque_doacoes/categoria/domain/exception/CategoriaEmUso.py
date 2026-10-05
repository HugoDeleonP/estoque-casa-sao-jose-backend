from estoque_doacoes.shared.exception.Erros import Conflito


class CategoriaEmUso(Conflito):
    def __init__(self, categoria_id: int):
        super().__init__(f"Categoria {categoria_id} possui produtos ativos vinculados")
