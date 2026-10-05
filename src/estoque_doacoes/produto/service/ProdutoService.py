from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from estoque_doacoes.categoria.domain.entity.Categoria import Categoria
from estoque_doacoes.categoria.domain.exception.CategoriaNaoEncontrada import CategoriaNaoEncontrada
from estoque_doacoes.categoria.dto.CategoriaDTO import CategoriaOut
from estoque_doacoes.categoria.repository.CategoriaRepository import CategoriaRepository
from estoque_doacoes.movimentacao.repository.MovimentacaoRepository import MovimentacaoRepository
from estoque_doacoes.produto.domain.entity.Produto import Produto
from estoque_doacoes.produto.domain.exception.CodigoDuplicado import CodigoDuplicado
from estoque_doacoes.produto.domain.exception.ProdutoComSaldo import ProdutoComSaldo
from estoque_doacoes.produto.domain.exception.ProdutoNaoEncontrado import ProdutoNaoEncontrado
from estoque_doacoes.produto.dto.ProdutoDTO import ProdutoIn, ProdutoOut
from estoque_doacoes.produto.repository.ProdutoRepository import ProdutoRepository


class ProdutoService:
    """Regras de negócio de Produto e DONO DA TRANSAÇÃO (equivale ao @Transactional)."""

    def __init__(self, session: Session):
        self.session = session
        self.produtos = ProdutoRepository(session)
        self.categorias = CategoriaRepository(session)
        self.movimentacoes = MovimentacaoRepository(session)  # só leitura: saldo em lote

    def listar(self, categoria_id: int | None = None) -> list[ProdutoOut]:
        produtos = self.produtos.listar(categoria_id=categoria_id)
        saldos = self.movimentacoes.saldos(p.id for p in produtos)  # 1 query p/ todos
        return [self._para_saida(p, saldos[p.id]) for p in produtos]

    def buscar(self, produto_id: int) -> ProdutoOut:
        produto = self._ativo(produto_id)
        return self._para_saida(produto, produto.saldo())

    def buscar_por_codigo(self, codigo: str) -> ProdutoOut:
        produto = self.produtos.por_codigo(codigo)
        if produto is None:
            raise ProdutoNaoEncontrado.por_codigo(codigo)
        return self._para_saida(produto, produto.saldo())

    def cadastrar(self, dados: ProdutoIn) -> ProdutoOut:
        produto = Produto(categoria=self._categoria(dados.categoria_id))
        self._preencher(produto, dados)
        self.produtos.adicionar(produto)
        self._commit(dados.codigo_barras)
        return self._para_saida(produto, saldo=0)

    def atualizar(self, produto_id: int, dados: ProdutoIn) -> ProdutoOut:
        produto = self._ativo(produto_id)
        produto.categoria = self._categoria(dados.categoria_id)
        self._preencher(produto, dados)
        self._commit(dados.codigo_barras)
        return self._para_saida(produto, produto.saldo())

    def excluir(self, produto_id: int) -> None:
        """Soft delete, só com saldo zero. O histórico de movimentações é preservado."""
        produto = self._ativo(produto_id)
        if not produto.pode_excluir():
            raise ProdutoComSaldo(produto_id, produto.saldo())
        self.produtos.excluir(produto)
        self.session.commit()

    # ---------- Auxiliares ----------

    def _ativo(self, produto_id: int) -> Produto:
        produto = self.produtos.por_id(produto_id)
        if produto is None:
            raise ProdutoNaoEncontrado.por_id(produto_id)
        return produto

    def _categoria(self, categoria_id: int) -> Categoria:
        # Categoria excluída (soft delete) também não serve para produto ativo
        categoria = self.categorias.por_id(categoria_id)
        if categoria is None:
            raise CategoriaNaoEncontrada(categoria_id)
        return categoria

    def _preencher(self, produto: Produto, dados: ProdutoIn) -> None:
        # Checagem amigável (mensagem clara no caso comum)...
        if dados.codigo_barras is not None:
            outro = self.produtos.por_codigo(dados.codigo_barras)
            if outro is not None and outro is not produto:
                raise CodigoDuplicado(dados.codigo_barras)
        produto.codigo_barras = dados.codigo_barras
        produto.nome = dados.nome
        produto.marca = dados.marca
        produto.unidade = dados.unidade

    def _commit(self, codigo: str | None) -> None:
        try:
            self.session.commit()
        except IntegrityError:
            # ...e a garantia real fica no índice único parcial: duas bancadas bipando o
            # mesmo produto novo ao mesmo tempo passam ambas pela checagem acima.
            self.session.rollback()
            raise CodigoDuplicado(codigo) from None

    @staticmethod
    def _para_saida(produto: Produto, saldo: int) -> ProdutoOut:
        return ProdutoOut(
            id=produto.id,
            codigo_barras=produto.codigo_barras,
            nome=produto.nome,
            marca=produto.marca,
            unidade=produto.unidade,
            categoria=CategoriaOut.model_validate(produto.categoria),
            saldo=saldo,
            created_at=produto.created_at,
            updated_at=produto.updated_at,
        )
