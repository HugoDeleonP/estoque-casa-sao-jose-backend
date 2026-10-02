"""Erros de DOMÍNIO. O service não conhece HTTP; o main.py traduz para status codes.
Assim o mesmo service serve para API, script de importação ou teste."""


class ErroDominio(Exception):
    pass

class NaoEncontrado(ErroDominio):
    pass

class Conflito(ErroDominio):
    pass