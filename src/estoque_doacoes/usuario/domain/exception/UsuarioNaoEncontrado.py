from estoque_doacoes.shared.exception.Erros import NaoEncontrado


class UsuarioNaoEncontrado(NaoEncontrado):
    def __init__(self, usuario_id: int):
        super().__init__(f"Usuário {usuario_id} não existe")
