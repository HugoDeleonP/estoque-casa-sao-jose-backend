"""Erros de DOMÍNIO. O service não conhece HTTP; o main.py traduz para status codes.
Assim o mesmo service serve para API, script de importação ou teste."""


class ErroDominio(Exception):
    pass


class NaoEncontrado(ErroDominio):
    pass


class Conflito(ErroDominio):
    pass


class DadosInvalidos(ErroDominio):
    """Regra que depende do banco (ex.: unidade inexistente) — vira 422, como a validação."""


class NaoAutenticado(ErroDominio):
    def __init__(self, mensagem: str = "Faça login para continuar"):
        super().__init__(mensagem)


class SemPermissao(ErroDominio):
    def __init__(self, mensagem: str = "Seu perfil não tem acesso a este recurso"):
        super().__init__(mensagem)
