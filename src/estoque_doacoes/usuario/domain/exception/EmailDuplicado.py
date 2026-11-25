from estoque_doacoes.shared.exception.Erros import Conflito


class EmailDuplicado(Conflito):
    def __init__(self, email: str):
        super().__init__(f"Já existe usuário ativo com o e-mail {email}")
