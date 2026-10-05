"""modelo de dominio v2

Revision ID: 72a1a00e22d9
Revises: 842468ad06ea
Create Date: 2026-10-04 22:00:00

Alinha o schema ao diagrama de classes (seção 6):
- categoria: + deleted_at (soft delete); nome único só entre categorias ativas
- produto: codigo_barras opcional; embalagem → unidade (opcional); + marca;
  criado_em → created_at; + updated_at
- movimentacao: criado_em → created_at; SAIDA passa a gravar quantidade NEGATIVA
  (saldo = SUM(quantidade)); AJUSTE exige observação

SQLite não altera CHECK/NOT NULL/UNIQUE com ALTER TABLE: cada tabela é recriada à mão
(cria nova → copia → apaga antiga → renomeia), o procedimento oficial do SQLite. O env.py
desliga as FKs durante a migração e roda PRAGMA foreign_key_check no fim.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "72a1a00e22d9"
down_revision: str | Sequence[str] | None = "842468ad06ea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OBS_AJUSTE_LEGADO = "Ajuste registrado antes da observação ser obrigatória"


def _tipo() -> sa.Enum:
    return sa.Enum(
        "ENTRADA",
        "SAIDA",
        "AJUSTE",
        name="tipomovimentacao",
        native_enum=False,
        create_constraint=True,
        length=10,
    )


def _trocar(tabela: str, nova: str, colunas_destino: str, select_origem: str) -> None:
    op.execute(f"INSERT INTO {nova} ({colunas_destino}) {select_origem}")
    op.drop_table(tabela)  # leva junto os índices da tabela antiga
    op.rename_table(nova, tabela)


def upgrade() -> None:
    # ---------- categoria ----------
    op.create_table(
        "_categoria_nova",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categoria")),
    )
    _trocar("categoria", "_categoria_nova", "id, nome", "SELECT id, nome FROM categoria")
    op.create_index(
        "uq_categoria_nome_ativa",
        "categoria",
        ["nome"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    # ---------- produto ----------
    op.create_table(
        "_produto_novo",
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
    _trocar(
        "produto",
        "_produto_novo",
        "id, codigo_barras, nome, unidade, categoria_id, created_at, updated_at, deleted_at",
        # embalagem ("1 kg", "lata 350 g") vira unidade; updated_at começa igual ao created_at
        "SELECT id, codigo_barras, nome, embalagem, categoria_id, criado_em, criado_em, deleted_at"
        " FROM produto",
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
        sa.Column("tipo", _tipo(), nullable=False),
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
        "_movimentacao_nova",
        "id, produto_id, tipo, quantidade, observacao, created_at",
        "SELECT id, produto_id, tipo,"
        " CASE WHEN tipo = 'SAIDA' THEN -quantidade ELSE quantidade END,"
        " CASE WHEN tipo = 'AJUSTE' AND (observacao IS NULL OR trim(observacao) = '')"
        f"      THEN '{OBS_AJUSTE_LEGADO}' ELSE observacao END,"
        " criado_em FROM movimentacao",
    )
    op.create_index(op.f("ix_movimentacao_created_at"), "movimentacao", ["created_at"])
    op.create_index(op.f("ix_movimentacao_produto_id"), "movimentacao", ["produto_id"])


def downgrade() -> None:
    conn = op.get_bind()
    sem_codigo = conn.exec_driver_sql(
        "SELECT count(*) FROM produto WHERE codigo_barras IS NULL"
    ).scalar_one()
    if sem_codigo:
        raise RuntimeError(
            f"Downgrade impossível: {sem_codigo} produto(s) sem código de barras "
            "(o schema anterior exige o código)."
        )

    # ---------- movimentacao ----------
    op.create_table(
        "_movimentacao_antiga",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("tipo", _tipo(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("observacao", sa.String(length=200), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(tipo = 'AJUSTE' AND quantidade <> 0) OR (tipo <> 'AJUSTE' AND quantidade > 0)",
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
        "id, produto_id, tipo, quantidade, observacao, criado_em",
        "SELECT id, produto_id, tipo,"
        " CASE WHEN tipo = 'SAIDA' THEN -quantidade ELSE quantidade END,"
        " observacao, created_at FROM movimentacao",
    )
    op.create_index(op.f("ix_movimentacao_criado_em"), "movimentacao", ["criado_em"])
    op.create_index(op.f("ix_movimentacao_produto_id"), "movimentacao", ["produto_id"])

    # ---------- produto ----------
    op.create_table(
        "_produto_antigo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo_barras", sa.String(length=14), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("embalagem", sa.String(length=30), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["categoria_id"], ["categoria.id"], name=op.f("fk_produto_categoria_id_categoria")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_produto")),
    )
    _trocar(
        "produto",
        "_produto_antigo",
        "id, codigo_barras, nome, embalagem, categoria_id, criado_em, deleted_at",
        "SELECT id, codigo_barras, nome, coalesce(unidade, ''), categoria_id, created_at,"
        " deleted_at FROM produto",
    )
    op.create_index(
        "uq_produto_codigo_ativo",
        "produto",
        ["codigo_barras"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    # ---------- categoria ----------
    # Categorias em soft delete voltam como ativas; falha se houver nome repetido.
    op.create_table(
        "_categoria_antiga",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categoria")),
        sa.UniqueConstraint("nome", name=op.f("uq_categoria_nome")),
    )
    _trocar("categoria", "_categoria_antiga", "id, nome", "SELECT id, nome FROM categoria")
