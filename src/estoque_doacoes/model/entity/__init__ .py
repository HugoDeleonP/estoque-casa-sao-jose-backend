"""Importar todos os modelos aqui garante que Base.metadata conheça todas as tabelas
(necessário para create_all e para o autogenerate do Alembic)."""

from estoque_doacoes.model.entity.Categoria import Categoria
from estoque_doacoes.model.entity.Movimentacao import Movimentacao
from estoque_doacoes.model.entity.Produto import Produto

__all__ = ["Categoria", "Movimentacao", "Produto"]
