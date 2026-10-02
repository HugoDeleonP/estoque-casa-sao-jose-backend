from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from estoque_doacoes.model import Categoria, Movimentacao, Produto
from estoque_doacoes.repository import MovimentacaoRepository, ProdutoRepository
from estoque_doacoes.dto.MovimentacaoDTO import MovimentacaoCreate, MovimentacaoOut
from estoque_doacoes.dto.ProdutoDTO import ProdutoCreate, ProdutoOut
from estoque_doacoes.model.exception import (
    CategoriaNaoEncontrada,
    CodigoDuplicado,
    ProdutoNaoEncontrado,
)


class CatalogoService:
    """Regras de negócio do Módulo de Catálogo e DONO DA TRANSAÇÃO (equivale ao @Transactional)."""

    def __init__(self, session: Session):
        self.session = session
        self.produtos = ProdutoRepository(session)
        self.movimentacoes = MovimentacaoRepository(session)

    # ---------- Categoria: sem repository (seria só repasse para a Session) ----------

    def criar_categoria(self, nome: str) -> Categoria:
        categoria = Categoria(nome=nome.strip())
        self.session.add(categoria)
        self.session.commit()
        return categoria

    def listar_categorias(self) -> list[Categoria]:
        return list(self.session.scalars(select(Categoria).order_by(Categoria.nome)))

    # ---------- Produto ----------

    def buscar_por_codigo(self, codigo: str) -> ProdutoOut:
        produto = self.produtos.por_codigo(codigo)
        if produto is None:
            raise ProdutoNaoEncontrado(codigo)
        return self._para_saida(produto, self.movimentacoes.saldo(produto.id))

    def listar(self, categoria_id: int | None = None) -> list[ProdutoOut]:
        produtos = self.produtos.listar(categoria_id=categoria_id)
        saldos = self.movimentacoes.saldos(p.id for p in produtos)  # 1 query p/ todos
        return [self._para_saida(p, saldos[p.id]) for p in produtos]

    def cadastrar(self, dados: ProdutoCreate) -> ProdutoOut:
        if self.session.get(Categoria, dados.categoria_id) is None:
            raise CategoriaNaoEncontrada(dados.categoria_id)
        # Checagem amigável (mensagem clara no caso comum)...
        if self.produtos.por_codigo(dados.codigo_barras) is not None:
            raise CodigoDuplicado(dados.codigo_barras)

        produto = Produto(**dados.model_dump())
        self.produtos.adicionar(produto)
        try:
            self.session.commit()
        except IntegrityError:
            # ...e a garantia real fica no índice único: duas bancadas bipando o mesmo
            # produto novo ao mesmo tempo passam ambas pela checagem acima.
            self.session.rollback()
            raise CodigoDuplicado(dados.codigo_barras) from None
        self.session.refresh(produto, ["categoria"])
        return self._para_saida(produto, saldo=0)

    # ---------- Movimentação ----------

    def registrar_movimentacao(self, dados: MovimentacaoCreate) -> MovimentacaoOut:
        produto = self.produtos.por_codigo(dados.codigo_barras)
        if produto is None:
            raise ProdutoNaoEncontrado(dados.codigo_barras)

        mov = Movimentacao(
            produto=produto,
            tipo=dados.tipo,
            quantidade=dados.quantidade,
            observacao=dados.observacao,
        )
        self.movimentacoes.adicionar(mov)
        self.session.flush()  # envia o INSERT (dentro da transação) para o SUM enxergá-lo
        saldo = self.movimentacoes.saldo(produto.id)
        self.session.commit()

        return MovimentacaoOut(
            id=mov.id,
            codigo_barras=produto.codigo_barras,
            tipo=mov.tipo,
            quantidade=mov.quantidade,
            criado_em=mov.criado_em,
            saldo_atual=saldo,
            alerta_saldo_negativo=saldo < 0,  # registra mesmo assim; o frontend avisa
        )

    # ---------- Mapeamento model → schema ----------

    @staticmethod
    def _para_saida(produto: Produto, saldo: int) -> ProdutoOut:
        return ProdutoOut(
            id=produto.id,
            codigo_barras=produto.codigo_barras,
            nome=produto.nome,
            embalagem=produto.embalagem,
            categoria=produto.categoria.nome,
            saldo=saldo,
        )
