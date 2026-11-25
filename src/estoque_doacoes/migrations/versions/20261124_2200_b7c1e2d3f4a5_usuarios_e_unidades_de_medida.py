"""usuarios e unidades de medida

Revision ID: b7c1e2d3f4a5
Revises: 72a1a00e22d9
Create Date: 2026-11-24 22:00:00

Entrega v2 (plano F1 e F3):
- usuario: login com senha (bcrypt), perfil ADMIN/COMUM, exclusão lógica
- unidade_medida: unidades do conteúdo da embalagem, com grandeza e fator de conversão,
  já populada com as mais usadas (kg, g, L, mL, un, dz)
- produto: unidade (texto livre) → conteudo_valor (> 0) + unidade_medida_id; + created_by
- movimentacao: + created_by

O banco de produção é novo (D3). Se houver produtos antigos, recebem 1 un como conteúdo
para não violar o NOT NULL — revisar pela tela de edição.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c1e2d3f4a5"
down_revision: str | Sequence[str] | None = "72a1a00e22d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Congelado aqui de propósito: a migração não pode mudar se o seed da aplicação mudar.
UNIDADES = [
    # sigla, nome, grandeza, fator_base
    ("kg", "quilograma", "MASSA", 1),
    ("g", "grama", "MASSA", 0.001),
    ("L", "litro", "VOLUME", 1),
    ("mL", "mililitro", "VOLUME", 0.001),
    ("un", "unidade", "CONTAGEM", 1),
    ("dz", "dúzia", "CONTAGEM", 12),
]


def _enum(nome: str, *valores: str) -> sa.Enum:
    return sa.Enum(*valores, name=nome, native_enum=False, create_constraint=True, length=10)


def _tipo_mov() -> sa.Enum:
    return _enum("tipomovimentacao", "ENTRADA", "SAIDA", "AJUSTE")


def _trocar(tabela: str, nova: str, colunas_destino: str, select_origem: str) -> None:
    op.execute(f"INSERT INTO {nova} ({colunas_destino}) {select_origem}")
    op.drop_table(tabela)  # leva junto os índices da tabela antiga
    op.rename_table(nova, tabela)


def upgrade() -> None:
    # ---------- usuario ----------
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("senha_hash", sa.String(length=100), nullable=False),
        sa.Column("role", _enum("role", "ADMIN", "COMUM"), nullable=False),
        sa.Column("sessao_versao", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
    )
    op.create_index(
        "uq_usuario_email_ativo",
        "usuario",
        ["email"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    # ---------- unidade_medida ----------
    op.create_table(
        "unidade_medida",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sigla", sa.String(length=10), nullable=False),
        sa.Column("nome", sa.String(length=40), nullable=False),
        sa.Column("grandeza", _enum("grandeza", "MASSA", "VOLUME", "CONTAGEM"), nullable=False),
        sa.Column("fator_base", sa.Numeric(14, 6), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("fator_base > 0", name=op.f("ck_unidade_medida_fator_base_positivo")),
        sa.ForeignKeyConstraint(
            ["created_by"], ["usuario.id"], name=op.f("fk_unidade_medida_created_by_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_unidade_medida")),
    )
    op.create_index(
        "uq_unidade_medida_sigla_ativa",
        "unidade_medida",
        ["sigla"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    # Mesmo formato de data que o SQLAlchemy grava (UTC, microssegundos)
    op.execute(
        "INSERT INTO unidade_medida (sigla, nome, grandeza, fator_base, created_at) VALUES "
        + ", ".join(
            f"('{s}', '{n}', '{g}', {f}, strftime('%Y-%m-%d %H:%M:%S', 'now') || '.000000')"
            for s, n, g, f in UNIDADES
        )
    )

    # ---------- produto ----------
    op.create_table(
        "_produto_novo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo_barras", sa.String(length=14), nullable=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("marca", sa.String(length=80), nullable=True),
        sa.Column("conteudo_valor", sa.Numeric(12, 3), nullable=False),
        sa.Column("unidade_medida_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("conteudo_valor > 0", name=op.f("ck_produto_conteudo_positivo")),
        sa.ForeignKeyConstraint(
            ["categoria_id"], ["categoria.id"], name=op.f("fk_produto_categoria_id_categoria")
        ),
        sa.ForeignKeyConstraint(
            ["unidade_medida_id"],
            ["unidade_medida.id"],
            name=op.f("fk_produto_unidade_medida_id_unidade_medida"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["usuario.id"], name=op.f("fk_produto_created_by_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_produto")),
    )
    _trocar(
        "produto",
        "_produto_novo",
        "id, codigo_barras, nome, marca, conteudo_valor, unidade_medida_id, categoria_id,"
        " created_at, updated_at, deleted_at",
        "SELECT id, codigo_barras, nome, marca, 1,"
        " (SELECT id FROM unidade_medida WHERE sigla = 'un'),"
        " categoria_id, created_at, updated_at, deleted_at FROM produto",
    )
    op.create_index(
        "uq_produto_codigo_ativo",
        "produto",
        ["codigo_barras"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    # ---------- movimentacao ----------
    op.create_table(
        "_movimentacao_nova",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("tipo", _tipo_mov(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("observacao", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "(tipo = 'ENTRADA' AND quantidade > 0)"
            " OR (tipo = 'SAIDA' AND quantidade < 0)"
            " OR (tipo = 'AJUSTE' AND quantidade <> 0"
            " AND observacao IS NOT NULL AND trim(observacao) <> '')",
            name=op.f("ck_movimentacao_quantidade_por_tipo"),
        ),
        sa.ForeignKeyConstraint(
            ["produto_id"], ["produto.id"], name=op.f("fk_movimentacao_produto_id_produto")
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["usuario.id"], name=op.f("fk_movimentacao_created_by_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movimentacao")),
    )
    _trocar(
        "movimentacao",
        "_movimentacao_nova",
        "id, produto_id, tipo, quantidade, observacao, created_at",
        "SELECT id, produto_id, tipo, quantidade, observacao, created_at FROM movimentacao",
    )
    op.create_index(op.f("ix_movimentacao_created_at"), "movimentacao", ["created_at"])
    op.create_index(op.f("ix_movimentacao_produto_id"), "movimentacao", ["produto_id"])


def downgrade() -> None:
    # ---------- movimentacao ----------
    op.create_table(
        "_movimentacao_antiga",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("tipo", _tipo_mov(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("observacao", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(tipo = 'ENTRADA' AND quantidade > 0)"
            " OR (tipo = 'SAIDA' AND quantidade < 0)"
            " OR (tipo = 'AJUSTE' AND quantidade <> 0"
            " AND observacao IS NOT NULL AND trim(observacao) <> '')",
            name=op.f("ck_movimentacao_quantidade_por_tipo"),
        ),
        sa.ForeignKeyConstraint(
            ["produto_id"], ["produto.id"], name=op.f("fk_movimentacao_produto_id_produto")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movimentacao")),
    )
    _trocar(
        "movimentacao",
        "_movimentacao_antiga",
        "id, produto_id, tipo, quantidade, observacao, created_at",
        "SELECT id, produto_id, tipo, quantidade, observacao, created_at FROM movimentacao",
    )
    op.create_index(op.f("ix_movimentacao_created_at"), "movimentacao", ["created_at"])
    op.create_index(op.f("ix_movimentacao_produto_id"), "movimentacao", ["produto_id"])

    # ---------- produto ----------
    op.create_table(
        "_produto_antigo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo_barras", sa.String(length=14), nullable=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("marca", sa.String(length=80), nullable=True),
        sa.Column("unidade", sa.String(length=30), nullable=True),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["categoria_id"], ["categoria.id"], name=op.f("fk_produto_categoria_id_categoria")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_produto")),
    )
    # "5 kg" volta como texto descritivo
    _trocar(
        "produto",
        "_produto_antigo",
        "id, codigo_barras, nome, marca, unidade, categoria_id, created_at, updated_at, deleted_at",
        "SELECT p.id, p.codigo_barras, p.nome, p.marca,"
        " rtrim(rtrim(printf('%.3f', p.conteudo_valor), '0'), '.') || ' ' || u.sigla,"
        " p.categoria_id, p.created_at, p.updated_at, p.deleted_at"
        " FROM produto p JOIN unidade_medida u ON u.id = p.unidade_medida_id",
    )
    op.create_index(
        "uq_produto_codigo_ativo",
        "produto",
        ["codigo_barras"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.drop_table("unidade_medida")
    op.drop_table("usuario")
