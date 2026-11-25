from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"  # voluntário chefe: catálogo, unidades, usuários e dashboard
    COMUM = "COMUM"  # bancada: cadastra produto e registra entrada/saída/ajuste
