"""Importa todas as entidades: registra as tabelas no metadata e os mappers (relationship
por nome) — necessário em scripts que não sobem a API inteira."""

import estoque_doacoes.categoria.domain.entity.Categoria  # noqa: F401
import estoque_doacoes.movimentacao.domain.entity.Movimentacao  # noqa: F401
import estoque_doacoes.produto.domain.entity.Produto  # noqa: F401
import estoque_doacoes.unidade.domain.entity.UnidadeMedida  # noqa: F401
import estoque_doacoes.usuario.domain.entity.Usuario  # noqa: F401
