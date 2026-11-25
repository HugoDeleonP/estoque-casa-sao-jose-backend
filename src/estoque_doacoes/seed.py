"""Dados iniciais idempotentes: pode rodar quantas vezes quiser (deploy, testes, local).

- Unidades de medida: as do seed da migração, caso tenham sido apagadas.
- Categorias: só se o banco não tiver NENHUMA (a lista definitiva é da Casa, pergunta P3)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import estoque_doacoes.entidades  # noqa: F401
from estoque_doacoes.categoria.domain.entity.Categoria import Categoria
from estoque_doacoes.unidade.domain.entity.UnidadeMedida import UnidadeMedida
from estoque_doacoes.unidade.domain.enum.Grandeza import Grandeza

UNIDADES = [
    ("kg", "quilograma", Grandeza.MASSA, 1),
    ("g", "grama", Grandeza.MASSA, 0.001),
    ("L", "litro", Grandeza.VOLUME, 1),
    ("mL", "mililitro", Grandeza.VOLUME, 0.001),
    ("un", "unidade", Grandeza.CONTAGEM, 1),
    ("dz", "dúzia", Grandeza.CONTAGEM, 12),
]

CATEGORIAS = ["Alimentos", "Bebidas", "Higiene", "Limpeza", "Vestuário", "Outros"]


def semear_unidades(session: Session) -> None:
    existentes = set(
        session.scalars(select(UnidadeMedida.sigla).where(UnidadeMedida.deleted_at.is_(None)))
    )
    for sigla, nome, grandeza, fator in UNIDADES:
        if sigla not in existentes:
            session.add(UnidadeMedida(sigla=sigla, nome=nome, grandeza=grandeza, fator_base=fator))


def semear_categorias(session: Session) -> None:
    if session.scalar(select(func.count()).select_from(Categoria)):
        return
    session.add_all(Categoria(nome=n) for n in CATEGORIAS)


def semear(session: Session) -> None:
    semear_unidades(session)
    semear_categorias(session)
    session.commit()
